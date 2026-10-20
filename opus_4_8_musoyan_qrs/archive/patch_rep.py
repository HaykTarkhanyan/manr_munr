from pathlib import Path
p = Path("build_match_report.py")
s = p.read_text(encoding="utf-8")
s = s.replace('PLACEABLE = ("high", "manual")', 'PLACEABLE = ("high", "manual", "chapter")')
s = s.replace('cls = m["confidence"] if m["confidence"] in ("high", "manual") else "review"',
              'cls = m["confidence"] if m["confidence"] in ("high", "manual", "chapter") else "review"')
s = s.replace(' .m.manual{{border-left-color:{RED};background:#fff6f6}}',
              ' .m.manual{{border-left-color:{RED};background:#fff6f6}}\n'
              ' .m.chapter{{border-left-color:#6b6b70;background:#f7f7f8}}')
s = s.replace('Red = hand-verified.', 'Red = hand-verified. Grey = chapter link (first lecture of that chapter).')
s = s.replace("key = f'v{r[\"vol\"]} \u00b7 {r[\"chapter\"]}'", "key = f'v{r[\"vol\"]} \u00b7 {r[\"chapter\"]}'")
p.write_text(s, encoding="utf-8")
print("patched report")
