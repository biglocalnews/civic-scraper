import requests
import json
from datetime import datetime
import os

SITES = [
    # {"url": "https://turlockca.portal.civicclerk.com", "place": "turlock", "state": "ca"},
    # {"url": "https://jacksonmi.civicclerk.com", "place": "jackson", "state": "mi"},
    # {"url": "https://alpharettaga.civicclerk.com", "place": "alpharetta", "state": "ga"},
    {"url": "https://islamoradafl.portal.civicclerk.com/", "place": "Islamorada", "state": "fl"},
]

PAGE_SIZE = 20

def get_api_base(site_url):
    # Handles both portal and non-portal civicclerk domains
    if ".portal." in site_url:
        domain = site_url.split(".portal.")[0].replace("https://", "")
    else:
        domain = site_url.split(".civicclerk.com")[0].replace("https://", "")
    return f"https://{domain}.api.civicclerk.com/v1/Events"

def fetch_all_events(api_base):
    all_events = []
    skip = 0
    while True:
        params = {
            "$orderby": "startDateTime asc, eventName asc",  # ASCENDING order
            "$top": PAGE_SIZE,
            "$skip": skip
        }
        print(f"Fetching events $skip={skip} from {api_base}")
        resp = requests.get(api_base, params=params)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("value", [])
        if not events:
            break
        all_events.extend(events)
        skip += PAGE_SIZE
    return all_events

def standardise_asset_url(site_url, meeting_id, fileId):
    site_url = site_url.rstrip('/')
    return f"{site_url}/event/{meeting_id}/files/agenda/{fileId}"

def standardise_meeting_url(site_url, meeting_id):
    site_url = site_url.rstrip('/')
    return f"{site_url}/event/{meeting_id}/overview"

def extract_event_details(event, site_url):
    # Standardize meeting_date to YYYY-MM-DD HH:MM:SS (local time if needed, else UTC)
    meeting_date_raw = event.get("startDateTime")
    meeting_date = None
    if meeting_date_raw:
        try:
            # Parse ISO format and output as 'YYYY-MM-DD HH:MM:SS'
            dt = datetime.fromisoformat(meeting_date_raw.replace('Z', '+00:00'))
            meeting_date = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            meeting_date = meeting_date_raw  # fallback to raw if parsing fails
    # Standardize publishOn for each asset and set clickable url
    assets = event.get("publishedFiles", [])
    for asset in assets:
        publish_on_raw = asset.get("publishOn")
        if publish_on_raw:
            try:
                dt = datetime.fromisoformat(publish_on_raw.replace('Z', '+00:00'))
                asset["publishOn"] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass  # leave as is if parsing fails
        fileId = asset.get("fileId")
        if fileId is not None:
            asset["url"] = standardise_asset_url(site_url, event.get("id"), fileId)
    return {
        "meeting_id": event.get("id"),
        "meeting_name": event.get("eventName"),
        "meeting_date": meeting_date,
        "asset_type": event.get("eventCategoryName"),
        "meeting_url": standardise_meeting_url(site_url, event.get('id')),
        "assets": assets
    }

if __name__ == "__main__":
    output_dir = "./Civic_Clerk_Json"
    os.makedirs(output_dir, exist_ok=True)
    for site in SITES:
        api_base = get_api_base(site["url"])
        all_events = fetch_all_events(api_base)
        print(f"Fetched {len(all_events)} events for {site['place']}, {site['state']}.")
        event_details = [extract_event_details(ev, site["url"]) for ev in all_events]
        out_file_name = f"scraped_events_api_{site['place']}_{site['state']}.json"
        out_path = f"{output_dir}/{out_file_name}"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(event_details, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(event_details)} events to {out_file_name}")