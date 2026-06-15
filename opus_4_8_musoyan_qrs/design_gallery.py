"""Generate a gallery PDF of video-link badge designs, using a long Armenian title.

Purpose: try MANY visual options so we can pick one. Each option is drawn with the
same longish Armenian title to show how it handles length (wrap / truncate / inline).
Outputs out_pdf/design_gallery.pdf (and the caller renders it to PNG to view).
"""

import logging
import sys
from pathlib import Path

import fitz  # PyMuPDF

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "out_pdf"
LOG_DIR = SCRIPT_DIR.parent / "logs"

FONTS = {
    "reg":  fitz.Font(fontfile="C:/Windows/Fonts/segoeui.ttf"),
    "sb":   fitz.Font(fontfile="C:/Windows/Fonts/seguisb.ttf"),
    "bold": fitz.Font(fontfile="C:/Windows/Fonts/segoeuib.ttf"),
    "syl":  fitz.Font(fontfile="C:/Windows/Fonts/sylfaen.ttf"),
    "noto": fitz.Font(fontfile=str(SCRIPT_DIR.parent / "musoyan" / "NotoSansArmenian-Black.ttf")),
    "mono": fitz.Font(fontfile="C:/Windows/Fonts/segoeui.ttf"),
}

TITLE = "Զուգամետ հաջորդականությունների պարզագույն հատկությունները"
MED = "Մոնոտոն հաջորդականության սահմանը"
URL = "youtu.be/dQw4w9WgXcQ"

YT_RED = (0.80, 0.05, 0.05)
RED = (0.84, 0.11, 0.11)
DARK = (0.14, 0.14, 0.16)
GREY = (0.46, 0.46, 0.48)
LINK = (0.10, 0.32, 0.66)
TINT = (0.99, 0.92, 0.92)
BORDER = (0.80, 0.80, 0.82)
DARKBG = (0.15, 0.16, 0.20)
SHADOW = (0.87, 0.87, 0.88)
WHITE = (1, 1, 1)


def log_setup():
    LOG_DIR.mkdir(exist_ok=True)
    lg = logging.getLogger("gallery")
    lg.setLevel(logging.INFO)
    lg.handlers.clear()
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(message)s"))
    lg.addHandler(h)
    return lg


log = log_setup()


# ---- text helpers -----------------------------------------------------------
def tlen(font, s, sz):
    return font.text_length(s, fontsize=sz)


def wrap(font, s, sz, maxw, max_lines=3):
    out, cur = [], ""
    for word in s.split(" "):
        trial = (cur + " " + word).strip()
        if tlen(font, trial, sz) <= maxw or not cur:
            cur = trial
        else:
            out.append(cur)
            cur = word
        if len(out) == max_lines:
            break
    if cur and len(out) < max_lines:
        out.append(cur)
    if tlen(font, out[-1], sz) > maxw:  # last line still too long -> ellipsize
        out[-1] = truncate(font, out[-1], sz, maxw)
    return out


def truncate(font, s, sz, maxw):
    if tlen(font, s, sz) <= maxw:
        return s
    while s and tlen(font, s + "…", sz) > maxw:
        s = s[:-1]
    return s.rstrip() + "…"


def T(page, x, y_base, s, font, sz, color=DARK):
    tw = fitz.TextWriter(page.rect)
    tw.append((x, y_base), s, font=font, fontsize=sz)
    tw.write_text(page, color=color)


def play_tri(page, cx, cy, size, color=WHITE):
    pts = [(cx - size * 0.5, cy - size * 0.62), (cx - size * 0.5, cy + size * 0.62), (cx + size * 0.72, cy)]
    sh = page.new_shape()
    sh.draw_polyline(pts)
    sh.finish(color=color, fill=color, closePath=True)
    sh.commit()


def play_square(page, x, y, s, fill=YT_RED, tri=WHITE, radius=0.3):
    page.draw_rect(fitz.Rect(x, y, x + s, y + s), color=fill, fill=fill, radius=radius)
    play_tri(page, x + s / 2, y + s / 2, s * 0.42, tri)


def play_circle(page, cx, cy, r, fill=YT_RED, tri=WHITE):
    page.draw_circle((cx, cy), r, color=fill, fill=fill)
    play_tri(page, cx, cy, r * 0.85, tri)


# ---- badge designs: fn(page, x, y, maxw) -> height used ----------------------
def d_icon(page, x, y, maxw):
    play_square(page, x, y, 26, radius=0.32)
    return 26


def d_pill_solid(page, x, y, maxw):
    h, sz = 21, 9.5
    txt = truncate(FONTS["sb"], TITLE, sz, maxw - 34)
    w = 12 + tlen(FONTS["sb"], txt, sz) + 14
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=YT_RED, fill=YT_RED, radius=0.5)
    play_tri(page, x + 12, y + h / 2, 6, WHITE)
    T(page, x + 20, y + h / 2 + 3.2, txt, FONTS["sb"], sz, WHITE)
    return h


def d_pill_outline(page, x, y, maxw):
    h, sz = 21, 9.5
    txt = truncate(FONTS["sb"], TITLE, sz, maxw - 34)
    w = 12 + tlen(FONTS["sb"], txt, sz) + 14
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=YT_RED, fill=WHITE, width=0.9, radius=0.5)
    play_tri(page, x + 12, y + h / 2, 6, YT_RED)
    T(page, x + 20, y + h / 2 + 3.2, txt, FONTS["sb"], sz, (0.45, 0.0, 0.0))
    return h


def d_pill_tint(page, x, y, maxw):
    h, sz = 21, 9.5
    txt = truncate(FONTS["sb"], TITLE, sz, maxw - 34)
    w = 12 + tlen(FONTS["sb"], txt, sz) + 14
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=None, fill=TINT, radius=0.5)
    play_tri(page, x + 12, y + h / 2, 6, YT_RED)
    T(page, x + 20, y + h / 2 + 3.2, txt, FONTS["sb"], sz, (0.40, 0.0, 0.0))
    return h


def d_inline(page, x, y, maxw):
    sz = 10
    play_tri(page, x + 4, y + 7, 5.5, YT_RED)
    lines = wrap(FONTS["reg"], TITLE, sz, maxw - 14, max_lines=3)
    yy = y + 10
    for ln in lines:
        T(page, x + 12, yy, ln, FONTS["reg"], sz, LINK)
        page.draw_line((x + 12, yy + 2), (x + 12 + tlen(FONTS["reg"], ln, sz), yy + 2), color=LINK, width=0.4)
        yy += 13
    return yy - y - 3


def d_watchbtn(page, x, y, maxw):
    sz = 10
    bw, bh = 46, 19
    page.draw_rect(fitz.Rect(x, y, x + bw, y + bh), color=YT_RED, fill=YT_RED, radius=0.28)
    play_tri(page, x + 11, y + bh / 2, 6, WHITE)
    T(page, x + 19, y + bh / 2 + 3.2, "Դիտել", FONTS["sb"], 9.5, WHITE)
    lines = wrap(FONTS["reg"], TITLE, sz, maxw - bw - 12, max_lines=2)
    yy = y + 8
    for ln in lines:
        T(page, x + bw + 10, yy, ln, FONTS["reg"], sz, DARK)
        yy += 12.5
    return max(bh, yy - y - 4)


def d_footnote(page, x, y, maxw):
    sz = 9
    page.draw_line((x, y), (x + maxw, y), color=BORDER, width=0.5)
    play_tri(page, x + 4, y + 9, 5, YT_RED)
    s = truncate(FONTS["reg"], f"{TITLE}  ·  {URL}", sz, maxw - 12)
    T(page, x + 11, y + 12, s, FONTS["reg"], sz, (0.42, 0.0, 0.0))
    return 16


def _card_text_block(page, tx, ty, title, font_title, sz_t, color_t, maxw, url=URL):
    lines = wrap(font_title, title, sz_t, maxw, max_lines=3)
    yy = ty
    for ln in lines:
        T(page, tx, yy, ln, font_title, sz_t, color_t)
        yy += sz_t + 3.0
    T(page, tx, yy + 1, url, FONTS["reg"], 8, LINK)
    return yy + 9 - ty


def d_card_shadow(page, x, y, maxw):
    tw_ = 250
    th = _card_height(FONTS["sb"], 9.5, tw_)
    w = 7 + 22 + 9 + tw_ + 10
    page.draw_rect(fitz.Rect(x + 1.8, y + 2.0, x + w + 1.8, y + th + 2.0), color=None, fill=SHADOW, radius=0.10)
    page.draw_rect(fitz.Rect(x, y, x + w, y + th), color=BORDER, fill=WHITE, width=0.7, radius=0.10)
    play_square(page, x + 7, y + (th - 22) / 2, 22, radius=0.3)
    _card_text_block(page, x + 38, y + 13, TITLE, FONTS["sb"], 9.5, DARK, tw_)
    return th


def d_card_flat(page, x, y, maxw):
    tw_ = 250
    th = _card_height(FONTS["sb"], 9.5, tw_)
    w = 7 + 22 + 9 + tw_ + 10
    page.draw_rect(fitz.Rect(x, y, x + w, y + th), color=BORDER, fill=WHITE, width=0.8, radius=0.08)
    play_circle(page, x + 18, y + th / 2, 11)
    _card_text_block(page, x + 38, y + 13, TITLE, FONTS["sb"], 9.5, DARK, tw_)
    return th


def d_card_left_accent(page, x, y, maxw):
    tw_ = 258
    th = _card_height(FONTS["sb"], 9.5, tw_)
    w = 6 + 10 + tw_ + 12
    page.draw_rect(fitz.Rect(x, y, x + w, y + th), color=(0.93, 0.93, 0.94), fill=(0.985, 0.985, 0.99), width=0.6, radius=0.08)
    page.draw_rect(fitz.Rect(x, y, x + 4.5, y + th), color=None, fill=YT_RED)
    play_tri(page, x + 14, y + 12, 5.5, YT_RED)
    T(page, x + 24, y + 14.5, "Տեսանյութ", FONTS["sb"], 7.5, GREY)
    _card_text_block(page, x + 14, y + 27, TITLE, FONTS["sb"], 9.5, DARK, tw_)
    return th


def d_card_red_header(page, x, y, maxw):
    tw_ = 250
    body_h = _card_height(FONTS["sb"], 9.5, tw_) - 4
    head_h = 16
    w = tw_ + 24
    page.draw_rect(fitz.Rect(x, y, x + w, y + head_h + body_h), color=BORDER, fill=WHITE, width=0.7, radius=0.08)
    page.draw_rect(fitz.Rect(x, y, x + w, y + head_h), color=None, fill=YT_RED)
    play_tri(page, x + 11, y + head_h / 2, 5, WHITE)
    T(page, x + 19, y + head_h / 2 + 3, "ԴԻՏԵԼ ՏԵՍԱՆՅՈՒԹԸ", FONTS["sb"], 8, WHITE)
    _card_text_block(page, x + 12, y + head_h + 13, TITLE, FONTS["sb"], 9.5, DARK, tw_)
    return head_h + body_h


def d_card_dark(page, x, y, maxw):
    tw_ = 250
    th = _card_height(FONTS["sb"], 9.5, tw_)
    w = 7 + 22 + 9 + tw_ + 10
    page.draw_rect(fitz.Rect(x, y, x + w, y + th), color=None, fill=DARKBG, radius=0.10)
    play_square(page, x + 7, y + (th - 22) / 2, 22, radius=0.3)
    lines = wrap(FONTS["sb"], TITLE, 9.5, tw_, max_lines=3)
    yy = y + 13
    for ln in lines:
        T(page, x + 38, yy, ln, FONTS["sb"], 9.5, (0.96, 0.96, 0.97))
        yy += 12.5
    T(page, x + 38, yy + 1, URL, FONTS["reg"], 8, (0.55, 0.72, 1.0))
    return th


def d_big_play(page, x, y, maxw):
    tw_ = 250
    th = _card_height(FONTS["bold"], 10, tw_)
    play_square(page, x, y + (th - 34) / 2, 34, radius=0.28)
    _card_text_block(page, x + 44, y + 13, TITLE, FONTS["bold"], 10, DARK, tw_)
    return th


def d_underline_min(page, x, y, maxw):
    sz = 10
    play_tri(page, x + 4, y + 8, 5.5, YT_RED)
    lines = wrap(FONTS["sb"], TITLE, sz, maxw - 14, max_lines=2)
    yy = y + 11
    for ln in lines:
        T(page, x + 12, yy, ln, FONTS["sb"], sz, DARK)
        yy += 13
    page.draw_line((x + 12, yy - 11), (x + 12 + tlen(FONTS["sb"], lines[-1], sz), yy - 11), color=YT_RED, width=1.1)
    T(page, x + 12, yy, URL, FONTS["reg"], 7.5, GREY)
    return yy - y + 2


def d_numbered(page, x, y, maxw):
    h = 20
    page.draw_rect(fitz.Rect(x, y, x + 34, y + h), color=YT_RED, fill=YT_RED, radius=0.3)
    play_tri(page, x + 10, y + h / 2, 5.5, WHITE)
    T(page, x + 18, y + h / 2 + 3.3, "12", FONTS["bold"], 10, WHITE)
    T(page, x + 42, y + h / 2 + 3, "(վերնագիրը՝ տեսանյութերի ցանկում)", FONTS["reg"], 8.5, GREY)
    return h


def d_banner(page, x, y, maxw):
    h = 30
    page.draw_rect(fitz.Rect(x, y, x + maxw, y + h), color=None, fill=(0.965, 0.965, 0.975), radius=0.10)
    page.draw_rect(fitz.Rect(x, y, x + 3.5, y + h), color=None, fill=YT_RED)
    play_circle(page, x + 18, y + h / 2, 9)
    t1 = truncate(FONTS["sb"], TITLE, 9.5, maxw - 80)
    T(page, x + 33, y + 13, t1, FONTS["sb"], 9.5, DARK)
    T(page, x + 33, y + 24, URL, FONTS["reg"], 8, LINK)
    return h


def d_sylfaen_card(page, x, y, maxw):
    tw_ = 250
    th = _card_height(FONTS["syl"], 10.5, tw_)
    w = 7 + 22 + 9 + tw_ + 10
    page.draw_rect(fitz.Rect(x, y, x + w, y + th), color=BORDER, fill=WHITE, width=0.7, radius=0.10)
    play_square(page, x + 7, y + (th - 22) / 2, 22, radius=0.3)
    lines = wrap(FONTS["syl"], TITLE, 10.5, tw_, max_lines=3)
    yy = y + 13
    for ln in lines:
        T(page, x + 38, yy, ln, FONTS["syl"], 10.5, DARK)
        yy += 13.5
    T(page, x + 38, yy + 1, URL, FONTS["syl"], 8.5, LINK)
    return th


def d_noto_pill(page, x, y, maxw):
    h, sz = 22, 9
    txt = truncate(FONTS["noto"], MED, sz, maxw - 34)
    w = 12 + tlen(FONTS["noto"], txt, sz) + 14
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=YT_RED, fill=YT_RED, radius=0.5)
    play_tri(page, x + 12, y + h / 2, 6, WHITE)
    T(page, x + 20, y + h / 2 + 3.2, txt, FONTS["noto"], sz, WHITE)
    return h


def _card_height(font, sz, maxw):
    n = len(wrap(font, TITLE, sz, maxw, max_lines=3))
    return 13 + n * (sz + 3.0) + 11


# ---- simple generic-word labels (short text -> no long-title problem) --------
def _word_pill(page, x, y, word, fill, txt_col, font=None, sz=10, outline=False, tint=False):
    f = font or FONTS["sb"]
    h = 22
    w = 13 + 7 + tlen(f, word, sz) + 14
    r = fitz.Rect(x, y, x + w, y + h)
    if tint:
        page.draw_rect(r, color=None, fill=TINT, radius=0.5)
    elif outline:
        page.draw_rect(r, color=YT_RED, fill=WHITE, width=0.9, radius=0.5)
    else:
        page.draw_rect(r, color=fill, fill=fill, radius=0.5)
    play_tri(page, x + 13, y + h / 2, 6, txt_col if (outline or tint) else WHITE)
    T(page, x + 22, y + h / 2 + 3.3, word, f, sz, txt_col)
    return h


def w_tesagrutyun_solid(page, x, y, maxw):
    return _word_pill(page, x, y, "Տեսագրություն", YT_RED, WHITE)


def w_tesanyut_solid(page, x, y, maxw):
    return _word_pill(page, x, y, "Տեսանյութ", YT_RED, WHITE)


def w_ditel_outline(page, x, y, maxw):
    return _word_pill(page, x, y, "Դիտել", WHITE, (0.45, 0, 0), outline=True)


def w_tesadas_tint(page, x, y, maxw):
    return _word_pill(page, x, y, "Տեսադաս", TINT, (0.40, 0, 0), tint=True)


def w_ditel_btn(page, x, y, maxw):
    h, sz, word = 20, 10, "Դիտել"
    w = 12 + 7 + tlen(FONTS["bold"], word, sz) + 12
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=YT_RED, fill=YT_RED, radius=0.28)
    play_tri(page, x + 12, y + h / 2, 6, WHITE)
    T(page, x + 21, y + h / 2 + 3.3, word, FONTS["bold"], sz, WHITE)
    return h


def w_icon_word(page, x, y, maxw):
    play_square(page, x, y, 22, radius=0.3)
    T(page, x + 30, y + 15, "Տեսագրություն", FONTS["sb"], 11, DARK)
    return 22


def w_phrase_btn(page, x, y, maxw):
    h, sz, word = 22, 10, "Դիտել տեսանյութը"
    w = 13 + 7 + tlen(FONTS["sb"], word, sz) + 14
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=YT_RED, fill=YT_RED, radius=0.5)
    play_tri(page, x + 13, y + h / 2, 6, WHITE)
    T(page, x + 22, y + h / 2 + 3.3, word, FONTS["sb"], sz, WHITE)
    return h


def w_minimal(page, x, y, maxw):
    sz, word = 11, "Տեսանյութ"
    play_tri(page, x + 4, y + 9, 6, YT_RED)
    T(page, x + 13, y + 12, word, FONTS["sb"], sz, DARK)
    page.draw_line((x + 13, y + 14), (x + 13 + tlen(FONTS["sb"], word, sz), y + 14), color=YT_RED, width=1.1)
    return 16


def w_circle_word(page, x, y, maxw):
    play_circle(page, x + 11, y + 11, 11)
    T(page, x + 30, y + 15, "Տեսագրություն", FONTS["sb"], 11, DARK)
    return 22


OPTIONS = [
    ("1 · Icon only (title lives in the bookmark / legend)", d_icon),
    ("2 · Pill, solid red — single line, truncates (…)", d_pill_solid),
    ("3 · Pill, outline — single line, truncates", d_pill_outline),
    ("4 · Pill, light tint — single line, truncates", d_pill_tint),
    ("5 · Inline link — ▶ + underlined text, wraps", d_inline),
    ("6 · 'Դիտել' button + title beside (wraps)", d_watchbtn),
    ("7 · Footnote rule — title · url, truncates", d_footnote),
    ("8 · Numbered chip + legend note", d_numbered),
    ("9 · Card, soft shadow — bold title wraps + url", d_card_shadow),
    ("10 · Card, flat outline + play circle", d_card_flat),
    ("11 · Card, red left accent + 'Տեսանյութ'", d_card_left_accent),
    ("12 · Card, red header bar 'ԴԻՏԵԼ ՏԵՍԱՆՅՈՒԹԸ'", d_card_red_header),
    ("13 · Card, dark theme", d_card_dark),
    ("14 · Big play button + title + url", d_big_play),
    ("15 · Minimal — title + red underline + url", d_underline_min),
    ("16 · Subtle banner bar (full width)", d_banner),
    ("17 · Card with Sylfaen font (vs Segoe UI above)", d_sylfaen_card),
    ("18 · Pill with Noto Armenian Black (heavy)", d_noto_pill),
    ("19 · Simple word — pill 'Տեսագրություն'", w_tesagrutyun_solid),
    ("20 · Simple word — pill 'Տեսանյութ'", w_tesanyut_solid),
    ("21 · Simple word — outline 'Դիտել'", w_ditel_outline),
    ("22 · Simple word — tint 'Տեսադաս' (video lesson)", w_tesadas_tint),
    ("23 · Simple word — button '▶ Դիտել'", w_ditel_btn),
    ("24 · Simple word — play icon + 'Տեսագրություն'", w_icon_word),
    ("25 · Simple phrase — 'Դիտել տեսանյութը'", w_phrase_btn),
    ("26 · Simple word — minimal '▶ Տեսանյութ' + underline", w_minimal),
    ("27 · Simple word — play circle + 'Տեսագրություն'", w_circle_word),
]


def build():
    OUT_DIR.mkdir(exist_ok=True)
    doc = fitz.open()
    PW, PH = 600, 880
    margin = 34
    per_page = 9
    label_font = FONTS["sb"]

    for chunk_start in range(0, len(OPTIONS), per_page):
        chunk = OPTIONS[chunk_start:chunk_start + per_page]
        page = doc.new_page(width=PW, height=PH)
        T(page, margin, 40, "Տեսանյութի հղման ձևավորման տարբերակներ — Video-link design options",
          FONTS["bold"], 13, DARK)
        T(page, margin, 56, "opt. 1-18 use the long topic title · opt. 19-27 use a short generic word · pick by number",
          FONTS["reg"], 9, GREY)
        y = 78
        row_h = (PH - 96) / per_page
        for name, fn in chunk:
            T(page, margin, y + 10, name, label_font, 9.5, (0.30, 0.30, 0.33))
            fn(page, margin + 4, y + 18, PW - 2 * margin - 8)
            page.draw_line((margin, y + row_h - 6), (PW - margin, y + row_h - 6), color=(0.90, 0.90, 0.92), width=0.4)
            y += row_h

    out = OUT_DIR / "design_gallery.pdf"
    doc.save(out, deflate=True)
    doc.close()
    log.info(f"wrote {out}  ({len(OPTIONS)} options, {doc.page_count if False else (len(OPTIONS)+per_page-1)//per_page} pages)")
    return out


if __name__ == "__main__":
    build()
