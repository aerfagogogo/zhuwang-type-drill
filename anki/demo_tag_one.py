#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_tag_one.py — 演示给一张 Anki 卡打 KP tag

流程：
1. 拉操作系统牌组第一张卡
2. 看题面提取关键词
3. 跟 outline.json 的 KP keywords 比对，得出候选 KP
4. 调 AnkiConnect addTags 把 KP tag 加上
5. 报告结果

跑一次后去 Anki 浏览器查这张卡，应该看到新 tag。
"""
import json
import re
import subprocess
from pathlib import Path

ANKI = "http://127.0.0.1:8765"
DECK = "实操题::操作系统"
OUTLINE_PATH = Path(__file__).resolve().parents[1] / 'web' / 'outline.json'

def ank(action, params=None):
    """AnkiConnect via curl（urllib 跟它 502，不知道为啥；curl 没事）"""
    body = {"action": action, "version": 6}
    if params:
        body["params"] = params
    r = subprocess.run(
        ['curl', '-s', '-X', 'POST', ANKI,
         '-H', 'Content-Type: application/json',
         '-d', json.dumps(body, ensure_ascii=False)],
        capture_output=True, text=True, timeout=15
    )
    if r.returncode != 0:
        raise RuntimeError(f"curl 失败: {r.stderr}")
    resp = json.loads(r.stdout)
    if resp.get('error'):
        raise RuntimeError(f"AnkiConnect error: {resp['error']}")
    return resp.get('result')


def strip_html(s: str) -> str:
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def suggest_kps(text: str, outline) -> list:
    """按 keywords 匹配，返回候选 KP（含完整 tag + 命中关键词）"""
    hits = []
    low = text.lower()
    for cat in outline['categories']:
        for sec in cat['sections']:
            for kp in sec['kps']:
                matched_kw = [k for k in kp['keywords'] if k.lower() in low]
                if matched_kw:
                    tag = f"KP::{cat['tag_segment']}::{sec['tag_segment']}::{kp['name']}"
                    hits.append({
                        'tag': tag,
                        'kp_name': kp['name'],
                        'matched': matched_kw,
                    })
    return hits


def main():
    outline = json.loads(OUTLINE_PATH.read_text(encoding='utf-8'))

    # 1. 第一张卡
    card_ids = ank("findCards", {"query": f'deck:"{DECK}"'})
    if not card_ids:
        print(f"× 牌组 {DECK} 没卡")
        return
    card = ank("cardsInfo", {"cards": [card_ids[0]]})[0]
    note_id = card['note']
    fields = card['fields']
    front_key = 'Front' if 'Front' in fields else list(fields.keys())[0]
    front_text = strip_html(fields[front_key]['value'])

    print(f"📇 卡片 cardId={card['cardId']} noteId={note_id}")
    print(f"📝 题面: {front_text[:200]}")
    print(f"🏷️  现有 tags: {card.get('tags') or '(无)'}")
    print()

    # 2. 关键词匹配
    hits = suggest_kps(front_text, outline)
    if not hits:
        print("× 没匹配到 KP，需要扩 keywords 或手填")
        return

    print(f"💡 推荐 KP tag（{len(hits)} 个候选）:")
    for h in hits:
        print(f"   • {h['tag']}")
        print(f"     ↳ 命中: {', '.join(h['matched'])}")
    print()

    # 3. 加 tag（先全加，不交互。下个版本可以加交互）
    tags_to_add = [h['tag'] for h in hits]
    # AnkiConnect addTags 接受 notes(list) + tags(空格分隔字符串)
    ank("addTags", {
        "notes": [note_id],
        "tags": " ".join(tags_to_add)
    })

    # 4. 验证
    info = ank("notesInfo", {"notes": [note_id]})[0]
    print(f"✓ tag 已加，现在 noteId={note_id} 的 tags:")
    for t in info.get('tags', []):
        marker = '  ⭐' if t.startswith('KP::') else '    '
        print(f"{marker} {t}")

    print()
    print(f"👉 去 Anki 浏览器搜 'nid:{note_id}' 验证，或浏览器侧栏 KP:: 那一行点开")


if __name__ == '__main__':
    main()
