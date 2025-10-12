import json
import ndjson

# INPUT AND OUTPUT FILE PATHS
INPUT_FILE = "simulated_user_journeys.ndjson"
OUTPUT_FILE = "formatted_user_journeys.ndjson"

def format_event_for_posthog(event):
    cleaned_event = {
        "event_name": event.get("event_name"),
        "user_id": event.get("user_id"),
        "time": event.get("time"),
        "event_properties": {}
    }

    props = event.get("event_properties", {})

    # Keep all simple (non-list, non-excluded) props
    for key, value in props.items():
        if key not in ["blocks", "screen_id", "screen_version"] and not isinstance(value, list):
            cleaned_event["event_properties"][key] = value

    # Flatten blocks and elements
    blocks = props.get("blocks", [])
    for i, block in enumerate(blocks):
        if isinstance(block, dict):
            block_type = block.get("type")
            if block_type:
                cleaned_event["event_properties"][f"block_type_{i}"] = block_type

            elements = block.get("elements", [])
            for j, element in enumerate(elements):
                if isinstance(element, dict):
                    if "type" in element:
                        cleaned_event["event_properties"][f"element_type_{i}_{j}"] = element["type"]
                    if "text" in element:
                        cleaned_event["event_properties"][f"element_text_{i}_{j}"] = element["text"]

    return cleaned_event

# Load original events
with open(INPUT_FILE, "r") as f:
    raw_events = ndjson.load(f)

# Format them
formatted_events = [format_event_for_posthog(e) for e in raw_events]

# Write formatted NDJSON
with open(OUTPUT_FILE, "w") as f:
    ndjson.dump(formatted_events, f)

print(f"✅ Formatted {len(formatted_events)} events to '{OUTPUT_FILE}'")
