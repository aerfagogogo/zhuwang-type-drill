#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_subject_bank.py v3 · 2026-05-18 大重构后重写
====================================================

作用变更（关键）：
  旧版：扫学科 MD → 派生 题库.json（已废弃，因为 MD 已不再维护）
  新版：从 question.json → 派生「学科+源文件」副产物 md，作为 Anki 推题归档

输出：
  04实操题集/{subject}/anki归档/{subject}-{源文件名}.md

每份 md 内容：
  - YAML frontmatter（学科、源文件、生成时间、题数）
  - 题目列表，每题：
    - ## #{编号} - {title}
    - **归属大纲**: {归属大纲}
    - **tags**: ...
    - **题面**: ...
    - **答案**: ...

用法：
  python3 build_subject_bank.py --all          # 全部学科
  python3 build_subject_bank.py 操作系统       # 单学科
"""

import sys
import re
from pathlib import Path
from collections import defaultdict
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qdata

ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛")
EXAM_DIR = ROOT / "04实操题集"


def sanitize_filename(s):
    """文件名安全化：去掉路径分隔符、特殊字符，保留中文"""
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)
    s = re.sub(r"\s+", "_", s).strip("._")
    if not s:
        s = "未命名源文件"
    return s[:80]


def build_one_subject(subject):
    qs = _qdata.by_subject(subject)
    if not qs:
        print(f"  ⚠️  {subject}: question.json 无题目，跳过")
        return 0

    # 按 题源 分组（题源可能为空，统一归到「未标题源」组）
    by_source = defaultdict(list)
    for q in qs:
        key = (q.get("题源") or "未标题源").strip()
        by_source[key].append(q)

    out_dir = EXAM_DIR / subject / "anki归档"
    out_dir.mkdir(parents=True, exist_ok=True)

    count_files = 0
    for source, qlist in by_source.items():
        fname = f"{subject}-{sanitize_filename(source)}.md"
        fpath = out_dir / fname
        lines = [
            "---",
            f"subject: {subject}",
            f"题源: {source}",
            f"题数: {len(qlist)}",
            f"生成: {date.today()}",
            f"来源: question.json (全局题库)",
            f"说明: Anki 推题副产物，自动生成，勿手改",
            "---",
            "",
            f"# {subject} · {source}",
            "",
            f"> 本文档由 build_subject_bank.py 自动生成，是 Anki 推题的归档副产物。",
            f"> 真正的题库 SSOT 是项目根的 question.json，不要在此文件修改。",
            "",
        ]
        for q in sorted(qlist, key=lambda x: x["编号"]):
            lines.append(f"## #{q['编号']} · {q.get('title','')}")
            lines.append("")
            if q.get("归属大纲"):
                lines.append(f"- **归属大纲**: {q['归属大纲']}")
            if q.get("tags"):
                lines.append(f"- **tags**: {', '.join(q['tags'])}")
            if q.get("deck"):
                lines.append(f"- **deck**: `{q['deck']}`")
            lines.append("")
            lines.append("### 题面")
            lines.append("")
            lines.append(q.get("题面", "").strip() or "_（空）_")
            lines.append("")
            lines.append("### 答案")
            lines.append("")
            lines.append(q.get("答案", "").strip() or "_（待补）_")
            lines.append("")
            wc = q.get("weak_count", 0)
            cs = q.get("correct_streak", 0)
            if wc or cs or q.get("last_attempt_at"):
                lines.append(f"- _训练状态_: weak={wc} streak={cs} last={q.get('last_attempt_at','-')}")
                lines.append("")
            lines.append("---")
            lines.append("")
        fpath.write_text("\n".join(lines), encoding="utf-8")
        count_files += 1
    print(f"  ✓ {subject}: {len(qs)} 题 → {count_files} 份副产物 md  ({out_dir.name}/)")
    return count_files


def main():
    args = sys.argv[1:]
    if "--all" in args or not args:
        subjects = _qdata.subjects()
    else:
        subjects = args

    print(f"=== build_subject_bank · question.json → anki 副产物 md ===\n")
    total_files = 0
    for s in subjects:
        n = build_one_subject(s)
        total_files += n
    print(f"\n合计 {len(subjects)} 学科 / {total_files} 份副产物 md")


if __name__ == "__main__":
    main()
