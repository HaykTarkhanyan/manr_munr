"""Fetch every video (title + full description) from the Համալսարանական մաթեմատիկա channel.

Read-only YouTube Data API v3, authenticated with YOUTUBE_DATA_API_KEY from the repo
root .env (copied from timestamp_generation_agentic; .env is gitignored).

Why the whole channel and not just the analysis playlists: the quota cost is trivial
(~40 units of the 10,000/day free allowance, no dollar cost), and the Musoyan chapters
reach into functional analysis and metric spaces, while the two grab-bag playlists
("Բաց դասեր", "Կարճ տեսանյութեր") mix analysis lessons in with everything else. So
every playlist is fetched and tagged with a relevance TIER instead, and the matching
step filters on that rather than on a guess made here.

Descriptions come from videos.list, not playlistItems - playlistItems can serve a
stale or truncated description, and the description text is the whole point here.

Output (videos/):
  channel.json      channel metadata + every playlist with its tier and video count
  playlists/*.json  one file per playlist, with its videos in playlist order
  all_videos.json   flat de-duplicated index of every video, for matching

Usage:
  python opus_4_8_musoyan_qrs/fetch_videos.py
  python opus_4_8_musoyan_qrs/fetch_videos.py --tier core adjacent
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOG_DIR = REPO_ROOT / "logs"
OUT_DIR = SCRIPT_DIR / "videos"

API = "https://www.googleapis.com/youtube/v3"
CHANNEL_ID = "UCMFONp28jEDHXDBWJyRVYcA"  # Համալսարանական մաթեմատիկա
# Swapping UC->UU gives the channel's uploads playlist. Fetching it is not optional:
# Martirosyan's whole "Մաթեմատիկական անալիզ 4" course (Դաս 1-12, covering vol 2 ch.12-13)
# sits in no playlist at all and is invisible if you only walk playlists.
UPLOADS_PLAYLIST = f"UU{CHANNEL_ID[2:]}"
SUBJECT_RE = re.compile(r"«([^»]+)»")  # the course name inside the description

# Relevance to Musoyan's two Mathematical Analysis volumes, by playlist title.
# core     - the analysis course itself
# adjacent - overlaps specific chapters (ch.15 continuous-function spaces / metric
#            spaces) or is a mixed bag known to contain analysis lessons
# other    - different subject; fetched for completeness, not expected to match
CORE_PATTERNS = [r"^Մաթեմատիկական անալիզ"]
ADJACENT_PATTERNS = [
    r"^Ֆունկցիոնալ անալիզ",
    r"^Տոպոլոգիա և մետրիկական տարածություններ",
    r"^Կարճ տեսանյութեր",
]
# "Բաց դասեր" is deliberately NOT adjacent: those 235 items are Armenian Public TV
# school broadcasts (set-theory basics, GCD/LCM, linear equations) titled only by
# air date. Wrong level for a university analysis text, and untitled by topic.


def setup_logging() -> logging.Logger:
    for stream in (sys.stdout, sys.stderr):  # Armenian titles vs the cp1252 console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("fetch_videos")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_DIR / "fetch_videos.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


log = setup_logging()
QUOTA_UNITS = 0


def api_key() -> str:
    load_dotenv(REPO_ROOT / ".env")
    key = os.environ.get("YOUTUBE_DATA_API_KEY")
    if not key:
        raise RuntimeError(f"YOUTUBE_DATA_API_KEY missing from {REPO_ROOT / '.env'}")
    return key


KEY = api_key()


def get(endpoint: str, **params) -> dict:
    """One API call. Raises on any non-200 so a quota or key problem stops the run."""
    global QUOTA_UNITS
    params["key"] = KEY
    resp = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
    QUOTA_UNITS += 1
    if resp.status_code != 200:
        raise RuntimeError(f"{endpoint} returned {resp.status_code}: {resp.text[:400]}")
    return resp.json()


def paged(endpoint: str, **params):
    """Yield every item across all pages."""
    token = None
    while True:
        page = get(endpoint, **params, **({"pageToken": token} if token else {}))
        yield from page["items"]
        token = page.get("nextPageToken")
        if not token:
            return
        time.sleep(0.05)


def tier_for(title: str) -> str:
    if any(re.search(p, title) for p in CORE_PATTERNS):
        return "core"
    if any(re.search(p, title) for p in ADJACENT_PATTERNS):
        return "adjacent"
    return "other"


def tier_for_video(video: dict) -> str:
    """Tier an un-playlisted video from the course name quoted in its description."""
    subject = SUBJECT_RE.search(video.get("description", ""))
    return tier_for(subject.group(1)) if subject else "other"


def slugify(title: str, playlist_id: str) -> str:
    """Filename-safe stem; keeps the playlist id so files stay unambiguous."""
    stem = re.sub(r"[^\w԰-֏]+", "_", title, flags=re.UNICODE).strip("_")
    return f"{stem[:60]}_{playlist_id}"


def fetch_channel() -> dict:
    items = get("channels", part="snippet,statistics", id=CHANNEL_ID)["items"]
    if not items:
        raise RuntimeError(f"channel {CHANNEL_ID} not found")
    c = items[0]
    return {
        "channel_id": c["id"],
        "title": c["snippet"]["title"],
        "description": c["snippet"].get("description", ""),
        "video_count": int(c["statistics"].get("videoCount", 0)),
        "url": f"https://www.youtube.com/channel/{c['id']}",
    }


def fetch_playlists() -> list:
    out = []
    for p in paged("playlists", part="snippet,contentDetails", channelId=CHANNEL_ID,
                   maxResults=50):
        title = p["snippet"]["title"]
        out.append({
            "playlist_id": p["id"],
            "title": title,
            "description": p["snippet"].get("description", ""),
            "item_count": p["contentDetails"]["itemCount"],
            "tier": tier_for(title),
            "url": f"https://www.youtube.com/playlist?list={p['id']}",
        })
    return sorted(out, key=lambda x: (x["tier"] != "core", x["tier"] != "adjacent",
                                      x["title"]))


def fetch_video_details(video_ids: list) -> dict:
    """videos.list in batches of 50 -> {video_id: record}. Full, current descriptions."""
    details = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        for v in get("videos", part="snippet,contentDetails,statistics",
                     id=",".join(batch), maxResults=50)["items"]:
            sn, cd, st = v["snippet"], v["contentDetails"], v.get("statistics", {})
            details[v["id"]] = {
                "video_id": v["id"],
                "title": sn["title"],
                "description": sn.get("description", ""),
                "channel_title": sn.get("channelTitle"),  # playlists may hold guest videos
                "published_at": sn.get("publishedAt"),
                "duration": cd.get("duration"),
                "view_count": int(st["viewCount"]) if "viewCount" in st else None,
                "url": f"https://youtu.be/{v['id']}",
            }
        time.sleep(0.05)
    return details


def fetch_playlist_videos(playlist: dict) -> list:
    ids, positions = [], {}
    for item in paged("playlistItems", part="contentDetails,snippet",
                      playlistId=playlist["playlist_id"], maxResults=50):
        vid = item["contentDetails"]["videoId"]
        ids.append(vid)
        positions[vid] = item["snippet"]["position"]

    details = fetch_video_details(ids)
    missing = [v for v in ids if v not in details]
    if missing:  # private / deleted entries are normal, but never silently
        log.warning(f"  {playlist['title']}: {len(missing)} unavailable "
                    f"(private or deleted): {missing[:5]}")

    videos = []
    for vid in ids:
        if vid not in details:
            continue
        rec = dict(details[vid])
        rec["position"] = positions[vid]
        videos.append(rec)
    return sorted(videos, key=lambda v: v["position"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch channel videos + descriptions.")
    ap.add_argument("--tier", nargs="+", choices=["core", "adjacent", "other"],
                    default=["core", "adjacent", "other"],
                    help="which playlist tiers to fetch (default: all)")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "playlists").mkdir(exist_ok=True)

    channel = fetch_channel()
    log.info(f"channel: {channel['title']} ({channel['video_count']} videos)")

    playlists = fetch_playlists()
    counts = {t: sum(1 for p in playlists if p["tier"] == t) for t in
              ("core", "adjacent", "other")}
    log.info(f"{len(playlists)} playlists: {counts['core']} core, "
             f"{counts['adjacent']} adjacent, {counts['other']} other")

    selected = [p for p in playlists if p["tier"] in args.tier]
    all_videos, seen = [], {}
    for p in selected:
        videos = fetch_playlist_videos(p)
        p["fetched_count"] = len(videos)
        path = OUT_DIR / "playlists" / f"{slugify(p['title'], p['playlist_id'])}.json"
        path.write_text(json.dumps({"playlist": p, "videos": videos},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
        log.info(f"  [{p['tier']:>8}] {len(videos):>3} videos  {p['title']}")
        for v in videos:
            if v["video_id"] in seen:  # a video can sit in several playlists
                seen[v["video_id"]]["playlists"].append(p["title"])
                continue
            rec = dict(v)
            rec.pop("position", None)
            rec["playlists"] = [p["title"]]
            rec["tier"] = p["tier"]
            seen[v["video_id"]] = rec
            all_videos.append(rec)

    # Sweep the uploads feed so videos in no playlist are still captured.
    upload_ids = [i["contentDetails"]["videoId"] for i in
                  paged("playlistItems", part="contentDetails",
                        playlistId=UPLOADS_PLAYLIST, maxResults=50)]
    orphan_ids = [v for v in upload_ids if v not in seen]
    if orphan_ids:
        orphans = fetch_video_details(orphan_ids)
        kept = 0
        for vid in orphan_ids:
            if vid not in orphans:
                continue
            rec = dict(orphans[vid])
            rec["playlists"] = []
            rec["tier"] = tier_for_video(rec)
            seen[vid] = rec
            all_videos.append(rec)
            kept += 1
        by_tier = {t: sum(1 for v in all_videos if not v["playlists"] and v["tier"] == t)
                   for t in ("core", "adjacent", "other")}
        log.info(f"uploads sweep: {kept} video(s) in no playlist "
                 f"({by_tier['core']} core, {by_tier['adjacent']} adjacent, "
                 f"{by_tier['other']} other)")

    (OUT_DIR / "channel.json").write_text(
        json.dumps({"channel": channel, "playlists": playlists},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "all_videos.json").write_text(
        json.dumps(all_videos, ensure_ascii=False, indent=2), encoding="utf-8")

    no_desc = sum(1 for v in all_videos if not v["description"].strip())
    log.info(f"wrote {len(all_videos)} unique videos to {OUT_DIR.relative_to(REPO_ROOT)} "
             f"({no_desc} with an empty description)")
    log.info(f"quota used: ~{QUOTA_UNITS} units of the 10,000/day free allowance")


if __name__ == "__main__":
    main()
