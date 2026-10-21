# Decisions - opus_4_8_musoyan_qrs

Newest at the top. See the script docstrings for mechanism-level detail; this file
records choices someone would otherwise have to reverse-engineer.

## 12. Full-set semantic pass by Codex with repo access: 8 retargets, 11 removals; the heading's containing section defines the object
- **Date / status:** 2026-10-21, active; applies rules #9.1/#9.2, partially supersedes
  the 11.3-family call in #10
- **Why:** With its sandbox bypassed (broken Windows exec helper), Codex audited all
  311 shipped links against the lectures' chapter lists - the first full semantic
  pass by a reviewer other than this pipeline's author. Verdict 274 OK / 18 analogue
  / 19 suspect; every suspect was re-verified here against matches.json,
  analysis_index.json and, where decisive, the book's own page text. Outcome:
  (a) 8 retimes/retargets - definition-bearing headings moved to their block starts
  (4.8.1, 13.2.1, 17.2.2), wrong-object landings moved to the exact same-object
  lesson that existed unused (8.1.4 to the multivariable tangent-plane lesson whose
  TITLE equals the heading; 7.5.4 to Bolzano-Cauchy 1, the scalar continuous-image
  theorem; the 11.3 family to Քեռյան's improper-integral by-parts/substitution
  blocks in A4 L16, reopening #10's definite-integral call on strictly better
  evidence - the honest same-object topics score 8.4 in the alternates);
  (b) 11 removals of shipped links with no honest substitute (4.7.6, 5.8.4, 7.5.2,
  12.3.4, 13.2.5, 14.7.2 both lecturers, 14.7.3-Մ, 17.6.1, 18.2.3, 18.3.3);
  (c) 1 suspect REJECTED: 17.1.1's retime to the partition item - the book page
  (v2 source p228) shows the subsection opens by defining the coordinate
  parallelepiped, so the current t=2993 IS the block start.
  The recurring new failure shape: the heading's CONTAINING SECTION defines the
  mathematical object. 14.7 is the Fourier INTEGRAL section, so its 14.7.2/14.7.3
  headings read identically to the Fourier-series topics every earlier audit matched
  them to; ch. 11 is improper integrals, so 11.3 wanted the improper (not definite)
  theorems. One Codex miss was caught in re-verification (14.7.3-Մ, same
  series-on-integral shape as its flagged 14.7.2). Totals: 311 -> 297 configured
  (156 + 141; 11 removals + 3 new same-page dedups), 295 placed (p125's two 14.1
  lines still the only drops), 275 lines on 209 pages, audits clean, 108/108 live.
- **Alternatives rejected:** Substituting the 2nd-order extremum rule for 4.7.6
  (already linked from 4.7.5 on the same page); retiming 18.3.3 to the
  equivalent-condition theorem at t=2112 (plausibly the closed<=>exact theorem, but
  the chapter list never names closedness and 18.3.2 already links it); keeping
  14.7.3-Մ as an analogue (series-vs-integral same-name links were removed in the
  9.x precedent, unlike the kept cross-dimension family).
- **What would change this:** The owner ruling the series-vs-integral family should
  be kept as analogues after all (restores 14.7.2 both, 14.7.3-Մ), or new lectures
  covering Fourier integrals / Stieltjes representation / multiply-connected Green.

## 11. Chapter-page skip is by URL, not by page; footnote lines may stack above the cards
- **Date / status:** 2026-10-21, active; refines the skip clause of #8
- **Why:** A Codex cross-review caught that make_video_links.py skipped EVERY
  section line on a chapter-card page, on the stated assumption that the card is
  derived from exactly that heading's link. Measured: true for only 24 of 32 skips.
  Of the 8 others, 4 were themselves wrong links fixed under rules #9.1/#9.2
  (7.1-Ք and 12.1-Մ were best-title mid-block landings whose honest block start IS
  the card's target; 8.1/8.1.1-Ք pointed at Դաս 12 = higher-order partials, i.e.
  §8.2.1's lesson, when the honest Դաս 8 t=0 again equals the card) and 4 were
  genuinely distinct targets a reader was losing (10.1-Մ on a page where
  Մարտիրոսյան has no card; 14.1 both lecturers -> the Dirichlet-integral lessons;
  17.1.1-Մ -> the subsection block +268s after the card). The skip now compares
  urls: a line is skipped only when some card on the page already carries its
  target. place_video_links.footnote_capacity was fixed so the line stack sits
  ABOVE foot badges, computing capacity from the page's PRE-draw occupied rects -
  a card's label is real inserted text a post-draw scan would count as content
  (contrary to _slot_blocks' "drawn badges are invisible" claim, which holds only
  for vector-only styles; the pre-draw scan was a second-round Codex suggestion
  over intersection-based ink exclusion, which could hide real book text near an
  explicit [x, y] badge). Totals: 311 placeable
  (160 + 151), 309 placed: p125's two 14.1 lines drop loudly because the measured
  text-to-card gap there is 20pt and one line needs 27pt.
- **Alternatives rejected:** Keeping the page-level skip (loses 4 honest links);
  forcing the 14.1 lines onto p125 by shrinking pads (27pt is already tight);
  moving dropped lines to the next page (the link would sit on the wrong page).
- **What would change this:** A redesign of chapter-page layout (e.g. smaller
  cards) that frees the ~7pt p125 is short, or reader feedback that lines above
  the cards look crowded.

## 10. Independent-audit round: exact-lesson substitutions and 16 more removals; cross-dimension analogues kept pending owner ruling
- **Date / status:** 2026-10-21, active; extends #9; the 11.3-family retarget
  superseded by #12 (ch. 11 is improper integrals - the improper-integral theorems
  existed in Քեռյան's A4 L16 and beat the definite-integral ones chosen here)
- **Why:** An independent (unanchored) audit agent re-checked all 324 links against
  rendered book pages and the lectures' chapter lists. Structural layers were clean;
  semantically it found (a) 17 links where an EXACT same-object landing existed
  unused - notably Քեռյան's own 1-D "Ինտեգրալի հատկությունները" (A2 L13) and the
  definite-integral "Փոփոխականի փոխարինում և մասերով ինտեգրում" (A2 L15) lessons,
  the 1-D Cantor theorem (A1 L18), and §2.1.2's true Property 1 at the END of L5
  (the reader-reported link, now on its third and best landing) - all retargeted;
  (b) 16 links whose content was a different theorem with no honest substitute
  (Stone-Weierstrass -> classical Weierstrass, Fourier-specific termwise
  integration/differentiation -> generic uniform-convergence theorems, Քեռյան on
  Stieltjes headings, ch. 16 leftovers, 9.2/9.2.2 Մարտիրոսյան) - all removed.
  Every retarget was asserted against analysis_index.json. Totals: 324 -> 307 links
  (160 + 147), verified end to end (data chain, PDF rects/pairing, 107/107 live).
  Count arithmetic (gap spotted by a Codex cross-review): 324 - 16 removals = 308;
  the 17 retargets are count-neutral except that 8.3.1's new target equals 8.3's on
  the same page, so the same-target dedup absorbed one more line (counter 24 -> 25),
  308 - 1 = 307. (5.8/5.8.1 were already a dedup pair before and after - no change.)
- **Deliberately NOT applied:** the audit's strictest reading of rule #9.2 would
  also strip the systematic cross-dimension analogues (Մարտիրոսյան's multi-D
  twins on vol-1 1-D integral headings 5.2.2-5.4.2, his ՊԿԱԻ versions of the
  functional-series tests 10.2.1/10.2.2, the 1-D improper lemmas on §17.7's multi-D
  headings, and similar). These exist because each lecturer covers the object in
  only one course, were hand-curated deliberately, and removing them would strip
  most dual-lecturer coverage in those stretches. Kept for now.
- **What would change this:** The owner ruling that analogues should also go
  (one more _reject batch), or new lectures covering the removed topics.

## 9. A link targets its topic block's START; same-name topics for a different object get no link
- **Date / status:** 2026-10-21, active
- **Why:** A reader reported §2.1.2 opening at Property 4 instead of the section
  start. A full semantic audit of all 355 shipped links against the lectures' own
  chapter lists followed, and three rules came out of it:
  1. A heading's timestamp is where its topic BLOCK starts in the lecture (walk
     backward from the best title match), not the sub-item whose title matches best.
     26 links retimed on this rule (audit + sweep entries in manual_matches.json).
  2. A topic with the same NAME about a different mathematical object is a wrong
     link: series vs improper-integral criteria (9.1.3, 9.3.2, 9.3.4, 9.6.3
     Մարտիրոսյան), Fourier-Dini vs Abel-Dini (9.2.9), single-variable Fermat vs
     constrained extrema (16.4.2). 7 links removed; where the honest same-object
     topic exists it was substituted instead (9.3.2, 9.6.3 Քեռյան).
  3. Two lines on one page pointing at the identical url are noise: make_video_links
     dedups them, first in book order wins (24 removed, typically a section + its
     first subsection opening on the same page).
  Totals: 355 -> 324 links. Every retime was asserted against analysis_index.json.
- **Alternatives rejected:** Keeping nearest-content same-name links (reader
  feedback shows wrong landings get noticed); deduping by hiding the subsection
  entry at generation (the section may be unmatched - dedup at the end is simpler).
- **What would change this:** New lectures covering the removed topics (re-run
  fetch + reconcile), or reader feedback that a deduped page should carry both labels.

## 8. Section/subsection links are thin footnote lines, capacity-aware, both lecturers
- **Date / status:** 2026-10-20, active; supersedes #2 (owner asked for the full set)
- **Why:** 336 placeable section/subsection matches land on 228 pages (max 4 per
  page), so the big cards would bury the text; the footnote style stacks 14pt lines
  in whatever band stays clear below the page's content (text, formulas, printed
  footnotes, badges). Lines keep book order, label = "heading · lecturer surname"
  (surname never truncated), score decides drops on overfull pages. Measured: all
  336 lines fit, 0 dropped. Headings opening on a chapter-card page are skipped
  (32 matches) because the chapter card is derived from exactly that heading's link.
- **Alternatives rejected:** Cards everywhere (4 cards do not fit on a 420pt page);
  margin chips (collide with the dense scan margins); capping subsections to one
  lecturer (owner chose both lecturers for chapters, same policy kept).
- **What would change this:** Print tests showing the foot lines clash with the
  books' printed footnotes, or reader feedback that 4 lines is too loud.

## 7. A reader-info page is inserted at build time, before the first chapter
- **Date / status:** 2026-09-04, active; wording finalized 2026-10-20 (mentions
  search, bookmarks, cards AND the footnote lines)
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
- **Date / status:** 2026-09-04, superseded by #8 (2026-10-20: owner asked for the
  full placeable set)
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
