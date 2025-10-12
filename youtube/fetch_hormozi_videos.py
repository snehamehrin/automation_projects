import os
import sys
from apify_client import ApifyClient
import pandas as pd
from dotenv import load_dotenv
from typing import Optional

"""
Usage:
  1) Set your Apify token in env: export APIFY_TOKEN=your_token
     OR create youtube/.env with APIFY_TOKEN=your_token
  2) pip install apify-client pandas python-dotenv
  3) python youtube/fetch_hormozi_videos.py

This script calls the YouTube scraper actor and collects all videos from
Alex Hormozi's channel, saving a CSV named alex_hormozi_videos.csv
in the current working directory.
"""

# Load .env from the youtube folder (same directory as this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

CHANNEL_URLS = [
    "https://www.youtube.com/@AlexHormozi",
    "https://www.youtube.com/@AlexHormozi/videos",
]

# Default to very large cap to capture the full backlog; the actor may enforce its own limits
RUN_INPUT = {
    "searchQueries": [],
    # Actor expects objects with "url" keys, not plain strings
    "startUrls": [{"url": u} for u in CHANNEL_URLS],
    "maxResults": 100000,  # request a high cap
    "maxResultsShorts": 0,  # we will also filter client-side
    "maxResultStreams": 0,
    # "subtitlesLanguage": "any",
    # "subtitlesFormat": "srt",
}

# Replace with your actor ID if different
DEFAULT_ACTOR_ID = "h7sDV53CddomktSi5"


def parse_duration_seconds(value: Optional[object]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        # If YouTube-style mm:ss or hh:mm:ss
        if ":" in s and all(part.isdigit() for part in s.split(":")):
            parts = [int(p) for p in s.split(":")]
            secs = 0
            for p in parts:
                secs = secs * 60 + p
            return secs
        # Fallback: unknown string format
    return None


def is_short_video(item: dict) -> bool:
    url = item.get("videoUrl") or ""
    if "/shorts/" in url:
        return True
    # If duration available, treat < 70 seconds as short
    secs = parse_duration_seconds(item.get("duration"))
    if secs is not None and secs < 70:
        return True
    # Some actors expose a flag
    if item.get("type") == "short" or item.get("isShort") is True:
        return True
    return False


def is_vlog(item: dict) -> bool:
    title = (item.get("title") or "").lower()
    return "vlog" in title


def main() -> int:
    api_token = os.getenv("APIFY_TOKEN")
    if not api_token:
        print("ERROR: Please set APIFY_TOKEN environment variable.")
        print("Create youtube/.env with: APIFY_TOKEN=apify_api_xxx  OR  export APIFY_TOKEN=apify_api_xxx")
        return 1

    client = ApifyClient(api_token)

    print(f"Starting Apify actor {DEFAULT_ACTOR_ID} for Alex Hormozi channel…")
    run = client.actor(DEFAULT_ACTOR_ID).call(run_input=RUN_INPUT)

    print("Fetching results…")
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    videos = []
    for it in items:
        video_id = it.get("videoId")
        video_url = it.get("videoUrl")
        item_type = it.get("type")
        looks_like_video = item_type == "video" or video_id or video_url
        if not looks_like_video:
            continue
        if is_short_video(it) or is_vlog(it):
            continue
        url = video_url or (f"https://www.youtube.com/watch?v={video_id}" if video_id else None)
        videos.append({
            "title": it.get("title"),
            "videoId": video_id,
            "url": url,
            "publishedAt": it.get("publishedAt"),
            "duration": it.get("duration"),
            "viewCount": it.get("viewCount"),
        })

    print(f"Total long-form, non-vlog videos found: {len(videos)}")

    out_csv = "alex_hormozi_videos.csv"
    pd.DataFrame(videos).to_csv(out_csv, index=False)
    print(f"Saved {out_csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main()) 