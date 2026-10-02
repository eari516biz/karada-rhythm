import urllib.request
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
from youtube_transcript_api import YouTubeTranscriptApi

sys.stdout.reconfigure(encoding='utf-8')

CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "..", "01_channels", "channels.json")
PROCESSED_FILE = os.path.join(os.path.dirname(__file__), "..", "03_data", "processed_videos.json")
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "03_data", "raw_transcripts")

os.makedirs(RAW_DATA_DIR, exist_ok=True)

def load_processed_ids():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_processed_ids(processed_set):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(processed_set)), f, ensure_ascii=False, indent=2)

def fetch_channel_videos(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            xml_data = res.read().decode('utf-8')
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
            videos = []
            for entry in root.findall('atom:entry', ns):
                vid = entry.find('yt:videoId', ns).text
                title = entry.find('atom:title', ns).text
                published = entry.find('atom:published', ns).text
                videos.append({
                    'video_id': vid,
                    'title': title,
                    'published_at': published
                })
            return videos
    except Exception as e:
        print(f"Error fetching RSS for {channel_id}: {e}")
        return []

def fetch_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcripts = api.list(video_id)
        # Try Japanese first
        t = transcripts.find_transcript(['ja'])
        snippets = t.fetch()
        full_text = " ".join([s.text for s in snippets])
        return full_text
    except Exception as e:
        print(f"Transcript unavailable for {video_id}: {e}")
        return None

def run_collector(max_videos=2, sleep_sec=10):
    processed = load_processed_ids()
    print(f"Already processed videos: {len(processed)}")

    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        channels = json.load(f)

    collected_count = 0

    for ch in channels:
        if collected_count >= max_videos:
            break

        cid = ch['channel_id']
        cname = ch['channel_name']
        print(f"\nChecking channel: {cname} ({cid})...")
        videos = fetch_channel_videos(cid)

        for v in videos:
            vid = v['video_id']
            if vid in processed:
                continue

            print(f"  -> Found new video: [{vid}] {v['title']}")
            transcript_text = fetch_transcript(vid)

            if transcript_text and len(transcript_text) > 100:
                record = {
                    "video_id": vid,
                    "title": v['title'],
                    "published_at": v['published_at'],
                    "channel_id": cid,
                    "channel_name": cname,
                    "expert_type": ch.get("expert_type", ""),
                    "category": ch.get("category", ""),
                    "transcript": transcript_text,
                    "transcript_length": len(transcript_text)
                }

                out_path = os.path.join(RAW_DATA_DIR, f"{vid}.json")
                with open(out_path, "w", encoding="utf-8") as out_f:
                    json.dump(record, out_f, ensure_ascii=False, indent=2)

                print(f"  [SUCCESS] Saved transcript ({len(transcript_text)} chars) to {vid}.json")
                processed.add(vid)
                collected_count += 1
                save_processed_ids(processed)

                if collected_count >= max_videos:
                    break

                print(f"  Sleeping {sleep_sec}s for rate safety...")
                time.sleep(sleep_sec)
            else:
                print(f"  [SKIP] No valid transcript found, skipping.")
                # Mark as processed to avoid retrying continuously
                processed.add(vid)
                save_processed_ids(processed)

    print(f"\nDone! Newly collected: {collected_count} videos.")

if __name__ == "__main__":
    run_collector(max_videos=1, sleep_sec=5)
