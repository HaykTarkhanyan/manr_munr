# PyMuPDF base-14 fonts render Armenian as dots, with no error

**Symptom** - `page.insert_text(..., fontname="helv")` with Armenian text produces
a row of dots in the PDF. No exception, no warning; you only notice by looking at
the rendered page.

**Cause** - the base-14 PDF fonts (helv, hebo, etc.) are Latin-1 only. PyMuPDF
substitutes a placeholder glyph for every character outside that range instead of
raising.

**Consequences / fix** (opus_4_8_musoyan_qrs, 2026-09):

- Any non-Latin label must use an embedded font:
  `page.insert_text(..., fontname="SegoeUISemibold", fontfile="C:/Windows/Fonts/seguisb.ttf")`.
- `fitz.get_text_length()` only knows base-14 fonts; measure embedded faces with
  `fitz.Font(fontfile=...).text_length(text, fontsize=...)`.
- Size cost: a full save plus `doc.subset_fonts()` (needs `fonttools`) keeps the
  embedded faces to KB. Measured on musoyan_1.pdf: two Segoe UI faces (~1 MB each
  on disk) added, final grew 18.87 MB -> 19.04 MB total including all cards and an
  extra page. An INCREMENTAL save embeds the whole face instead (~+1 MB per font).
- Verify coverage before trusting any font: `fitz.Font(fontfile=p).has_glyph(ord('Ա'))`.
