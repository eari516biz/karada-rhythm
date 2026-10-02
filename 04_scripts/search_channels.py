import urllib.request
import urllib.parse
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

queries = [
    '理学療法士 ストレッチ',
    'オガトレ',
    '精神科医 樺沢紫苑',
    '睡眠専門医 坪田',
    '内科医 ドクターハッシー',
    '理学療法士 姿勢'
]

channels = {}

for q in queries:
    url = f'https://www.youtube.com/results?search_query={urllib.parse.quote(q)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req) as res:
            html = res.read().decode('utf-8')
            m = re.search(r'var ytInitialData = ({.*?});</script>', html)
            if m:
                data = json.loads(m.group(1))
                sections = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
                for sec in sections:
                    for item in sec.get('itemSectionRenderer', {}).get('contents', []):
                        v = item.get('videoRenderer')
                        if v:
                            owner_runs = v.get('ownerText', {}).get('runs', [{}])[0]
                            c_name = owner_runs.get('text', '')
                            nav = owner_runs.get('navigationEndpoint', {})
                            browse_id = nav.get('browseEndpoint', {}).get('browseId', '')
                            if browse_id.startswith('UC') and c_name and c_name not in channels:
                                channels[c_name] = browse_id
    except Exception as e:
        print('Error:', e)

print(f"Found {len(channels)} candidate channels:")
results = []
for name, cid in channels.items():
    print(f"- {name}: {cid}")
    results.append({"channel_id": cid, "channel_name": name})

with open("daily_tuning/01_channels/channels_raw.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
