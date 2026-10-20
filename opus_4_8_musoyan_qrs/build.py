"""One-pass build: apply nested bookmarks AND video links, then verify, in a single save.

Pipeline per volume:  source PDF
                       -> set nested outline from fixed_bookmarks_N.json
                       -> open bookmark panel on launch (UseOutlines)
                       -> draw video links from video_links.json (chosen style)
                       -> save once -> out_pdf/musoyan_N_final.pdf
                       -> verify outline round-trips and links are present

Reuses the logic from apply_bookmarks.py and place_video_links.py so there is a
single source of truth. A full save (not incremental) is correct here because
setting the outline rewrites the document anyway; the output stays ~the same size
as the source (vector badges + base font add only KB).

Usage:
  python opus_4_8_musoyan_qrs/build.py                # card style, both volumes
  python opus_4_8_musoyan_qrs/build.py --style chip
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

from apply_bookmarks import build_toc, level_counts
from place_video_links import (
    badge_size, anchor_xy, draw_footnote, load_entries, verify_links, DRAWERS,
    LABEL_TTF, LABEL_FONTNAME,
)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOG_DIR = REPO_ROOT / "logs"
OUT_DIR = SCRIPT_DIR / "out_pdf"

# (volume key, source pdf, bookmarks json, final output)
VOLUMES = [
    ("1", "musoyan_1.pdf", "fixed_bookmarks_1.json", "musoyan_1_final.pdf"),
    ("2", "musoyan_2.pdf", "fixed_bookmarks_2.json", "musoyan_2_final.pdf"),
]

# ---- reader-info page, inserted right before the first chapter of each volume ----
# DRAFT wording - edit these constants to finalize the text.
REG_TTF = "C:/Windows/Fonts/segoeui.ttf"  # Segoe UI Regular, has Armenian glyphs
REG_FONTNAME = "SegoeUIRegular"
INFO_TITLE = "Ընթերցողին"
INFO_ITEMS = [
    "Փաստաթուղթը որոնելի է։ Սեղմեք Ctrl+F (Mac-ում՝ Cmd+F)՝ ցանկացած "
    "բառ կամ արտահայտություն գտնելու համար։",
    "Գրքի կառուցվածքով կարող եք տեղաշարժվել ձախ վահանակի էջանիշերի "
    "(bookmarks) միջոցով։",
    "Գլուխների առաջին էջերի կարմիր քարտերը բացում են համապատասխան "
    "տեսադասախոսությունները YouTube-ում։",
]
INFO_LINK_LABEL = "Լրացուցիչ նյութեր՝ "
INFO_URL = "https://mathteam.notion.site/"
INFO_URL_TEXT = "mathteam.notion.site"


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("build")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_DIR / "build.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


log = setup_logging()


def first_chapter_page(toc: list) -> int:
    """1-based page where the first numbered chapter opens ('1. ...' / '10. ...')."""
    for level, title, page in toc:
        if level == 1 and re.match(r"\d+\.", title):
            return page
    raise ValueError("no numbered chapter entry found in the TOC")


def wrap_lines(text: str, font: fitz.Font, size: float, maxw: float) -> list:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if not cur or font.text_length(trial, fontsize=size) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def insert_info_page(doc: fitz.Document, insert_at: int) -> None:
    """Insert the reader-info page so it becomes 1-based page `insert_at`."""
    ref = doc[insert_at - 1].rect  # match the size of the page being displaced
    page = doc.new_page(pno=insert_at - 1, width=ref.width, height=ref.height)
    reg, sb = fitz.Font(fontfile=REG_TTF), fitz.Font(fontfile=LABEL_TTF)
    W = page.rect.width
    margin, indent = 60.0, 16.0
    body, lh = 10.5, 17.0

    title_size = 15.0
    tw = sb.text_length(INFO_TITLE, fontsize=title_size)
    page.insert_text(((W - tw) / 2, 150), INFO_TITLE, fontname=LABEL_FONTNAME,
                     fontfile=LABEL_TTF, fontsize=title_size, color=(0.1, 0.1, 0.1))
    page.draw_line((W / 2 - 30, 162), (W / 2 + 30, 162), color=(0.6, 0.6, 0.6), width=0.7)

    y = 200.0
    for item in INFO_ITEMS:
        page.insert_text((margin, y), "•", fontname=REG_FONTNAME, fontfile=REG_TTF,
                         fontsize=body, color=(0.15, 0.15, 0.15))
        for line in wrap_lines(item, reg, body, W - 2 * margin - indent):
            page.insert_text((margin + indent, y), line, fontname=REG_FONTNAME,
                             fontfile=REG_TTF, fontsize=body, color=(0.15, 0.15, 0.15))
            y += lh
        y += 10

    page.insert_text((margin, y), "•", fontname=REG_FONTNAME, fontfile=REG_TTF,
                     fontsize=body, color=(0.15, 0.15, 0.15))
    page.insert_text((margin + indent, y), INFO_LINK_LABEL, fontname=REG_FONTNAME,
                     fontfile=REG_TTF, fontsize=body, color=(0.15, 0.15, 0.15))
    lx = margin + indent + reg.text_length(INFO_LINK_LABEL, fontsize=body)
    uw = sb.text_length(INFO_URL_TEXT, fontsize=body)
    page.insert_text((lx, y), INFO_URL_TEXT, fontname=LABEL_FONTNAME, fontfile=LABEL_TTF,
                     fontsize=body, color=(0.00, 0.32, 0.66))
    page.insert_link({"kind": fitz.LINK_URI,
                      "from": fitz.Rect(lx, y - body, lx + uw, y + 3), "uri": INFO_URL})


def draw_links(doc: fitz.Document, vol: str, style: str, shift_at: int) -> list:
    """Draw all configured links; pages >= shift_at move +1 for the inserted page."""
    entries = [dict(e) for e in load_entries(vol)]
    for e in entries:
        if e["page"] >= shift_at:
            e["page"] += 1
    footnote_slot = defaultdict(int)
    taken = defaultdict(list)  # badges already on the page, per page number
    for e in entries:
        page = doc[e["page"] - 1]
        this_style = e.get("style", style)
        if this_style == "footnote":
            draw_footnote(page, e["label"], e["url"], footnote_slot[page.number])
            footnote_slot[page.number] += 1
        else:
            w, h = badge_size(this_style, e["label"], e["url"])
            x, y = anchor_xy(page, e["position"], w, h, taken=taken[page.number])
            taken[page.number].append(fitz.Rect(x, y, x + w, y + h))
            DRAWERS[this_style](page, x, y, e["label"], e["url"])
    return entries


def build_one(vol: str, pdf_name: str, json_name: str, out_name: str, style: str):
    pdf_path = SCRIPT_DIR / pdf_name
    json_path = SCRIPT_DIR / json_name
    for required in (pdf_path, json_path):
        if not required.exists():
            raise FileNotFoundError(f"Missing input: {required}")

    doc = fitz.open(pdf_path)
    try:
        toc = build_toc(json.loads(json_path.read_text(encoding="utf-8")), doc.page_count)
        # The reader-info page goes right before the first chapter, so every
        # bookmark and link from there on shifts one page down.
        insert_at = first_chapter_page(toc)
        insert_info_page(doc, insert_at)
        toc = [[lv, t, p + 1 if p >= insert_at else p] for lv, t, p in toc]
        chapter_idx = next(i for i, (lv, t, _p) in enumerate(toc)
                           if lv == 1 and re.match(r"\d+\.", t))
        toc.insert(chapter_idx, [1, INFO_TITLE, insert_at])
        if doc.set_toc(toc) != len(toc):
            raise RuntimeError("set_toc wrote an unexpected number of entries")
        doc.set_pagemode("UseOutlines")
        entries = draw_links(doc, vol, style, insert_at)
        # card labels embed an Armenian face; keep only the glyphs actually used
        doc.subset_fonts()
        OUT_DIR.mkdir(exist_ok=True)
        out_path = OUT_DIR / out_name
        doc.save(out_path, garbage=3, deflate=True)
        page_count = doc.page_count
    finally:
        doc.close()
    return out_path, toc, entries, page_count


def verify(out_path: Path, src_path: Path, toc: list, entries: list, page_count: int) -> None:
    doc = fitz.open(out_path)
    try:
        actual_toc = doc.get_toc(simple=True)
        if doc.page_count != page_count:
            raise AssertionError(f"{out_path.name}: page count changed")
    finally:
        doc.close()

    if len(actual_toc) != len(toc):
        raise AssertionError(
            f"{out_path.name}: outline length {len(actual_toc)} != {len(toc)}"
        )
    for exp, act in zip(toc, actual_toc):
        if exp[:3] != act[:3]:
            raise AssertionError(f"{out_path.name}: outline entry mismatch: {exp} vs {act}")
    verify_links(out_path, src_path, entries)
    log.info(f"{out_path.name}: verified {len(actual_toc)} bookmarks, {page_count} pages")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build final bookmarked + linked PDFs.")
    ap.add_argument("--style", choices=["icon", "chip", "card", "footnote"], default="card")
    args = ap.parse_args()

    for vol, pdf_name, json_name, out_name in VOLUMES:
        log.info(f"=== building vol {vol} ({args.style}) ===")
        out_path, toc, entries, page_count = build_one(
            vol, pdf_name, json_name, out_name, args.style
        )
        counts = level_counts(toc)
        size_mb = out_path.stat().st_size / 1_048_576
        log.info(
            f"{out_name}: {len(toc)} bookmarks "
            f"(top={counts[1]}, sec={counts[2]}, sub={counts[3]}) + {len(entries)} video links, "
            f"{size_mb:.1f} MB"
        )
        verify(out_path, SCRIPT_DIR / pdf_name, toc, entries, page_count)

    log.info("Done: final PDFs in out_pdf/ (bookmarks + video links, verified).")


if __name__ == "__main__":
    main()
