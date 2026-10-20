# Decisions - opus_4_8_musoyan_qrs

Newest at the top. See the script docstrings for mechanism-level detail; this file
records choices someone would otherwise have to reverse-engineer.

## 7. A reader-info page is inserted at build time, before the first chapter
- **Date / status:** 2026-09-04, active (wording is DRAFT - owner will finalize)
- **Why:** Owner wants readers told the PDF is Ctrl+F-searchable, has bookmarks and
  video cards, and that extra material lives at mathteam.notion.site (clickable).
  Inserted by build.py in BOTH volumes, so the source PDFs and the bookmarks/links
  JSONs stay in source page numbering; build.py shifts everything past the insertion
  point by one and adds an "Ընթերցողին" bookmark. Text lives in INFO_* constants at
  the top of build.py.
- **Alternatives rejected:** Editing the source PDFs (breaks the JSONs' numbering
  contract and the ability to rebuild from clean sources).
- **What would change this:** Owner deciding vol 2 should not carry the page.
- **Gotcha recorded:** U+2024 (Armenian mid-dot ․) has no glyph in Segoe UI and
  renders as a box; use the Armenian full stop ։ instead.

## 6. A lone chapter badge is centered at the page foot (user decision)
- **Date / status:** 2026-09-04, active; revises the single-card case of #5
- **Why:** Owner: a card sitting bottom-right alone is "asymmetric and not
  aesthetic". Singles are now bottom-center; dual-lecturer pairs stay mirrored
  right + left, best match on the right.
- **Alternatives rejected:** Keeping bottom-right for all (rejected by owner).
- **What would change this:** Print tests, or a style change.

## 5. Chapter badges sit at the page foot, side by side when there are two
- **Date / status:** 2026-09-04, revised same day by #6 for the single-card case
- **Why:** Chapter opening pages are dense up top (chapter heading + immediate text);
  automatic top-right placement fell through to the page foot on *every* chapter page
  anyway, so foot placement was made deliberate and uniform: best match bottom-right,
  the other lecturer's bottom-left. `bottom-*` anchors now scan upward for a clear
  slot so they cannot cover footnotes.
- **Alternatives rejected:** Beside the centered chapter heading - the free side bands
  are ~80pt, a card is ~160pt. Stacked vertically at the foot - does not fit above the
  footnote block on p39. CARD_TEXT_W was reduced 190 -> 135 so two cards fit side by
  side on the 420pt page.
- **What would change this:** A different page trim, or a style smaller than card.

## 4. Card label = "lecturer · course"
- **Date / status:** 2026-09-04, active
- **Why:** The chapter heading printed next to the badge already says what the material
  is; the open question for a reader is who teaches it and in which course. Also keeps
  labels to two wrapped lines.
- **Alternatives rejected:** First-topic text (duplicates the heading), video title
  (too long, lesson numbers are meaningless out of context).
- **What would change this:** Links at section/subsection level, where the matched
  topic differs from the printed heading.

## 3. Labels embed Segoe UI Semibold, subset on save
- **Date / status:** 2026-09-04, active
- **Why:** Base-14 Helvetica cannot encode Armenian (renders as dots, silently).
  Segoe UI Semibold has full Armenian coverage (verified via `Font.has_glyph`), ships
  with Windows, and `doc.subset_fonts()` keeps the cost to KB - the finals actually
  shrank (18.9 -> 18.1 MB) thanks to `garbage=3`.
- **Alternatives rejected:** NotoSansArmenian-Black (only the Black weight is in the
  repo - too heavy for 8.5pt text), Sylfaen (dated look, thin at small sizes).
- **What would change this:** Building on a non-Windows machine - the font path is
  absolute (`C:/Windows/Fonts/seguisb.ttf`).

## 2. Links go on chapter headings only (user decision)
- **Date / status:** 2026-09-04, active
- **Why:** Owner chose low clutter: 20 links across 16 chapters. The 306 placeable
  section/subsection matches stay in `videos/matches.json`, curated and ready, so a
  later pass can widen scope without redoing any matching.
- **Alternatives rejected:** Chapters + sections (~83 links), everything placeable
  (~322) - both supported by the data, declined for now.
- **What would change this:** Owner asking for denser coverage; the only work is in
  `make_video_links.py`.

## 1. Card style, both lecturers (user decision)
- **Date / status:** 2026-09-04, active
- **Why:** Card is the most informative badge (label + visible URL - survives
  printing). Both lecturers kept because the two tracks (Քեռյան applied, Մարտիրոսյան
  theoretical) serve different readers; `reconcile_videos.py` was designed around
  exactly this duality.
- **Alternatives rejected:** chip / footnote / icon styles; single-lecturer preference.
- **What would change this:** Print tests showing the card too dominant on the page.
