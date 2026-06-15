"""Place video links near PDF pages from a JSON config, in a chosen visual style.

Reads video_links.json (keyed by volume), draws a clickable link on each listed
page of the bookmarked PDFs, and saves INCREMENTALLY over a copy of the source so
only the new annotation objects are appended (KB, not MB). Everything is drawn as
vector + base-14 Helvetica, so no images or fonts get embedded -> file size barely
moves.

Styles:
  icon      red play-button badge (vector only, no text)            -> smallest
  chip      play triangle + label in a rounded pill (Helvetica)     -> shows label
  footnote  thin rule + 'Video - <label>: <url>' line at page foot  -> least intrusive

Usage:
  python opus_4_8_musoyan_qrs/place_video_links.py --style icon
  python opus_4_8_musoyan_qrs/place_video_links.py --style chip --volume 1
"""

import argparse
import json
import logging
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOG_DIR = REPO_ROOT / "logs"
OUT_DIR = SCRIPT_DIR / "out_pdf"
CONFIG = SCRIPT_DIR / "video_links.json"

SOURCE = {
    "1": OUT_DIR / "musoyan_1_bookmarked.pdf",
    "2": OUT_DIR / "musoyan_2_bookmarked.pdf",
}

YT_RED = (0.84, 0.05, 0.05)
DARK_RED = (0.5, 0.0, 0.0)
WHITE = (1, 1, 1)
PILL_FILL = (1.0, 0.93, 0.93)
RULE_GREY = (0.75, 0.75, 0.75)
FONT = "helv"  # base-14, never embedded


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("place_video_links")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_DIR / "place_video_links.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


log = setup_logging()


def play_triangle(page: fitz.Page, cx: float, cy: float, size: float, color=WHITE) -> None:
    """Draw a small filled play triangle centered at (cx, cy)."""
    pts = [(cx - size * 0.5, cy - size * 0.62),
           (cx - size * 0.5, cy + size * 0.62),
           (cx + size * 0.7, cy)]
    shape = page.new_shape()
    shape.draw_polyline(pts)
    shape.finish(color=color, fill=color, closePath=True)
    shape.commit()


def add_link(page: fitz.Page, rect: fitz.Rect, url: str) -> None:
    page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": url})


def badge_size(style: str, label: str, url: str = "") -> tuple:
    """(width, height) of the clickable badge for anchoring."""
    if style == "icon":
        return 24.0, 17.0
    if style == "chip":
        text_w = fitz.get_text_length(label, fontname=FONT, fontsize=8)
        return 5 + 9 + 4 + text_w + 5, 16.0
    if style == "card":
        w, h, _ = card_dims(label, url)
        return w, h
    raise ValueError(f"badge_size: unsupported style {style!r}")


def header_clear_y(page: fitz.Page, margin: float = 18.0) -> float:
    """Y just below the page number / running head, so top badges don't collide with it."""
    h = page.rect.height
    # only the very top band: page number / running head (not centered chapter titles)
    header_bottoms = [b[3] for b in page.get_text("blocks")
                      if b[1] < h * 0.07 and b[4].strip()]
    return (max(header_bottoms) + 14) if header_bottoms else margin + 26


def clear_slot_y(page: fitz.Page, x: float, w: float, h: float, top_start: float,
                 margin: float = 18.0, step: float = 4.0) -> float:
    """A y where the badge's rect avoids all text: prefer top, else fall to the bottom."""
    blocks = [fitz.Rect(b[:4]) for b in page.get_text("blocks") if b[4].strip()]
    H = page.rect.height

    def is_clear(y: float) -> bool:
        badge = fitz.Rect(x, y, x + w, y + h)
        return not any(badge.intersects(b) for b in blocks)

    y = top_start                       # scan down through the upper part of the page
    while y <= H * 0.45:
        if is_clear(y):
            return y
        y += step
    y = H - margin - h                  # nothing up top -> scan up from the bottom margin
    while y > H * 0.5:
        if is_clear(y):
            return y
        y -= step
    return top_start                    # give up; best effort


def anchor_xy(page: fitz.Page, position, w: float, h: float, margin: float = 18.0) -> tuple:
    if isinstance(position, (list, tuple)):
        return float(position[0]), float(position[1])
    pr = page.rect
    W, H = pr.width, pr.height
    starts = {
        "top-right":    (W - margin - w, header_clear_y(page, margin)),
        "top-left":     (margin, header_clear_y(page, margin)),
        "right-margin": (W - margin - w, H * 0.40),
        "bottom-right": (W - margin - w, H - margin - h),
        "bottom-left":  (margin, H - margin - h),
    }
    if position not in starts:
        raise ValueError(f"Unknown position {position!r}")
    x, y = starts[position]
    if position in ("top-right", "top-left", "right-margin"):
        y = clear_slot_y(page, x, w, h, y, margin)  # keep off the text
    return x, y


def draw_icon(page: fitz.Page, x: float, y: float, label: str, url: str) -> None:
    w, h = badge_size("icon", label)
    rect = fitz.Rect(x, y, x + w, y + h)
    page.draw_rect(rect, color=YT_RED, fill=YT_RED, radius=0.28)
    play_triangle(page, x + w / 2, y + h / 2, 7, color=WHITE)
    add_link(page, rect, url)


def draw_chip(page: fitz.Page, x: float, y: float, label: str, url: str) -> None:
    w, h = badge_size("chip", label)
    rect = fitz.Rect(x, y, x + w, y + h)
    page.draw_rect(rect, color=YT_RED, fill=PILL_FILL, radius=0.45, width=0.6)
    play_triangle(page, x + 9, y + h / 2, 6, color=YT_RED)
    page.insert_text((x + 16, y + h / 2 + 3), label, fontname=FONT, fontsize=8, color=DARK_RED)
    add_link(page, rect, url)


def draw_footnote(page: fitz.Page, label: str, url: str, slot: int) -> None:
    pr = page.rect
    left, right = pr.x0 + 55, pr.x1 - 55
    y = pr.y1 - 30 - slot * 14
    page.draw_line((left, y), (right, y), color=RULE_GREY, width=0.5)
    play_triangle(page, left + 4, y + 8, 5, color=YT_RED)
    short = url.replace("https://", "").replace("http://", "")
    line = fitz.Rect(left, y + 2, right, y + 15)
    page.insert_text((left + 11, y + 11), f"Video - {label}:  {short}",
                     fontname=FONT, fontsize=8, color=DARK_RED)
    add_link(page, line, url)


def load_entries(vol: str) -> list:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    return cfg.get(vol, [])


def place(vol: str, style: str) -> Path:
    src = SOURCE[vol]
    if not src.exists():
        raise FileNotFoundError(f"Run apply_bookmarks.py first - missing {src}")
    entries = load_entries(vol)
    if not entries:
        log.info(f"vol{vol}: no entries in config, skipping")
        return None

    out = OUT_DIR / f"musoyan_{vol}_linked_{style}.pdf"
    shutil.copy(src, out)                       # copy so we can append incrementally
    doc = fitz.open(out)
    try:
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
        # incremental: append only the changes -> tiny delta over the source
        doc.save(out, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    finally:
        doc.close()

    delta_kb = (out.stat().st_size - src.stat().st_size) / 1024
    log.info(f"vol{vol} [{style}]: {len(entries)} links -> {out.name} "
             f"(+{delta_kb:.1f} KB over source)")
    return out


def verify(out: Path, expected: int) -> None:
    """Confirm the expected number of URI link annotations exist and resolve."""
    doc = fitz.open(out)
    try:
        found = sum(
            1 for p in doc for lk in p.get_links() if lk.get("kind") == fitz.LINK_URI
        )
    finally:
        doc.close()
    if found < expected:
        raise AssertionError(f"{out.name}: expected >= {expected} URI links, found {found}")
    log.info(f"{out.name}: verified {found} clickable URI link(s)")


def card_dims(label: str, url: str) -> tuple:
    short = url.replace("https://", "").replace("http://", "")
    label_w = fitz.get_text_length(label, fontname="hebo", fontsize=8.5)
    url_w = fitz.get_text_length(short, fontname=FONT, fontsize=7.5)
    width = 7 + 18 + 8 + max(label_w, url_w) + 9   # pad + play button + gap + text + pad
    return width, 30.0, short


def draw_card(page: fitz.Page, x: float, y: float, label: str, url: str) -> None:
    """A small 'watch' card: soft shadow, red play button, bold label + the URL."""
    w, h, short = card_dims(label, url)
    rect = fitz.Rect(x, y, x + w, y + h)
    page.draw_rect(fitz.Rect(x + 1.6, y + 1.9, x + w + 1.6, y + h + 1.9),
                   color=None, fill=(0.86, 0.86, 0.86), radius=0.16)        # soft shadow
    page.draw_rect(rect, color=(0.80, 0.80, 0.80), fill=WHITE, width=0.7, radius=0.16)  # card
    pb = fitz.Rect(x + 7, y + (h - 18) / 2, x + 25, y + (h - 18) / 2 + 18)  # red play button
    page.draw_rect(pb, color=YT_RED, fill=YT_RED, radius=0.3)
    play_triangle(page, (pb.x0 + pb.x1) / 2, (pb.y0 + pb.y1) / 2, 7, color=WHITE)
    tx = pb.x1 + 8
    page.insert_text((tx, y + 13), label, fontname="hebo", fontsize=8.5, color=(0.13, 0.13, 0.13))
    page.insert_text((tx, y + 24), short, fontname=FONT, fontsize=7.5, color=(0.00, 0.32, 0.66))
    add_link(page, rect, url)


DRAWERS = {"icon": draw_icon, "chip": draw_chip, "card": draw_card}


def main() -> None:
    ap = argparse.ArgumentParser(description="Place video links near PDF pages.")
    ap.add_argument("--style", choices=["icon", "chip", "card", "footnote"], default="card")
    ap.add_argument("--volume", choices=["1", "2", "all"], default="all")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    vols = ["1", "2"] if args.volume == "all" else [args.volume]
    for vol in vols:
        out = place(vol, args.style)
        if out is not None:
            verify(out, len(load_entries(vol)))
    log.info("Done.")


if __name__ == "__main__":
    main()
