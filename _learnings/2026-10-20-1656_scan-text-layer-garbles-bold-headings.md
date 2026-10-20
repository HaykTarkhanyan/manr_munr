# The Musoyan scans' text layer garbles bold headings - word-match audits false-positive

**Symptom** - auditing bookmark targets by checking whether the title's words appear
in the target page's extracted text flagged 8 of 515 bookmarks as off-by-one. 7 were
wrong flags: rendering the pages showed the printed heading sitting right there.

**Cause** - the book PDFs are scans with a text layer that garbles the bold
underlined heading lines specifically (body text extracts fine). So the heading's
own words are missing from its page's text, while the NEXT page naturally repeats
them in body prose - exactly the signature of an off-by-one.

**Consequences**:

- Text-layer word matching alone cannot confirm a bookmark on these scans; every
  flag needs a visual render check before being called an error.
- Casefold before matching: section headings are printed in ALL CAPS Armenian
  ("ԱԾԱՆՑՅԱԼ" vs bookmark "Ածանցյալ"), which zeroed a naive case-sensitive pass.
- The bookmark titles use invented decimal numbering ("7.4.2.") that never appears
  in print (the book numbers "§2" and bold "4." within sections) - don't match on
  numbers.
- The one REAL error the audit found in 515 bookmarks: vol 2 "10.4. Աստիճանային
  շարքեր" pointed one page late (heading at the foot of the previous page). Fixed
  2026-10-20 in fixed_bookmarks_2.json (26 -> 25). Base rate worth remembering:
  the hand-curated bookmark data was 514/515 correct.
