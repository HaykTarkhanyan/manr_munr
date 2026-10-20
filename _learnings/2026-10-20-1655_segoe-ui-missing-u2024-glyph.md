# Segoe UI has full Armenian letters but no U+2024 (Armenian mid-dot)

**Symptom** - an info page drawn with embedded Segoe UI rendered "որոնելի է․ սեղմեք"
with a missing-glyph box where the mid-dot ․ (U+2024, ONE DOT LEADER) should be.
Every Armenian LETTER was fine, so the font looked fully covered.

**Cause** - glyph coverage is per codepoint, not per script. Measured 2026-09:

```
U+2024 one dot leader -> 0        # no glyph
U+0589 arm full stop  -> 3247     # fine
arm comma (՝)         -> 3205     # fine
```

**Fix** - use ։ (U+0589) and restructure the sentence, or pick another punctuation
mark the font has. Check any "unusual" punctuation codepoint with
`fitz.Font(fontfile=p).has_glyph(ord(ch))` before shipping text in an embedded font -
letters passing does not mean punctuation passes.
