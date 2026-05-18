#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anki_sync.py · 「整理 anki」skill 后端 (2026-05-18 大重构后新增)

设计目标：
  把 Anki 端我手动改过的内容（备注/答案订正/tag/归属大纲）回写到本地 question.json。
  实现「Anki 是日常交互入口 / question.json 是数据 SSOT」的双向同步。

触发：
  关键词「整理 anki」「弄一下 anki」「整理一下 anki」（由 .claude/skills/整理anki.md 路由触发）
  skill 直接调用本脚本。

数据流（设想）：
  1. 通过 AnkiConnect 拉所有 `实操题::*` 牌组的卡片
  2. 按 Front 字段里的 `[#编号]` 标识反向定位到 question.json 的题
  3. 比对差异：
     - Back（答案）有变化 → 题库.答案 更新（但要慎重，可能用户改的是 Anki 端格式而不是答案本身）
     - Tags 变化 → 题库.tags 同步
     - notes 字段（如有）→ 题库.notes 追加
  4. 输出变更摘要，让用户确认后写回 question.json

最小可用实现（骨架，关键流程已搭好，业务规则留待后续打磨）：

用法：
  python3 anki_sync.py                    # 全量同步
  python3 anki_sync.py 操作系统             # 单学科
  python3 anki_sync.py --dry-run           # 只列差异，不写

TODO（用户用到时再补的边界规则）：
  - Back 内容回写要做格式去噪（Anki 自动加的 <br><div> 等 HTML 标签需还原成 markdown）
  - tag 变化时区分「Anki 端新增」vs「Anki 端删除」并据此更新题库
  - 大批量变更应有 review 步骤防误改
  - 训练状态字段（reps/ease）单向流入：question.json 写不写？现在脚本只读 weak，由 CV 训练写
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qdata

ANKI_URL = "http://127.0.0.1:8765"


def ank(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", ANKI_URL,
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"curl failed: {r.stderr}")
    res = json.loads(r.stdout)
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect [{action}]: {res['error']}")
    return res["result"]


def html_to_md_simple(html):
    """简化 HTML → markdown 还原（Anki 端编辑后的反向清洗）"""
    if not html:
        return ""
    s = html
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</?div[^>]*>", "\n", s)
    s = re.sub(r"</?p[^>]*>", "\n", s)
    s = re.sub(r"<strong>(.+?)</strong>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<b>(.+?)</b>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<code>(.+?)</code>", r"`\1`", s, flags=re.DOTALL)
    s = re.sub(r"<pre><code>(.+?)</code></pre>", r"```\n\1\n```", s, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s


def diff_subject(subject, dry_run=True):
    deck = f"实操题::{subject}"
    try:
        note_ids = ank("findNotes", query=f'deck:"{deck}"')
    except Exception as e:
        print(f"  ✗ AnkiConnect 失败: {e}")
        return
    if not note_ids:
        print(f"  · {deck}: 牌组无卡片")
        return

    notes_info = ank("notesInfo", notes=note_ids)
    q_by_no = {q["编号"]: q for q in _qdata.by_subject(subject)}

    diff_count = 0
    for note in notes_info:
        front = note["fields"].get("Front", {}).get("value", "")
        m = re.search(r"\[#(\d+)\]", front)
        if not m:
            continue
        no = int(m.group(1))
        q = q_by_no.get(no)
        if not q:
            continue

        anki_back_html = note["fields"].get("Back", {}).get("value", "")
        anki_tags = set(note.get("tags", []))

        anki_back_md = html_to_md_simple(anki_back_html)
        local_ans = q.get("答案", "").strip()

        # 简单对比：内容长度差异较大且本地为空 → 拉取 Anki 端
        differences = []
        if anki_back_md and not local_ans:
            differences.append(("答案", f"本地为空，Anki 端有 {len(anki_back_md)} 字"))
        # tag 同步检查（差异 > 阈值的才提醒）
        local_tags = set(t.replace(" ", "_") for t in q.get("tags", []))
        anki_only = anki_tags - local_tags - {"主网竞赛", subject}
        # 过滤大纲_* 等系统 tag
        anki_only = {t for t in anki_only if not t.startswith("大纲_")}
        if anki_only:
            differences.append(("tags", f"Anki 端多了: {sorted(anki_only)}"))

        if differences:
            diff_count += 1
            if diff_count <= 10:
                print(f"  ⚠ #{no} {q['title'][:40]}")
                for field, info in differences:
                    print(f"      {field}: {info}")

    print(f"  · {subject}: {diff_count} 题有差异" + (" (DRY-RUN)" if dry_run else ""))
    if not dry_run and diff_count:
        print("    ⚠️ 自动回写尚未实现（骨架版本）。请逐题人工确认。")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("subject", nargs="?", help="单学科同步（省略=全部）")
    p.add_argument("--dry-run", action="store_true", help="只列差异，不写回")
    args = p.parse_args()

    subjects = [args.subject] if args.subject else _qdata.subjects()

    print(f"=== anki_sync · Anki → question.json 差异检查 ===\n")
    for s in subjects:
        diff_subject(s, dry_run=args.dry_run)
    print(f"\n完成。如要回写，去掉 --dry-run（注意：当前为骨架版本，回写逻辑待完善）。")


if __name__ == "__main__":
    main()
