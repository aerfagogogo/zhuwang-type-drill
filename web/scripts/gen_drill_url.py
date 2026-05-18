#!/usr/bin/env python3
"""
读 <学科>/薄弱点.json + <学科>/<题>.md → 拼成 questions JSON → base64 → URL
用法: python3 gen_drill_url.py [学科]
"""
import json
import re
import sys
import base64
import urllib.parse
from pathlib import Path

ROOT = Path('/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛/04实操题集')
BASE_URL = 'https://aerfagogogo.github.io/zhuwang-type-drill/'

def read_question_text(subj, qid):
    """从 <学科>/<题号-*.md> 抽 ## 题目/题面 段落。"""
    num = qid.split('-')[-1]
    candidates = list((ROOT / subj).glob(f'{num}-*.md'))
    if not candidates:
        return ''
    text = candidates[0].read_text(encoding='utf-8')
    # 去掉 frontmatter
    m = re.match(r'^---\n.*?\n---\n', text, re.DOTALL)
    if m:
        text = text[m.end():]
    m = re.search(r'^##\s+题[目面]\s*\n(.+?)(?=\n##\s|\Z)', text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ''

def main():
    subj = sys.argv[1] if len(sys.argv) > 1 else '操作系统'
    weak_path = ROOT / subj / '薄弱点.json'
    if not weak_path.exists():
        print(f'[!] 未找到 {weak_path}', file=sys.stderr); sys.exit(1)

    data = json.load(weak_path.open(encoding='utf-8'))
    questions = []
    for entry in data:
        # 跳过已过关
        if entry.get('correct_streak', 0) >= 3:
            continue
        # 收集所有 notes 中的 drills，dedup
        seen = set(); drills = []
        for note in entry.get('notes', []):
            for d in note.get('drills', []):
                if d not in seen:
                    seen.add(d); drills.append(d)
        if not drills:
            continue
        title = entry.get('title', '')
        qti = read_question_text(subj, entry['id']) or title
        questions.append({
            'id': entry['id'],
            '题面': qti,
            'drills': drills,
        })

    if not questions:
        print('[!] 没有可练题（薄弱点为空或全部已过关）', file=sys.stderr); sys.exit(0)

    payload = {'subject': subj, 'questions': questions}
    enc = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode('utf-8')).decode()
    url = BASE_URL + '?q=' + urllib.parse.quote(enc)
    print(f'# {subj} · {len(questions)} 题待练')
    print(url)

if __name__ == '__main__':
    main()
