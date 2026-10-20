"""Reconcile the Musoyan bookmarks with the channel's Mathematical Analysis videos.

Two lecturers teach the same material to different departments, so a book subsection
can legitimately have two links:
  Կարեն Քեռյան        - Կիրառական վիճակագրություն և տվյալների գիտություն (applied)
  Մհեր Մարտիրոսյան    - Մաթեմատիկայի և մեխանիկայի ֆակուլտետ (theoretical)
Matches are kept separately per lecturer so both can be placed on the same page.

Matching is done against the timestamped topic markers inside each video description,
not against video titles, so a hit yields a moment (youtu.be/<id>?t=<sec>) rather than
a 60-minute lecture. Scoring is Armenian-aware: titles are stemmed of the usual
declension endings and tokens are IDF-weighted, so a shared proper name (Լագրանժ,
Դարբու, Ստիլտես) counts for far more than a shared «ֆունկցիա».

No LLM and no paid API is involved - this is deterministic text matching, and every
score is reproducible from the stored JSON.

Outputs (videos/):
  analysis_index.json  the 116 core videos, parsed: lecturer, track, course, chapters
  matches.json         every book subsection with its best match per lecturer

Usage:
  python opus_4_8_musoyan_qrs/reconcile_videos.py
  python opus_4_8_musoyan_qrs/reconcile_videos.py --min-score 3.5
"""

import argparse
import json
import logging
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOG_DIR = REPO_ROOT / "logs"
VIDEO_DIR = SCRIPT_DIR / "videos"

BOOKS = [("1", "fixed_bookmarks_1.json"), ("2", "fixed_bookmarks_2.json")]

LECTURER_RE = re.compile(r"դասախոս(?:ը)?[՝, ]*(?:պրոֆ․?\s*)?([Ա-Ֆ][ա-ֆ]+ [Ա-Ֆ][ա-ֆ]+)")
SUBJECT_RE = re.compile(r"«([^»]+)»")
LESSON_RE = re.compile(r"Դաս\s+(\d+)")
APPLIED_MARK = "Կիրառական վիճակագրություն"  # only the data-science track says this
CHAPTER_RE = re.compile(r"^[ \t]*(?:(\d{1,2}):)?(\d{1,2}):(\d{2})[ \t]+(\S.*?)[ \t]*$", re.M)

# Endings stripped to compare Armenian words across declensions. Longest first, and
# only applied when at least 4 characters survive, so short stems are left alone.
SUFFIXES = [
    "ություններին", "ությունների", "ությունները", "ություններից", "ություններ",
    "ությունը", "ությամբ", "ության", "ությունն", "ություն",
    "ներին", "ներից", "ներով", "ների", "ները", "ներ",
    "երին", "երից", "երով", "երի", "երը", "եր",
    "ին", "ից", "ով", "ում", "ը", "ի", "ն", "ս", "դ",
]
# Presentation scaffolding, not mathematics - these say nothing about the subject.
# Matched against the STEMMED token: "լեմմա" and "լեմման" must be treated alike, or a
# word is a stopword in one declension and content in another (which silently made
# "Ռիմանի լեմմա" unable to match the heading "Ռիմանի լեմման").
# Mathematical scaffolding (թեորեմ, լեմմա, հետևանք, սահմանում) is deliberately NOT
# listed: it distinguishes "X-ի թեորեմ" from "X-ի սահմանում", and IDF already discounts
# how common it is.
STOP = {"դաս", "թեմա", "մաս", "մասին", "և", "եւ", "ու", "the",
        "օրինակ", "ապացույց", "հիշեցում", "նախորդ", "շարունակություն"}


def setup_logging() -> logging.Logger:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("reconcile_videos")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_DIR / "reconcile_videos.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


log = setup_logging()


def stem(word: str) -> str:
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[:-len(suffix)]
    return word


def tokens(text: str) -> list:
    words = re.findall(r"[\w]+", text.lower(), flags=re.UNICODE)
    stems = [stem(w) for w in words if len(w) > 1 and not w.isdigit()]
    return [s for s in stems if s not in STOP and len(s) > 1]


def parse_chapters(description: str) -> list:
    """[(seconds, topic)] from the 'Թեմաներ' block of a description."""
    out = []
    for hh, mm, ss, topic in CHAPTER_RE.findall(description):
        seconds = int(hh or 0) * 3600 + int(mm) * 60 + int(ss)
        topic = topic.strip(" ․՝-–—")
        if topic and not topic.lower().startswith("http"):
            out.append((seconds, topic))
    return out


def parse_video(v: dict) -> dict:
    desc = v.get("description", "")
    lecturer = LECTURER_RE.search(desc)
    subject = SUBJECT_RE.search(desc)
    lesson = LESSON_RE.search(v["title"])
    name = lecturer.group(1) if lecturer else None
    if name:  # descriptions use the genitive: "Կարեն Քեռյանի" -> "Կարեն Քեռյան"
        name = re.sub(r"ի$", "", name)
    return {
        "video_id": v["video_id"],
        "title": v["title"],
        "url": v["url"],
        "lecturer": name,
        "track": "applied" if APPLIED_MARK in desc else ("theoretical" if name else None),
        "course": subject.group(1) if subject else None,
        "lesson": int(lesson.group(1)) if lesson else None,
        "duration": v.get("duration"),
        "chapters": [{"t": t, "topic": topic} for t, topic in parse_chapters(desc)],
    }


def load_book_entries() -> list:
    """Flatten both volumes into entries carrying their full heading path.

    Chapters are included as level-1 entries. Their titles ("4. Դիֆերենցիալ հաշիվ") are
    too broad to match a single lecture topic, so they are normally filled in afterwards
    from the earliest link inside the chapter - see fill_chapter_links().
    """
    entries = []
    for vol, json_name in BOOKS:
        data = json.loads((SCRIPT_DIR / json_name).read_text(encoding="utf-8"))
        for chap_title, chap in data.items():
            if not isinstance(chap, dict):
                continue
            entries.append({"vol": vol, "chapter": chap_title, "section": None,
                            "subsection": None, "title": chap_title,
                            "page": chap["page"], "level": 1})
            for sec_title, sec in chap["sections"].items():
                entries.append({"vol": vol, "chapter": chap_title, "section": sec_title,
                                "subsection": None, "title": sec_title,
                                "page": sec["page"], "level": 2})
                for sub_title, page in sec["subsections"].items():
                    entries.append({"vol": vol, "chapter": chap_title, "section": sec_title,
                                    "subsection": sub_title, "title": sub_title,
                                    "page": page, "level": 3})
    return entries


def build_idf(documents: list) -> dict:
    n = len(documents)
    seen = Counter()
    for doc in documents:
        seen.update(set(doc))
    return {tok: math.log(n / count) for tok, count in seen.items()}


TITLE_WEIGHT = 0.3  # the lecture title is context, not evidence for a specific moment
# How much a marker's score survives when the book chapter is the lecture's 1st, 2nd,
# 3rd ... closest chapter. A lecture ranges over a chapter or two, so distant chapters
# are heavily discounted but never ruled out.
CHAPTER_RANK_FACTOR = [1.0, 1.0, 0.9, 0.75, 0.6, 0.45, 0.3]
CANDIDATES_PER_LECTURER = 3  # keep runners-up so a human can overrule the top pick
# Hand-audited on a stratified sample of 24 matches (seed 509): every match at 7.0+ was
# correct (12/12), 5-7 was roughly 4/6, and below 5 roughly half. So 7.0 is the line
# between "place it" and "a human should look". Re-audit if the scorer changes.
CONFIDENT_SCORE = 7.0
# A lecturer must own at least this many links inside a chapter before the chapter
# heading carries their name; one stray hit is not "this lecturer teaches this chapter".
MIN_CHAPTER_LINKS = 3
# ...and a real share of it. With 3 links against the other lecturer's 25, the "first
# topic they cover" is something peripheral, and putting their name on the chapter
# heading claims a chapter they do not teach.
MIN_CHAPTER_SHARE = 0.25


def video_id(url: str) -> str:
    return re.search(r"youtu\.be/([\w-]{11})", url).group(1)


def weigh(topic_tokens: list, title_tokens: list) -> dict:
    """token -> weight. Topic words count fully; lecture-title words only hint."""
    out = {t: TITLE_WEIGHT for t in title_tokens}
    for t in topic_tokens:
        out[t] = 1.0
    return out


BOOK_WEIGHT = 0.75  # covering the heading matters more than the topic being terse
IDF: dict = {}  # filled once the corpus is known, in main()


def score(book_tokens: list, cand: dict) -> float:
    """Asymmetric IDF overlap: how much of the heading the topic covers, and vice versa.

    Weighted towards covering the heading (BOOK_WEIGHT), because a one-word heading like
    "Ասիմպտոտներ" is fully answered by "Օրինակ․ arctg(x) ֆունկցիայի ասիմպտոտները" even
    though the topic says much more. A symmetric measure plus a "needs 2 shared tokens"
    rule made every single-word heading unmatchable, which is what hid Ածանցյալ,
    Էքստրեմումներ and Ասիմպտոտներ among the "no candidate" rows.

    Still returns 0 unless the chapter topic itself carries part of the overlap: a match
    made only of lecture-title words cannot say *when* in the lecture the topic appears.
    """
    book = {t: 1.0 for t in book_tokens}
    shared = set(book) & set(cand)
    if not shared or not any(cand[t] == 1.0 for t in shared):
        return 0.0

    def mass(weights: dict, keys) -> float:
        return sum(weights[t] * IDF.get(t, 0.0) for t in keys)

    overlap = sum(min(book[t], cand[t]) * IDF.get(t, 0.0) for t in shared)
    book_cov = overlap / (mass(book, book) or 1.0)
    cand_cov = overlap / (mass(cand, cand) or 1.0)
    return 10.0 * (book_cov ** BOOK_WEIGHT) * (cand_cov ** (1.0 - BOOK_WEIGHT))


def fill_chapter_links(results: list, lessons: dict, no_link: set) -> int:
    """Point each chapter heading at where its material STARTS in the video course.

    A chapter title names a whole subject, so matching it to one lecture topic is
    meaningless - and worse than meaningless when it succeeds: the lexical scorer
    confidently sent "3. Անընդհատ ֆունկցիաներ" to a uniform-continuity topic from §3.2.4.
    So chapter links are always derived, never matched.

    Derived from the chapter's FIRST heading by book page. Ranking by lesson number
    instead looks principled and is not: lesson numbers restart per course, so ch.5
    ("Ինտեգրալ հաշիվ") jumps to Analysis 2 Դաս 3 - the Taylor-remainder lecture, which
    ch.5 touches only in §5.8.4 - instead of Դաս 9 where the integral actually begins.

    A lecturer needs MIN_CHAPTER_LINKS links in the chapter to get one, so a single
    stray hit cannot label a whole chapter with a lecturer who does not teach it.
    """
    placed = ("high", "manual")
    filled = 0
    for chapter_row in [r for r in results if r["level"] == 1]:
        if chapter_row["title"] in no_link:
            # audited and found to have no honest entry point on the channel
            chapter_row["alternates"] = (chapter_row.get("alternates", [])
                                         + chapter_row["matches"])
            chapter_row["matches"] = []
            continue
        if any(m["confidence"] == "manual" for m in chapter_row["matches"]):
            continue  # explicitly curated by hand - leave it alone
        inside = sorted((r for r in results
                         if r["level"] > 1 and r["vol"] == chapter_row["vol"]
                         and r["chapter"] == chapter_row["chapter"]),
                        key=lambda r: r["page"])
        per_lecturer = defaultdict(list)
        for row in inside:
            for m in row["matches"]:
                if m["confidence"] in placed:
                    per_lecturer[m["lecturer"]].append((m, row))

        best = {}
        dominant = max((len(h) for h in per_lecturer.values()), default=0)
        for who, hits in per_lecturer.items():
            if len(hits) < MIN_CHAPTER_LINKS or len(hits) < dominant * MIN_CHAPTER_SHARE:
                continue
            m, row = hits[0]  # rows are in page order, so this is the chapter's opening
            lesson = lessons.get(video_id(m["url"]))
            best[who] = dict(
                m, confidence="chapter",
                source=f"chapter link: where this chapter opens "
                       f"({m['course']}, Դաս {lesson}, from {row['title'][:34]} "
                       f"p.{row['page']}); {len(hits)} links in the chapter",
            )
        if best:
            weak = [m for m in chapter_row["matches"] if m["confidence"] != "manual"]
            chapter_row["alternates"] = chapter_row.get("alternates", []) + weak
            chapter_row["matches"] = sorted(best.values(), key=lambda m: -m["score"])
            filled += 1
    if filled:
        log.info(f"chapter headings: filled {filled} with the first lecture their "
                 f"contents point to")
    return filled


def main() -> None:
    ap = argparse.ArgumentParser(description="Match book subsections to video moments.")
    ap.add_argument("--min-score", type=float, default=3.0,
                    help="drop matches weaker than this (0-10 scale, default 3.0)")
    args = ap.parse_args()

    videos = json.loads((VIDEO_DIR / "all_videos.json").read_text(encoding="utf-8"))
    core = [parse_video(v) for v in videos if v["tier"] == "core"]
    named = [v for v in core if v["lecturer"]]
    by_lecturer = Counter(v["lecturer"] for v in named)
    chapter_total = sum(len(v["chapters"]) for v in named)
    log.info(f"{len(core)} core videos, {len(named)} with a named lecturer, "
             f"{chapter_total} timestamped topics")
    for who, n in by_lecturer.most_common():
        track = next(v["track"] for v in named if v["lecturer"] == who)
        marks = sum(len(v["chapters"]) for v in named if v["lecturer"] == who)
        log.info(f"  {who} ({track}): {n} videos, {marks} topics")

    (VIDEO_DIR / "analysis_index.json").write_text(
        json.dumps(core, ensure_ascii=False, indent=2), encoding="utf-8")

    entries = load_book_entries()
    log.info(f"{len(entries)} book headings (sections + subsections) across both volumes")

    # Candidates: one per timestamped topic, its text enriched by the lecture title so a
    # topic like "Ապացույց" still carries the lecture's subject matter.
    candidates = []
    for v in named:
        title_tokens = tokens(v["title"].split("|")[1] if "|" in v["title"] else v["title"])
        for ch in v["chapters"]:
            candidates.append({
                "video": v, "t": ch["t"], "topic": ch["topic"],
                "tokens": weigh(tokens(ch["topic"]), title_tokens),
            })
    idf = build_idf([list(c["tokens"]) for c in candidates]
                    + [tokens(e["title"]) for e in entries])
    IDF.clear()
    IDF.update(idf)
    log.info(f"vocabulary {len(idf)} stems")

    # Phrase overlap alone confuses different objects that share vocabulary: "Դարբուի
    # վերին և ստորին ինտեգրալներ" scores well against "Հաջորդականության վերին և ստորին
    # սահմանները" even though one is about integrals and the other about sequences. So
    # first place each LECTURE against the book's chapters, and only let its markers
    # match subsections in the handful of chapters that lecture is actually about.
    def vector(token_lists: list) -> dict:
        vec = defaultdict(float)
        for toks in token_lists:
            for t in toks:
                vec[t] += idf.get(t, 0.0)
        return vec

    def cosine(a: dict, b: dict) -> float:
        shared = set(a) & set(b)
        if not shared:
            return 0.0
        dot = sum(a[t] * b[t] for t in shared)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    chapter_titles = defaultdict(list)
    for e in entries:
        chapter_titles[(e["vol"], e["chapter"])].append(tokens(e["title"]))
    chapter_vecs = {k: vector(v) for k, v in chapter_titles.items()}

    video_topics = defaultdict(list)
    for c in candidates:
        video_topics[c["video"]["video_id"]].append([t for t, w in c["tokens"].items()
                                                     if w == 1.0])
    # A soft penalty, not a gate. A hard cut-off drops true positives: Cauchy's
    # convergence principle is vol 1 ch.2 in the book but recurs in Martirosyan's
    # Analysis 3, and that pairing is exactly the dual-lecturer case worth keeping.
    scope = {}
    for v in named:
        vec = vector(video_topics.get(v["video_id"], []) + [tokens(v["title"])])
        ranked_ch = sorted(chapter_vecs, key=lambda k: -cosine(vec, chapter_vecs[k]))
        scope[v["video_id"]] = {ch: CHAPTER_RANK_FACTOR[min(i, len(CHAPTER_RANK_FACTOR) - 1)]
                                for i, ch in enumerate(ranked_ch)}
    log.info("lectures scored against book chapters; off-topic chapters are penalised, "
             f"not excluded (factors {CHAPTER_RANK_FACTOR})")

    title_by_url = {v["url"]: v["title"] for v in core}
    manual_path = SCRIPT_DIR / "manual_matches.json"
    manual = json.loads(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else {}
    curated = sum(len(v) for k, v in manual.items() if not k.startswith("_"))
    log.info(f"{curated} hand-verified match(es) loaded from {manual_path.name}")

    # A key that matches no heading is a typo that silently does nothing - exactly the
    # kind of quiet failure that makes hand-curation untrustworthy. Fail loudly.
    known = {e["title"] for e in entries}
    stray = sorted({k for k in manual if not k.startswith("_")} - known)
    for section in ("_approve", "_reject"):
        stray += sorted(set(manual.get(section, {})) - known)
    if stray:
        for key in stray:
            log.error(f"manual_matches.json key matches no book heading: {key!r}")
        raise ValueError(
            f"{len(stray)} key(s) in manual_matches.json match no heading - fix the "
            f"spelling (they are silently ignored otherwise)"
        )

    matched = 0
    both = 0
    manual_used = 0
    results = []
    for entry in entries:
        btokens = tokens(entry["title"])
        per_video = {}
        for cand in candidates:
            video = cand["video"]
            factor = scope[video["video_id"]][(entry["vol"], entry["chapter"])]
            s = score(btokens, cand["tokens"]) * factor
            if s < args.min_score:
                continue
            hit = {
                "score": round(s, 2),
                "confidence": "high" if s >= CONFIDENT_SCORE else "review",
                "lecturer": video["lecturer"],
                "track": video["track"],
                "course": video["course"],
                "video_title": video["title"],
                "topic": cand["topic"],
                "t": cand["t"],
                "url": f"{video['url']}?t={cand['t']}",
            }
            # one entry per lecture: 3 markers from the same video is not 3 options
            if s > per_video.get(video["video_id"], {}).get("score", 0):
                per_video[video["video_id"]] = hit

        by_lecturer = defaultdict(list)
        for hit in per_video.values():
            by_lecturer[hit["lecturer"]].append(hit)
        picks, alternates = [], []
        for who, hits in by_lecturer.items():
            hits.sort(key=lambda m: -m["score"])
            picks.append(hits[0])
            alternates.extend(hits[1:CANDIDATES_PER_LECTURER])

        # Hand-verified entries override the scorer for that heading + lecturer. Armenian
        # derivational morphology (խմբավորումը/խմբավորված, պարամետրացված/պարամետրացում)
        # is beyond suffix-stripping, so some true matches can only be found by reading.
        overrides = manual.get(entry["title"], [])
        rejected = manual.get("_reject", {}).get(entry["title"], [])
        approved = manual.get("_approve", {}).get(entry["title"], [])
        picks = [p for p in picks if p["lecturer"] not in rejected
                 and p["lecturer"] not in {o["lecturer"] for o in overrides}]
        for p in picks:  # a human read this review-tier match and confirmed it
            if p["lecturer"] in approved and p["confidence"] != "high":
                p["confidence"] = "manual"
                p["source"] = "manual: reviewed and confirmed"
                manual_used += 1
        for o in overrides:
            picks.append({
                "score": 10.0, "confidence": "manual", "lecturer": o["lecturer"],
                "track": next((v["track"] for v in named if v["lecturer"] == o["lecturer"]),
                              None),
                "course": o.get("course"),
                "video_title": title_by_url.get(o["url"].split("?")[0], o.get("topic")),
                "topic": o["topic"], "t": o["t"], "url": o["url"],
                "source": o.get("source", "manual"),
            })
            manual_used += 1

        record = dict(entry)
        record["matches"] = sorted(picks, key=lambda m: -m["score"])
        record["alternates"] = sorted(alternates, key=lambda m: -m["score"])
        results.append(record)
        if record["matches"]:
            matched += 1
        if len(record["matches"]) > 1:
            both += 1

    fill_chapter_links(results, {v["video_id"]: v["lesson"] for v in core if v["lesson"]},
                       set(manual.get("_no_link", [])))

    (VIDEO_DIR / "matches.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    per_vol = defaultdict(lambda: [0, 0])
    for r in results:
        per_vol[r["vol"]][1] += 1
        if r["matches"]:
            per_vol[r["vol"]][0] += 1
    log.info(f"matched {matched}/{len(entries)} headings at min-score {args.min_score}; "
             f"{both} have both lecturers")
    for vol in sorted(per_vol):
        hit, total = per_vol[vol]
        log.info(f"  vol {vol}: {hit}/{total} headings matched")

    def placeable(m: dict) -> bool:
        return m["confidence"] in ("high", "manual", "chapter")

    confident = [r for r in results if any(placeable(m) for m in r["matches"])]
    dual_conf = [r for r in confident
                 if len({m["lecturer"] for m in r["matches"] if placeable(m)}) > 1]
    # a row is "review" only if it has candidates but none good enough to place; chapter
    # rows whose weak hits were replaced by a chapter link are placeable, not review
    to_review = [r for r in results
                 if r["matches"] and not any(placeable(m) for m in r["matches"])]
    log.info(f"confidence split at {CONFIDENT_SCORE}: {len(confident)} headings are "
             f"placeable ({len(dual_conf)} with both lecturers); "
             f"{len(to_review)} need review; {manual_used} hand-verified")
    log.info(f"wrote {VIDEO_DIR.relative_to(REPO_ROOT)}/matches.json")


if __name__ == "__main__":
    main()
