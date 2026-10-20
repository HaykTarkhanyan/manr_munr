"""Build an interactive HTML review of the book-heading <-> video-moment matches.

Derived entirely from videos/matches.json, so re-running this never re-runs the
reconciliation. Single self-contained file, no CDN.

Usage:
  python opus_4_8_musoyan_qrs/build_match_report.py
"""

import html
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOG_DIR = REPO_ROOT / "logs"
VIDEO_DIR = SCRIPT_DIR / "videos"
OUT = VIDEO_DIR / "match_report.html"

RED, BLUE, ORANGE = "#D90012", "#0033A0", "#F2A800"


def setup_logging() -> logging.Logger:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("build_match_report")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_DIR / "build_match_report.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


log = setup_logging()


def hms(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def match_html(m: dict) -> str:
    cls = m["confidence"] if m["confidence"] in ("high", "manual", "chapter") else "review"
    return (
        f'<div class="m {cls}">'
        f'<span class="score">{m["score"]:.1f}</span>'
        f'<span class="who">{html.escape(m["lecturer"])}</span>'
        f'<span class="course">{html.escape(m["course"] or "")}</span>'
        f'<a href="{html.escape(m["url"])}" target="_blank">{html.escape(m["topic"][:70])}'
        f' <span class="t">@{hms(m["t"])}</span></a>'
        f'</div>'
    )


def build() -> Path:
    rows = json.loads((VIDEO_DIR / "matches.json").read_text(encoding="utf-8"))

    total = len(rows)
    with_any = [r for r in rows if r["matches"]]
    PLACEABLE = ("high", "manual", "chapter")
    high = [r for r in rows if any(m["confidence"] in PLACEABLE for m in r["matches"])]
    dual_high = [r for r in rows
                 if len([m for m in r["matches"] if m["confidence"] in PLACEABLE]) > 1]
    review_only = [r for r in with_any if r not in high]

    per_chapter = defaultdict(lambda: {"total": 0, "high": 0, "review": 0})
    for r in rows:
        key = f'v{r["vol"]} · {r["chapter"]}'
        per_chapter[key]["total"] += 1
        if any(m["confidence"] in PLACEABLE for m in r["matches"]):
            per_chapter[key]["high"] += 1
        elif r["matches"]:
            per_chapter[key]["review"] += 1

    bars = []
    widest = max(c["total"] for c in per_chapter.values())
    for name, c in per_chapter.items():
        hi_pct, rv_pct = 100 * c["high"] / widest, 100 * c["review"] / widest
        bars.append(
            f'<div class="barrow"><div class="barlabel">{html.escape(name)}</div>'
            f'<div class="bartrack">'
            f'<div class="seg hi" style="width:{hi_pct:.1f}%"></div>'
            f'<div class="seg rv" style="width:{rv_pct:.1f}%"></div>'
            f'<span class="barval">{c["high"]} confident · {c["review"]} review '
            f'· {c["total"]} headings</span>'
            f'</div></div>'
        )

    trs = []
    for r in rows:
        state = ("high" if any(m["confidence"] in PLACEABLE for m in r["matches"])
                 else ("review" if r["matches"] else "none"))
        names = sorted({m["lecturer"] for m in r["matches"]})
        who = " ".join(names) + (" both" if len(names) > 1 else "")
        alt_list = r.get("alternates", [])
        alts = "".join(match_html(a) for a in alt_list)
        alt_block = (f"<details><summary>{len(alt_list)} alternate(s)</summary>{alts}</details>"
                     if alt_list else "")
        trs.append(
            f'<tr data-vol="{r["vol"]}" data-state="{state}" data-who="{html.escape(who)}" '
            f'data-text="{html.escape((r["title"] + " " + r["chapter"]).lower())}">'
            f'<td class="pg">{r["page"]}</td>'
            f'<td class="head"><div class="crumb">v{r["vol"]} · {html.escape(r["chapter"])}'
            f'{" · " + html.escape(r["section"]) if r["subsection"] else ""}</div>'
            f'<div class="title">{html.escape(r["title"])}</div></td>'
            f'<td class="mm">{"".join(match_html(m) for m in r["matches"]) or "<i>no candidate</i>"}'
            f'{alt_block}</td></tr>'
        )

    doc = f"""<meta charset="utf-8"><title>Musoyan ↔ video matches</title>
<style>
 body{{font:14px/1.5 "Segoe UI",system-ui,sans-serif;margin:0;padding:24px;color:#1a1a1a;background:#fafafa}}
 h1{{font-size:20px;margin:0 0 4px}} h2{{font-size:15px;margin:28px 0 10px}}
 .sub{{color:#666;margin-bottom:18px}}
 .cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px}}
 .card{{background:#fff;border:1px solid #e3e3e6;border-radius:8px;padding:12px 16px;min-width:150px}}
 .card b{{display:block;font-size:24px;line-height:1.1}}
 .card span{{color:#666;font-size:12px}}
 .barrow{{display:flex;align-items:center;gap:10px;margin:3px 0}}
 .barlabel{{width:330px;text-align:right;font-size:12px;color:#333;overflow:hidden;
   text-overflow:ellipsis;white-space:nowrap;flex:none}}
 .bartrack{{position:relative;flex:1;height:20px;background:#ececed;border-radius:3px;
   display:flex;overflow:visible}}
 .seg{{height:100%}} .seg.hi{{background:{BLUE}}} .seg.rv{{background:{ORANGE}}}
 .barval{{position:absolute;left:calc(100% + 8px);top:0;line-height:20px;font-size:11px;
   color:#555;white-space:nowrap}}
 .bars{{padding-right:190px}}
 .controls{{margin:18px 0 10px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
 select,input{{font:13px inherit;padding:6px 8px;border:1px solid #ccc;border-radius:6px}}
 table{{width:100%;border-collapse:collapse;background:#fff;table-layout:fixed}}
 th,td{{border-bottom:1px solid #ececf0;padding:8px 10px;vertical-align:top;text-align:left}}
 th{{background:#f2f2f4;font-size:12px;text-transform:uppercase;letter-spacing:.03em}}
 .pg{{font-variant-numeric:tabular-nums;color:#666}}
 .crumb{{font-size:11px;color:#888}} .title{{font-weight:600}}
 .m{{margin:2px 0;padding:3px 6px;border-radius:5px;border-left:3px solid #ccc;background:#fbfbfc}}
 .m.high{{border-left-color:{BLUE}}} .m.review{{border-left-color:{ORANGE}}}
 .m.manual{{border-left-color:{RED};background:#fff6f6}}
 .m.chapter{{border-left-color:#6b6b70;background:#f7f7f8}}
 .score{{display:inline-block;min-width:30px;font-weight:700;font-variant-numeric:tabular-nums}}
 .who{{color:{RED};margin-right:6px}} .course{{color:#888;font-size:11px;margin-right:6px}}
 .t{{color:#888;font-size:11px}} a{{color:#0b57b5}}
 details summary{{cursor:pointer;color:#777;font-size:12px;margin-top:4px}}
 i{{color:#aaa}}
</style>
<h1>Musoyan ↔ Համալսարանական մաթեմատիկա — match review</h1>
<div class="sub">Each book heading matched to a <b>timestamped moment</b> in a lecture.
Blue = score ≥ 7.0 (hand-audited as reliable). Orange = needs your judgement. Red = hand-verified. Grey = chapter link (first lecture of that chapter).</div>
<div class="cards">
 <div class="card"><b>{total}</b><span>book headings</span></div>
 <div class="card"><b>{len(high)}</b><span>confident match</span></div>
 <div class="card"><b>{len(dual_high)}</b><span>both lecturers, confident</span></div>
 <div class="card"><b>{len(review_only)}</b><span>need review</span></div>
 <div class="card"><b>{total - len(with_any)}</b><span>no candidate</span></div>
</div>
<h2>Coverage by chapter</h2>
<div class="bars">{"".join(bars)}</div>
<h2>Headings</h2>
<div class="controls">
 <select id="fvol"><option value="">both volumes</option><option value="1">vol 1</option>
  <option value="2">vol 2</option></select>
 <select id="fstate"><option value="">any status</option><option value="high">confident</option>
  <option value="review">needs review</option><option value="none">no candidate</option></select>
 <select id="fwho"><option value="">any lecturer</option>
  <option value="Կարեն Քեռյան">includes Քեռյան</option>
  <option value="Մհեր Մարտիրոսյան">includes Մարտիրոսյան</option>
  <option value="both">both lecturers</option></select>
 <input id="fq" placeholder="search heading…" size="30">
 <span id="count" style="color:#666"></span>
</div>
<table><colgroup><col style="width:56px"><col style="width:38%"><col></colgroup>
<thead><tr><th>page</th><th>book heading</th><th>video moment(s)</th></tr></thead>
<tbody id="tb">{"".join(trs)}</tbody></table>
<script>
const rows=[...document.querySelectorAll('#tb tr')];
const els=['fvol','fstate','fwho','fq'].map(i=>document.getElementById(i));
function apply(){{
  const [v,s,w,q]=els.map(e=>e.value.toLowerCase());
  let n=0;
  for(const r of rows){{
    const ok=(!v||r.dataset.vol===v)&&(!s||r.dataset.state===s)
      &&(!w||r.dataset.who.toLowerCase().includes(w))
      &&(!q||r.dataset.text.includes(q));
    r.style.display=ok?'':'none'; if(ok)n++;
  }}
  document.getElementById('count').textContent=n+' shown';
}}
els.forEach(e=>e.addEventListener('input',apply));apply();
</script>"""

    VIDEO_DIR.mkdir(exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    log.info(f"{total} headings | {len(high)} confident | {len(dual_high)} dual-lecturer "
             f"| {len(review_only)} to review | {total - len(with_any)} unmatched")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")
    return OUT


if __name__ == "__main__":
    build()
