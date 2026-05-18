#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_source.py · 源文件 → question.json 录入桥（2026-05-18 大重构后新增）

设计：
  用户把老师发的题文件（word/xlsx/txt）放在 `04实操题集/{学科}/源文件/` 下，
  跑本脚本解析后追加进全局 question.json（按 编号 全局自增）。

用法：
  python3 import_source.py <学科> <源文件路径> [--dry-run]
  # 学科 = 04实操题集 下的文件夹名（如「操作系统」「数据库」）
  # 文件类型自动按扩展名识别（.docx / .xlsx / .txt / .md）

最小可用实现（骨架）：
  - .txt / .md：按规则切题（### 或 ## 作题号边界）
  - .docx：需要 python-docx（pip install python-docx）
  - .xlsx：需要 openpyxl（pip install openpyxl）
  - 暂用 stdin 模式作为兜底：传 --paste，从标准输入读多题
  - 每题字段：title / 题面 / 答案 / 题源 = 文件名
  - tags / 归属大纲：录入时留空，让用户事后跑 retag 工具或在 Anki 里补

TODO（用户用到时再补）：
  - docx/xlsx 真实解析（需引入第三方库）
  - 题面/答案分割规则需要看老师题文件的实际格式定
  - 录入时调用 LLM 做初判 归属大纲（可调本机 ask 工具或留空）
  - 答案 markdown 规范化、代码块清洗

参考：当前 question.json 字段 schema 见 _qdata.py 模块注释。
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qdata

ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛")
EXAM_DIR = ROOT / "04实操题集"


def parse_txt(text):
    """从 txt/md 切题。规则：
       - 以 `## ` 或 `### ` 开头视为题号
       - 题号后面到下一个题号之间的内容拆为「题面」和「答案」
         - 默认整段当题面，留空答案
         - 如果含 `### 答案` 或 `### Answer` 标记，则按之分割
    """
    import re
    blocks = re.split(r"\n(?=#{2,3}\s)", text.strip())
    out = []
    for b in blocks:
        if not b.strip().startswith("#"):
            continue
        first_line, _, rest = b.partition("\n")
        title = first_line.lstrip("# ").strip()
        # 切分题面 / 答案
        m = re.search(r"###\s*(答案|Answer)\s*\n", rest)
        if m:
            tian = rest[:m.start()].strip()
            ans = rest[m.end():].strip()
        else:
            tian = rest.strip()
            ans = ""
        out.append({"title": title, "题面": tian, "答案": ans})
    return out


def append_to_question_json(subject, items, source_name, dry_run=False):
    doc = _qdata.load()
    questions = doc["questions"]
    next_no = max(q["编号"] for q in questions) + 1 if questions else 1

    new_records = []
    for it in items:
        rec = {
            "编号": next_no,
            "subject": subject,
            "deck": f"实操题::{subject}",
            "title": it["title"],
            "题面": it["题面"],
            "答案": it["答案"],
            "题源": source_name,
            "tags": [],
            "归属大纲": "",
            "weak_count": 0,
            "correct_streak": 0,
            "last_wrong_at": None,
            "last_attempt_at": None,
            "notes": "",
        }
        new_records.append(rec)
        next_no += 1

    print(f"准备追加 {len(new_records)} 题到 [{subject}]，编号 {new_records[0]['编号']}~{new_records[-1]['编号']}")
    for r in new_records[:3]:
        print(f"  · #{r['编号']} {r['title'][:50]}")
    if len(new_records) > 3:
        print(f"  · ... 还有 {len(new_records)-3} 条")

    if dry_run:
        print("[DRY-RUN] 未写入。去掉 --dry-run 正式录入。")
        return

    doc["questions"].extend(new_records)
    doc["total"] = len(doc["questions"])
    doc["last_updated_at"] = datetime.now().isoformat(timespec="seconds")
    _qdata.save_all(doc)
    print(f"✓ 已追加，question.json 现有 {doc['total']} 题")


def main():
    p = argparse.ArgumentParser(description="源文件 → question.json 录入桥")
    p.add_argument("subject", help="学科名（= 04实操题集 下文件夹名）")
    p.add_argument("source", help="源文件路径（.txt/.md/.docx/.xlsx）")
    p.add_argument("--dry-run", action="store_true", help="只解析不写入")
    args = p.parse_args()

    src = Path(args.source)
    if not src.exists():
        sys.exit(f"❌ 源文件不存在: {src}")

    ext = src.suffix.lower()
    if ext in (".txt", ".md"):
        items = parse_txt(src.read_text(encoding="utf-8"))
    elif ext == ".docx":
        sys.exit("❌ docx 解析尚未落地。请先 `pip install python-docx` 再扩展本脚本。")
    elif ext in (".xlsx", ".xls"):
        sys.exit("❌ xlsx 解析尚未落地。请先 `pip install openpyxl` 再扩展本脚本。")
    else:
        sys.exit(f"❌ 不支持的扩展名: {ext}")

    if not items:
        sys.exit("❌ 没有解析出任何题目，检查源文件格式（## 或 ### 题号开头）")

    append_to_question_json(args.subject, items, src.name, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
