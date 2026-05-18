#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_outline_md.py — 从 outline.json + 题库.json 生成：
  1. KP标签速查.md（人读，vault 根/项目目录）
  2. outline.js（前端 file:// 加载用，绕 CORS）
  3. questions_index.js（前端 file:// 用，含每题的 id/subject/归属大纲）

输入：工具/web/outline.json (v0.2 schema)
      04实操题集/<学科>/题库.json (所有学科)
输出：50-项目/主网自动化竞赛/KP标签速查.md
      50-项目/主网自动化竞赛/工具/web/outline.js
      50-项目/主网自动化竞赛/工具/web/questions_index.js

用法：手动 `python3 工具/build_outline_md.py`
"""
import json, re, glob
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent  # 主网自动化竞赛/
OUTLINE = HERE / 'web' / 'outline.json'
OUT_MD = PROJ / 'KP标签速查.md'
OUT_JS = HERE / 'web' / 'outline.js'
OUT_QIDX = HERE / 'web' / 'questions_index.js'
BANKS_GLOB = str(PROJ / '04实操题集' / '*' / '题库.json')


def parse_outline_field(raw):
    """归属大纲字段：可能是 '1.1.10' 单 code，或 '[1.1.3, 2.1.3]' 多 code 列表"""
    if not raw:
        return []
    s = str(raw).strip()
    if s.startswith('['):
        # 形如 "[1.1.3, 2.1.3]"
        return [x.strip() for x in re.findall(r'(\d+(?:\.\d+)+)', s)]
    return [s]


def build_questions_index():
    """扫所有题库，按 KP code 聚合：{ code: [题概览...] }"""
    by_kp = {}
    by_subj = {}
    total = 0
    for p in sorted(glob.glob(BANKS_GLOB)):
        try:
            d = json.loads(Path(p).read_text(encoding='utf-8'))
        except Exception as e:
            print(f"  ✗ {p}: {e}")
            continue
        qs = d.get('questions') if isinstance(d, dict) else (d if isinstance(d, list) else [])
        for q in qs:
            qid = q.get('id', '')
            subj = q.get('subject', '')
            title = q.get('title', '')
            codes = parse_outline_field(q.get('归属大纲'))
            entry = {'id': qid, 'subject': subj, 'title': title, 'codes': codes}
            total += 1
            for c in codes:
                by_kp.setdefault(c, []).append(qid)
            by_subj.setdefault(subj, []).append(qid)
    return {
        'total': total,
        'by_kp': {k: sorted(v) for k, v in by_kp.items()},
        'by_subj': {k: sorted(v) for k, v in by_subj.items()},
    }

def main():
    o = json.loads(OUTLINE.read_text(encoding='utf-8'))
    prefix = o.get('tag_prefix', 'KP::')

    # 写 outline.js（file:// fallback）
    OUT_JS.write_text(
        '// 自动生成自 outline.json by build_outline_md.py — 勿手改\n'
        f'window.OUTLINE_DATA = {json.dumps(o, ensure_ascii=False, indent=2)};\n',
        encoding='utf-8'
    )

    # 写 questions_index.js（题库按 KP code 聚合）
    qidx = build_questions_index()
    OUT_QIDX.write_text(
        '// 自动生成自 04实操题集/*/题库.json by build_outline_md.py — 勿手改\n'
        f'window.QUESTIONS_INDEX = {json.dumps(qidx, ensure_ascii=False, indent=2)};\n',
        encoding='utf-8'
    )
    print(f"✓ 题库索引：{qidx['total']} 题，覆盖 {len(qidx['by_kp'])} 个 KP code")

    # 写 MD
    lines = []
    total = sum(len(sec['kps']) for cat in o['categories'] for sec in cat['sections'])

    lines += [
        '# KP 标签速查表',
        '',
        f"> 自动生成自 `工具/web/outline.json` · 版本 {o['version']} · {o['generated']}",
        f"> 来源大纲：`{o.get('source', '?')}`",
        f"> ",
        f"> **总览**：{total} 个 KP，编号体系对齐题库.json 的 `归属大纲` 字段。",
        '> ',
        f"> **Tag 命名**：`{prefix}<末级KP名>` 单层，不嵌套。如 `{prefix}定时任务`。",
        '> ',
        '> **录题流程**：写题进 题库.json 时填 `归属大纲: "X.Y.Z"` 字段（编号），脚本自动转 tag 推 Anki。',
        '> ',
        f"> **更新方式**：改 `outline.json` 后跑 `python3 工具/build_outline_md.py`",
        '',
    ]

    for cat in o['categories']:
        lines += [f"## {cat['ordinal']}、{cat['name']}", '']
        subjs = cat.get('subjects', [])
        if subjs:
            lines += [f"绑定后台学科：{' / '.join(subjs)}", '']
        for sec in cat['sections']:
            lines += [f"### {sec['code']} {sec['name']}", '']
            lines += [
                '| 编号 | 末级 KP 名 | Tag（复制这个） | 说明 |',
                '|---|---|---|---|',
            ]
            for kp in sec['kps']:
                tag = f"{prefix}{kp['name']}"
                lines.append(f"| `{kp['code']}` | **{kp['name']}** | `{tag}` | {kp['desc']} |")
            lines.append('')

    OUT_MD.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✓ {total} 个 KP → {OUT_MD.name} + outline.js")

if __name__ == '__main__':
    main()
