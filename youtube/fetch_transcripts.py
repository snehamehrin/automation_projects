import os
import sys
import time
import csv
from typing import Optional, Dict, Any
from apify_client import ApifyClient
from dotenv import load_dotenv

"""
Usage:
  1) Ensure youtube/fetch_hormozi_videos.py has been run to produce alex_hormozi_videos.csv
  2) Create youtube/.env with APIFY_TOKEN=your_token
  3) pip install apify-client python-dotenv
  4) python youtube/fetch_transcripts.py [input_csv] [out_dir]

Defaults:
  input_csv: alex_hormozi_videos.csv (in current working dir)
  out_dir:   youtube/transcripts

This will call the transcript actor (CTQcdDtqW5dvELvur) for each video URL
and save a {videoId}.txt file containing the transcript text if available.
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

TRANSCRIPT_ACTOR_ID = "CTQcdDtqW5dvELvur"


def read_videos_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def extract_text_from_item(item: Dict[str, Any]) -> Optional[str]:
    # Try common keys where transcript might live
    for key in ("transcript", "transcriptText", "text", "content"):
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val
    # If subtitles are provided as array of segments
    subs = item.get("subtitles") or item.get("segments")
    if isinstance(subs, list):
        parts = []
        for seg in subs:
            t = seg.get("text") if isinstance(seg, dict) else None
            if t:
                parts.append(t)
        if parts:
            return "\n".join(parts)
    return None


def main() -> int:
    api_token = os.getenv("APIFY_TOKEN")
    if not api_token:
        print("ERROR: Please set APIFY_TOKEN in youtube/.env or environment.")
        return 1

    input_csv = sys.argv[1] if len(sys.argv) > 1 else "alex_hormozi_videos.csv"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join("youtube", "transcripts")

    os.makedirs(out_dir, exist_ok=True)

    client = ApifyClient(api_token)

    processed = 0
    saved = 0

    for row in read_videos_csv(input_csv):
        url = row.get("url")
        video_id = row.get("videoId") or "unknown"
        title = row.get("title") or ""
        if not url:
            continue

        out_path = os.path.join(out_dir, f"{video_id}.txt")
        if os.path.exists(out_path):
            processed += 1
            continue

        run_input = {
            "startUrls": [url],            # per example, strings are accepted
            "language": "Default",        # or set to "English"
            "includeTimestamps": "No",    # keep plain text
        }

        print(f"Fetching transcript for {video_id} → {title[:80]}…")
        try:
            run = client.actor(TRANSCRIPT_ACTOR_ID).call(run_input=run_input)
            dataset_client = client.dataset(run["defaultDatasetId"])
            text_chunks = []
            for item in dataset_client.iterate_items():
                text = extract_text_from_item(item)
                if text:
                    text_chunks.append(text)
            if text_chunks:
                content = "\n\n".join(text_chunks)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)
                saved += 1
            else:
                # Save a marker file to avoid re-trying every run
                with open(out_path + ".missing", "w", encoding="utf-8") as f:
                    f.write("NO_TRANSCRIPT")
        except Exception as e:
            print(f"Error for {video_id}: {e}")
        finally:
            processed += 1
            # Gentle pacing to avoid rate limits
            time.sleep(2)

    print(f"Done. Processed {processed} videos, saved {saved} transcripts to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 