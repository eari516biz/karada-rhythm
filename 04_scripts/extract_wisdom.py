import os
import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

PROMPT_TEMPLATE = """
あなたはプロの健康科学・身体調律エディターです。
以下のYouTube動画（専門家による解説）の文字起こしテキストを読み込み、
読者が日常ですぐに実践できる「身体・健康・運動・睡眠・自律神経の知恵（チューニング法）」を抽出・構造化してください。

【厳格な品質・Tier判定ルール】
1. **Tier A（プロの現場知）**: 解剖学（具体的な筋肉名等）、神経科学、生体リズムに基づいた、一般にはあまり知られていないプロの具体的指導。
2. **Tier B（実践Tips）**: 検証や実践に基づく具体的な工夫・グッズの使い分けなど。
3. **Tier C（一般常識）**: 誰でも知っている当たり前（背筋を伸ばす、深呼吸するなど）。※捨てずに「対比用（common_belief_tier_c）」の文脈として残してください。

【出力フォーマット】
以下のキーを持つJSONオブジェクトの配列（JSONのみを出力してください）：
[
  {
    "title": "知恵のタイトル（20〜30文字）",
    "tier": "Tier A" | "Tier B" | "Tier C",
    "tier_reason": "Tier判定の根拠（1行）",
    "target_problem": "対象の不調・プチ不快・悩み",
    "common_belief_tier_c": "世間の一般的な思い込み・当たり前",
    "pro_solution": "プロの具体的な解決アプローチ",
    "mechanism": "なぜ効くのか（解剖学・生体リズムの納得感）",
    "action_step": "今すぐ試せる具体的アクション（2ステップ以内）",
    "target_category": "睡眠 / 姿勢・運動 / 疲労回復 / 脳・集中 / 食事・消化"
  }
]

【動画情報】
タイトル: {title}
チャンネル名: {channel_name} ({expert_type})
文字起こし:
{transcript}
"""

def extract_with_gemini(transcript_data, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = PROMPT_TEMPLATE.format(
        title=transcript_data['title'],
        channel_name=transcript_data['channel_name'],
        expert_type=transcript_data.get('expert_type', '専門家'),
        transcript=transcript_data['transcript'][:6000] # truncate if too long
    )

    req_payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(req_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, timeout=30) as res:
        res_data = json.loads(res.read().decode('utf-8'))
        text_resp = res_data['candidates'][0]['content']['parts'][0]['text']
        return json.loads(text_resp)

def process_file(file_path, output_db_path, api_key=None):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print(f"Skipping LLM extraction for {data['video_id']}: GEMINI_API_KEY not set.")
        return False

    print(f"Extracting wisdom from [{data['video_id']}] {data['title']}...")
    try:
        wisdom_items = extract_with_gemini(data, api_key)
        print(f"Extracted {len(wisdom_items)} wisdom items.")

        # Append to DB
        os.makedirs(os.path.dirname(output_db_path), exist_ok=True)
        with open(output_db_path, "a", encoding="utf-8") as out_f:
            for item in wisdom_items:
                record = {
                    "source_video_id": data['video_id'],
                    "source_title": data['title'],
                    "source_channel": data['channel_name'],
                    "expert_type": data.get('expert_type', ''),
                    "published_at": data.get('published_at', ''),
                    **item
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"Error during LLM extraction: {e}")
        return False

if __name__ == "__main__":
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "03_data", "raw_transcripts")
    db_path = os.path.join(os.path.dirname(__file__), "..", "03_data", "wisdom_db.jsonl")
    
    files = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith('.json')]
    for fp in files:
        process_file(fp, db_path)
