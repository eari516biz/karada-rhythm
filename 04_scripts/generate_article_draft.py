import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "03_data", "wisdom_db.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "05_articles")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_draft(topic_category="姿勢・運動", limit=10):
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    items = []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    # Diversity Guard: Ensure no single channel dominates (max 1-2 items per channel)
    selected = []
    channel_counts = {}
    
    # Prioritize Tier A first
    target_items.sort(key=lambda x: 0 if x.get('tier') == 'Tier A' else 1)
    
    for item in target_items:
        ch = item.get('source_channel', 'unknown')
        if channel_counts.get(ch, 0) < 2:  # max 2 per expert
            selected.append(item)
            channel_counts[ch] = channel_counts.get(ch, 0) + 1
        if len(selected) >= limit:
            break

    if not selected:
        print(f"No items found for category: {topic_category}")
        return

    lines = []
    lines.append(f"# 【からだリズム Vol.1】プロが現場で教える身体の知恵 {len(selected)}選")
    lines.append("\n日常生活で感じる身体のコリやだるさ。ネットで調べると「とりあえずストレッチ」「姿勢を正しく」といった当たり前の情報ばかりが目につきます。")
    lines.append("しかし、理学療法士や専門医など、日頃から身体の現場と向き合っているプロの指導を見てみると、私たちが思っている「常識」とは少し違った、具体的で効果的なアプローチが存在します。")
    lines.append("\n今回は、現場のプロが実践している『からだリズムの整え方』を厳選してご紹介します。\n")
    lines.append("---\n")

    for idx, item in enumerate(selected, 1):
        lines.append(f"## {idx}. {item.get('title')}")
        lines.append(f"\n- **お悩み**: {item.get('target_problem')}")
        lines.append(f"- **一般的な思い込み（Tier C）**: {item.get('common_belief_tier_c')}")
        lines.append(f"- **専門家の調律アプローチ（{item.get('tier', 'Tier A')}）**: {item.get('pro_solution')}")
        lines.append(f"- **なぜ効くのか（メカニズム）**: {item.get('mechanism')}")
        lines.append(f"- **今すぐできるアクション**: {item.get('action_step')}")
        lines.append(f"\n> 💡 *出典・参照: {item.get('expert_type', '専門家')}による解説*")
        lines.append("\n---\n")

    lines.append("## おわりに")
    lines.append("\n身体の調律は、大がかりな運動や道具を用意しなくても、「ちょっとした動かし方や意識の向け方」を変えるだけで驚くほど楽になります。")
    lines.append("まずは今日、気になった1つから試してみてください。")

    draft_content = "\n".join(lines)
    out_file = os.path.join(OUTPUT_DIR, "article_draft_vol1.md")
    with open(out_file, "w", encoding="utf-8") as out_f:
        out_f.write(draft_content)

    print(f"Draft generated successfully: {out_file}")
    print(f"Included {len(selected)} wisdom items.")

if __name__ == "__main__":
    generate_draft(topic_category="姿勢・運動", limit=10)
