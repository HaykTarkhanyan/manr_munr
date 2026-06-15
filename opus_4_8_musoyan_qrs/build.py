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
  python opus_4_8_musoyan_qrs/build.py                # icon style, both volumes
  python opus_4_8_musoyan_qrs/build.py --style chip
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

from apply_bookmarks import build_toc, level_counts
from place_video_links import (
    badge_size, anchor_xy, draw_footnote, load_entries, DRAWERS,
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


def draw_links(doc: fitz.Document, vol: str, style: str) -> int:
    entries = load_entries(vol)
    footnote_slot = defaultdict(int)
    for e in entries:
        page = doc[e["page"] - 1]
        this_style = e.get("style", style)
        if this_style == "footnote":
            draw_footnote(page, e["label"], e["url"], footnote_slot[page.number])
            footnote_slot[page.number] += 1
        else:
            w, h = badge_size(this_style, e["label"], e["url"])
            x, y = anchor_xy(page, e["position"], w, h)
            DRAWERS[this_style](page, x, y, e["label"], e["url"])
    return len(entries)


def build_one(vol: str, pdf_name: str, json_name: str, out_name: str, style: str):
    pdf_path = SCRIPT_DIR / pdf_name
    json_path = SCRIPT_DIR / json_name
    for required in (pdf_path, json_path):
        if not required.exists():
            raise FileNotFoundError(f"Missing input: {required}")

    doc = fitz.open(pdf_path)
    try:
        toc = build_toc(json.loads(json_path.read_text(encoding="utf-8")), doc.page_count)
        if doc.set_toc(toc) != len(toc):
            raise RuntimeError("set_toc wrote an unexpected number of entries")
        doc.set_pagemode("UseOutlines")
        n_links = draw_links(doc, vol, style)
        OUT_DIR.mkdir(exist_ok=True)
        out_path = OUT_DIR / out_name
        doc.save(out_path, garbage=3, deflate=True)
        page_count = doc.page_count
    finally:
        doc.close()
    return out_path, toc, n_links, page_count


def verify(out_path: Path, toc: list, n_links: int, page_count: int) -> None:
    doc = fitz.open(out_path)
    try:
        actual_toc = doc.get_toc(simple=True)
        if doc.page_count != page_count:
            raise AssertionError(f"{out_path.name}: page count changed")
        uri_links = sum(
            1 for p in doc for lk in p.get_links() if lk.get("kind") == fitz.LINK_URI
        )
    finally:
        doc.close()

    if len(actual_toc) != len(toc):
        raise AssertionError(
            f"{out_path.name}: outline length {len(actual_toc)} != {len(toc)}"
        )
    for exp, act in zip(toc, actual_toc):
        if exp[:3] != act[:3]:
            raise AssertionError(f"{out_path.name}: outline entry mismatch: {exp} vs {act}")
    if uri_links < n_links:
        raise AssertionError(
            f"{out_path.name}: expected >= {n_links} URI links, found {uri_links}"
        )
    log.info(
        f"{out_path.name}: verified {len(actual_toc)} bookmarks + {uri_links} link(s), "
        f"{page_count} pages"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Build final bookmarked + linked PDFs.")
    ap.add_argument("--style", choices=["icon", "chip", "card", "footnote"], default="card")
    args = ap.parse_args()

    for vol, pdf_name, json_name, out_name in VOLUMES:
        log.info(f"=== building vol {vol} ({args.style}) ===")
        out_path, toc, n_links, page_count = build_one(
            vol, pdf_name, json_name, out_name, args.style
        )
        counts = level_counts(toc)
        size_mb = out_path.stat().st_size / 1_048_576
        log.info(
            f"{out_name}: {len(toc)} bookmarks "
            f"(top={counts[1]}, sec={counts[2]}, sub={counts[3]}) + {n_links} video links, "
            f"{size_mb:.1f} MB"
        )
        verify(out_path, toc, n_links, page_count)

    log.info("Done: final PDFs in out_pdf/ (bookmarks + video links, verified).")


if __name__ == "__main__":
    main()
