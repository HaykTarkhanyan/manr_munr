# A lecture topic with the same NAME about a different mathematical object is a wrong link, and title-based scoring loves them

**Symptom** The full audit of the Musoyan link set (all 355 shipped links read
against their lectures' chapter lists) found 7 links whose topic title matched the
book heading almost verbatim while the content was about a different object:

- "Կոշիի զուգամիտության սկզբունքը", "Բացարձակ և պայմանական զուգամիտություն",
  "Աբել և Դիրիխլեի հայտանիշները" for SERIES headings linked to the
  IMPROPER-INTEGRAL versions of the same-named theorems (9.1.3, 9.3.2, 9.3.4) and
  the infinite-products section to the integral one (9.6.3);
- "Աբել–Դինիի թեորեմները" (positive series) linked to the FOURIER-series Dini
  criterion - an unrelated theorem that happens to share Dini's name (9.2.9, both
  lecturers, and these had even been hand-approved during curation);
- "Անհրաժեշտ պայմաններ" under §16.4 (CONSTRAINED extrema) linked to single-variable
  Fermat (16.4.2).

**Cause** The scorer works on tokenized topic titles. Armenian course material
reuses the exact same theorem names across sequences / series / functions /
integrals / products, so the title similarity is near-perfect precisely when the
object is wrong. Human review passes also missed several because the title LOOKS
right; only checking which lesson the video belongs to exposes the mismatch.

**Consequences / rule** When auditing matches, always read the VIDEO's course and
lesson topic, not just the matched title. If the same-object version exists
elsewhere on the channel, substitute it (9.3.2 and 9.6.3 had exact series/product
topics 20 minutes away in the lecturer's own lessons). If it does not, remove the
link - no link beats a wrong link (DECISIONS.md #9; same policy as chapters
15/16/19). A useful heuristic for finding candidates: a heading in a series/products
chapter whose matched video title mentions ինտեգրալ (or vice versa).
