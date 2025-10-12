import json
import time
from posthog import Posthog
from datetime import datetime

# First uninstall current posthog version:
# pip uninstall posthog
# Then install an older version:
# pip install "posthog<3.0"

# ✅ Replace this with your actual PostHog project API key
POSTHOG_API_KEY = "phc_rcmj2HlhKZN4KpkODarrYrhXyBURHRYcHZMsxNpwcR3"
POSTHOG_HOST = "https://app.posthog.com"  # or your self-hosted URL

posthog = Posthog(project_api_key=POSTHOG_API_KEY, host=POSTHOG_HOST)

# Load events
import json
from datetime import datetime
import posthog

# 🔐 Replace with your actual PostHog project API key
posthog.project_api_key = "phc_FYuiluJi3bgmotlB6OGxOBckwut16DJoYfQ7PwuwROd"
posthog.host = "https://app.posthog.com"

# 📂 Load your NDJSON file
with open("supercom_100_users_varied_journeys.ndjson", "r") as f:
    for line in f:
        try:
            event = json.loads(line)
            event_type = event.get("event_name")
            distinct_id = event.get("user_id")
            timestamp = event.get("time")

            if not event_type or not distinct_id:
                print("❌ Skipping incomplete event:", event)
                continue

            # 🔄 Flatten top-level properties (ignore meta fields)
            properties = {
                k: v for k, v in event.items()
                if k not in ["event_name", "user_id", "time", "blocks"]
            }

            # 🔄 Flatten blocks and elements (1 block + 1 element max)
            blocks = event.get("blocks", [])
            if blocks and isinstance(blocks, list) and len(blocks) > 0:
                block = blocks[0]
                for key in ["id", "type", "version"]:
                    if key in block:
                        properties[f"block_{key}"] = block[key]

                elements = block.get("elements", [])
                if elements and isinstance(elements, list) and len(elements) > 0:
                    element = elements[0]
                    for key in ["id", "type", "version", "content_id", "text"]:
                        if key in element:
                            properties[f"element_{key}"] = element[key]

            # ⏱ Convert timestamp
            if isinstance(timestamp, str):
                timestamp = datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S")

            # 🚀 Send to PostHog
            posthog.capture(distinct_id, event_type, properties, timestamp=timestamp)
            print(f"✅ Sent: {event_type} → {distinct_id}")

        except Exception as e:
            print("❌ Error:", e)

posthog.flush()
print("🎉 All events sent to PostHog.")
