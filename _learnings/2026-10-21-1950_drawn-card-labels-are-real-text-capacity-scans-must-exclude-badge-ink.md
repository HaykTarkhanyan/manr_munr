# A drawn card's label is real text - any text-scan-based capacity check must exclude ink inside badge rects

**Symptom** After refining the Musoyan chapter-page skip so honest section lines
could coexist with chapter cards, `build.py` still reported `footnote band holds
0 line(s)` on every card page, even where a probe measured a 28-32pt clear gap
between the text bottom and the card top (enough for one 14.5pt line).

**Cause** `place_video_links._slot_blocks`'s docstring claims "drawn badges are
invisible to the text/image scan, so callers pass them in via `taken`". That is
only true for vector-only styles (icon's triangle, rules, borders). The card
style inserts its LABEL with `page.insert_text`, which is real text:
`page.get_text("blocks")` on a page with cards already drawn returns the card's
own label as a text block at the page foot. `footnote_capacity` took
`band_top = max(b.y1)` over those blocks, so the card's label (y1 about 570 on a
595pt page) pushed `band_top` below the stack base (515) and capacity went to 0.

**Fix / rule** Never compute free space from a text scan taken AFTER you drew on
the page - scan the page's occupied rects BEFORE any badge ink lands and pass
them in (`draw_entries` now captures `pre_blocks` and hands them to
`footnote_capacity`). The first attempt - dropping every scanned block that
intersects a badge rect - worked here but a Codex review flagged it as fragile:
if extraction ever merged book text with a label into one block, or a badge were
placed via an explicit `[x, y]` (which bypasses the BADGE_PAD clearance checks),
real book text would be hidden from the capacity calculation. The pre-draw scan
has no such failure mode. After the fix the measured capacities matched the
probe: final v2 p5 and p229 each hold 1 line above their cards; p125's 20pt gap
honestly holds 0 (27pt needed), and its two 14.1 lines drop with the standard
warning.

Verification: build log went from `vol2: 4 footnote line(s) dropped` to
`2 dropped`; renders of p5/p229 show the line cleanly between text and card.
