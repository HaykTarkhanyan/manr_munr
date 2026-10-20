"""Place video links near PDF pages from a JSON config, in a chosen visual style.

Reads video_links.json (keyed by volume), draws a clickable link on each listed
page of the bookmarked PDFs, and saves INCREMENTALLY over a copy of the source so
only the new annotation objects are appended (KB, not MB). Everything is drawn as
vector + base-14 Helvetica, so no images or fonts get embedded -> file size barely
moves.

Styles:
  icon      red play-button badge (vector only, no text)            -> smallest
  chip      play triangle + label in a rounded pill (Helvetica)     -> shows label
  card      play button + bold label (wraps) + the URL              -> most informative
  footnote  thin rule + 'Video - <label>: <url>' line at page foot  -> least intrusive

Card labels are drawn in an embedded Armenian-capable font (chip/footnote labels are
still base-14 Helvetica, Latin only). Saving INCREMENTALLY embeds that whole face
(~+1 MB); build.py does a full save plus doc.subset_fonts() and pays only KB - so
use build.py for the real output, and this script for quick per-style previews.

Usage:
  python opus_4_8_musoyan_qrs/place_video_links.py --style icon
  python opus_4_8_musoyan_qrs/place_video_links.py --style chip --volume 1
"""

import argparse
import json
import logging
import shutil
import sys
from collections import Counter, defaultdict
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
FONT = "helv"  # base-14, never embedded; fine for URLs (pure Latin)
# Card labels are Armenian, which base-14 fonts cannot encode (they render as dots,
# silently). So labels use an embedded Armenian-capable face; build.py subsets it on
# save so the whole ~2 MB font costs only KB in the output.
LABEL_TTF = "C:/Windows/Fonts/seguisb.ttf"  # Segoe UI Semibold, has Armenian glyphs
LABEL_FONTNAME = "SegoeUISemibold"
LABEL_FONT = fitz.Font(fontfile=LABEL_TTF)

LABEL_SIZE = 8.5
URL_SIZE = 7.5
CARD_TEXT_W = 135.0  # cap the text column so two cards fit side by side on a 420pt page
CARD_LINES = 2
CARD_LINE_H = 11.0
CHIP_TEXT_W = 150.0
BADGE_PAD = 6.0  # clear space demanded around a badge; 0 lets it sit 1pt off a heading


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


def text_len(text: str, fontname: str, fontsize: float) -> float:
    """Text width; fitz.get_text_length only knows base-14 fonts, so the embedded
    label face measures through its Font object."""
    if fontname == LABEL_FONTNAME:
        return LABEL_FONT.text_length(text, fontsize=fontsize)
    return fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)


def truncate(text: str, maxw: float, fontname: str, fontsize: float, force: bool = False) -> str:
    """Shorten text to fit maxw, appending '...' whenever anything is cut."""
    if not force and text_len(text, fontname, fontsize) <= maxw:
        return text
    while text and text_len(f"{text}...", fontname, fontsize) > maxw:
        text = text[:-1]
    return f"{text.rstrip()}..."


def wrap(text: str, maxw: float, fontname: str, fontsize: float, max_lines: int) -> list:
    """Break text into at most max_lines lines of width maxw; elided lines end in '...'."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if not cur or text_len(trial, fontname, fontsize) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if not lines:  # empty / whitespace-only label
        return [""]
    dropped = len(lines) > max_lines
    lines = lines[:max_lines]
    lines[-1] = truncate(lines[-1], maxw, fontname, fontsize, force=dropped)
    return lines


def chip_text(label: str) -> str:
    return truncate(label, CHIP_TEXT_W, FONT, 8)


def badge_size(style: str, label: str, url: str = "") -> tuple:
    """(width, height) of the clickable badge for anchoring."""
    if style == "icon":
        return 24.0, 17.0
    if style == "chip":
        text_w = text_len(chip_text(label), FONT, 8)
        return 5 + 9 + 4 + text_w + 5, 16.0
    if style == "card":
        w, h, _short, _lines = card_dims(label, url)
        return w, h
    raise ValueError(f"badge_size: unsupported style {style!r}")


def header_clear_y(page: fitz.Page, margin: float = 18.0) -> float:
    """Y just below the page number / running head, so top badges don't collide with it."""
    h = page.rect.height
    # only the very top band: page number / running head (not centered chapter titles)
    header_bottoms = [b[3] for b in page.get_text("blocks")
                      if b[1] < h * 0.07 and b[4].strip()]
    return (max(header_bottoms) + 14) if header_bottoms else margin + 26


def occupied_rects(page: fitz.Page) -> list:
    """Everything a badge must not cover: text blocks plus inline images.

    Both books are page scans, so every page carries one full-page background image;
    counting that as occupied would leave nowhere to put anything. The small images
    are the typeset formulas, which do not appear in the text layer at all - miss
    them and a badge lands on top of an equation.
    """
    page_area = page.rect.get_area()
    rects = [fitz.Rect(b[:4]) for b in page.get_text("blocks") if b[4].strip()]
    rects += [fitz.Rect(im["bbox"]) for im in page.get_image_info()
              if fitz.Rect(im["bbox"]).get_area() < page_area * 0.9]
    return rects


def _slot_blocks(page: fitz.Page, taken) -> list:
    """Rects a badge must avoid: text/formulas plus badges already placed on the page
    (dual-lecturer chapters put two cards on one page); drawn badges are invisible to
    the text/image scan, so callers pass them in via `taken`."""
    return occupied_rects(page) + [fitz.Rect(r) for r in taken]


def _is_clear(blocks: list, x: float, y: float, w: float, h: float) -> bool:
    badge = fitz.Rect(x, y, x + w, y + h) + (-BADGE_PAD, -BADGE_PAD, BADGE_PAD, BADGE_PAD)
    return not any(badge.intersects(b) for b in blocks)


def _no_slot(page: fitz.Page, x: float, w: float, h: float):
    log.error(f"page {page.number + 1}: no {w:.0f}x{h:.0f}pt gap free of text at x={x:.0f}")
    raise RuntimeError(
        f"page {page.number + 1}: nowhere to place a {w:.0f}x{h:.0f}pt badge without "
        f"covering text - use a smaller style, or an explicit [x, y] in video_links.json"
    )


def bottom_slot_y(page: fitz.Page, x: float, w: float, h: float,
                  margin: float = 18.0, step: float = 4.0, taken: list = ()) -> float:
    """Scan up from the bottom margin for a clear y (used by the bottom-* anchors,
    and as the fallback when the upper half is full)."""
    blocks = _slot_blocks(page, taken)
    H = page.rect.height
    y = H - margin - h
    while y > H * 0.5:
        if _is_clear(blocks, x, y, w, h):
            return y
        y -= step
    _no_slot(page, x, w, h)


def clear_slot_y(page: fitz.Page, x: float, w: float, h: float, top_start: float,
                 margin: float = 18.0, step: float = 4.0, taken: list = ()) -> float:
    """A y where the badge's rect avoids text and formulas: prefer top, else the bottom."""
    blocks = _slot_blocks(page, taken)
    H = page.rect.height
    y = top_start                       # scan down through the upper part of the page
    while y <= H * 0.45:
        if _is_clear(blocks, x, y, w, h):
            return y
        y += step
    y = bottom_slot_y(page, x, w, h, margin, step, taken)
    log.warning(f"page {page.number + 1}: no clear slot in the upper half, "
                f"placed the badge at the page foot (y={y:.0f})")
    return y


def anchor_xy(page: fitz.Page, position, w: float, h: float, margin: float = 18.0,
              taken: list = ()) -> tuple:
    pr = page.rect
    W, H = pr.width, pr.height
    if w > W - 2 * margin or h > H - 2 * margin:
        raise ValueError(
            f"page {page.number + 1}: a {w:.0f}x{h:.0f}pt badge does not fit inside the "
            f"{W:.0f}x{H:.0f}pt page with a {margin:.0f}pt margin - shorten the label"
        )
    if isinstance(position, (list, tuple)):
        x, y = float(position[0]), float(position[1])
        if not (0 <= x and x + w <= W and 0 <= y and y + h <= H):
            raise ValueError(
                f"page {page.number + 1}: explicit position {list(position)} puts a "
                f"{w:.0f}x{h:.0f}pt badge off the {W:.0f}x{H:.0f}pt page"
            )
        return x, y
    starts = {
        "top-right":    (W - margin - w, header_clear_y(page, margin)),
        "top-left":     (margin, header_clear_y(page, margin)),
        "right-margin": (W - margin - w, H * 0.40),
        "bottom-right": (W - margin - w, H - margin - h),
        "bottom-left":  (margin, H - margin - h),
        "bottom-center": ((W - w) / 2, H - margin - h),
    }
    if position not in starts:
        raise ValueError(f"Unknown position {position!r}")
    x, y = starts[position]
    if position in ("top-right", "top-left", "right-margin"):
        y = clear_slot_y(page, x, w, h, y, margin, taken=taken)  # keep off the text
    elif position in ("bottom-right", "bottom-left", "bottom-center"):
        y = bottom_slot_y(page, x, w, h, margin, taken=taken)  # keep off footnotes
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
    page.insert_text((x + 16, y + h / 2 + 3), chip_text(label),
                     fontname=FONT, fontsize=8, color=DARK_RED)
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
        # incremental: append only the changes -> tiny delta over the source
        doc.save(out, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    finally:
        doc.close()

    delta_kb = (out.stat().st_size - src.stat().st_size) / 1024
    log.info(f"vol{vol} [{style}]: {len(entries)} links -> {out.name} "
             f"(+{delta_kb:.1f} KB over source)")
    return out


def uri_counts(path: Path) -> Counter:
    """URI link annotations per 1-based page number."""
    doc = fitz.open(path)
    try:
        return Counter(p.number + 1 for p in doc
                       for lk in p.get_links() if lk.get("kind") == fitz.LINK_URI)
    finally:
        doc.close()


def verify_links(out: Path, src: Path, entries: list) -> None:
    """Confirm every configured page gained its links.

    Compares against the source page by page rather than totalling the document:
    vol 1 already ships with one URI link, so a whole-document count would let a
    missing badge slip through.
    """
    want = Counter(e["page"] for e in entries)
    before, after = uri_counts(src), uri_counts(out)
    for page, n in sorted(want.items()):
        added = after[page] - before[page]
        if added < n:
            raise AssertionError(
                f"{out.name}: page {page} gained {added} URI link(s), expected {n}"
            )
    log.info(f"{out.name}: verified {sum(want.values())} new clickable link(s) "
             f"on {len(want)} page(s)")


def card_dims(label: str, url: str) -> tuple:
    """(width, height, url without scheme, wrapped label lines) for the card badge."""
    short = url.replace("https://", "").replace("http://", "")
    lines = wrap(label, CARD_TEXT_W, LABEL_FONTNAME, LABEL_SIZE, CARD_LINES)
    text_w = max(
        max(text_len(ln, LABEL_FONTNAME, LABEL_SIZE) for ln in lines),
        text_len(short, FONT, URL_SIZE),
    )
    width = 7 + 18 + 8 + text_w + 9                 # pad + play button + gap + text + pad
    height = 19 + len(lines) * CARD_LINE_H          # one label line -> the original 30pt
    return width, height, short, lines


def draw_card(page: fitz.Page, x: float, y: float, label: str, url: str) -> None:
    """A small 'watch' card: soft shadow, red play button, bold label (wrapped) + the URL."""
    w, h, short, lines = card_dims(label, url)
    rect = fitz.Rect(x, y, x + w, y + h)
    page.draw_rect(fitz.Rect(x + 1.6, y + 1.9, x + w + 1.6, y + h + 1.9),
                   color=None, fill=(0.86, 0.86, 0.86), radius=0.16)        # soft shadow
    page.draw_rect(rect, color=(0.80, 0.80, 0.80), fill=WHITE, width=0.7, radius=0.16)  # card
    pb = fitz.Rect(x + 7, y + (h - 18) / 2, x + 25, y + (h - 18) / 2 + 18)  # red play button
    page.draw_rect(pb, color=YT_RED, fill=YT_RED, radius=0.3)
    play_triangle(page, (pb.x0 + pb.x1) / 2, (pb.y0 + pb.y1) / 2, 7, color=WHITE)
    tx, ty = pb.x1 + 8, y + 13
    for line in lines:
        page.insert_text((tx, ty), line, fontname=LABEL_FONTNAME, fontfile=LABEL_TTF,
                         fontsize=LABEL_SIZE, color=(0.13, 0.13, 0.13))
        ty += CARD_LINE_H
    page.insert_text((tx, ty), short, fontname=FONT, fontsize=URL_SIZE, color=(0.00, 0.32, 0.66))
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
            verify_links(out, SOURCE[vol], load_entries(vol))
    log.info("Done.")


if __name__ == "__main__":
    main()
