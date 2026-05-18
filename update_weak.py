#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_weak.py  —  更新题库训练记录（机械执行，不走 LLM）

2026-05-18 大重构后：数据源从 04实操题集/{学科}/薄弱点.json 改为单一全局 question.json。

用法（向后兼容两种 id 格式）：
    python3 update_weak.py <id>  <verdict> <notes_text> [--drills "cmd1,cmd2"] [--wrong "p1,p2"]
    python3 update_weak.py <编号> <verdict> <notes_text> [...]

id 格式（任一即可）：
    1. 旧风格 {学科}-{NNN}（如 操作系统-006）—— 解释为该学科内的第 NNN 题
    2. 新风格 全局整数编号（如 78）—— 直接定位 question.json 的 编号 字段

verdict：✅ 完全正确 / ⚠️ 对但不规范 / ❌ 错了

写入字段：weak_count / correct_streak / last_wrong_at / last_attempt_at / notes(list of training entry)

示例:
    python3 update_weak.py 操作系统-006 ❌ "ps 排行漏 n + 重定向" --drills "ps -ef --sort=-pmem | head -5 > out.txt"
    python3 update_weak.py 78 ✅ "ifconfig 一次过"
"""
import argparse
import sys
from datetime import date
from pathlib import Path

# 引入共享适配器
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qdata


def resolve_question(id_or_no):
    """支持两种 id 风格，返回 question dict"""
    # 1) 纯数字 → 全局编号
    if id_or_no.isdigit():
        q = _qdata.by_no(int(id_or_no))
        if not q:
            sys.exit(f"[update_weak] 找不到编号 {id_or_no}")
        return q
    # 2) {学科}-{NNN} 风格
    if "-" in id_or_no:
        subject, _, nnn = id_or_no.rpartition("-")
        try:
            n = int(nnn)
        except ValueError:
            sys.exit(f"[update_weak] 无法解析 id={id_or_no}（期望 {{学科}}-NNN 或纯数字编号）")
        # 在该学科里取第 n 题（按 question.json 内顺序）
        subj_qs = _qdata.by_subject(subject)
        if n < 1 or n > len(subj_qs):
            sys.exit(f"[update_weak] {subject} 学科共 {len(subj_qs)} 题，找不到第 {n} 题")
        return subj_qs[n - 1]
    sys.exit(f"[update_weak] 无法解析 id={id_or_no}")


def main():
    parser = argparse.ArgumentParser(description="更新题库训练记录，机械执行勿改")
    parser.add_argument("id_or_no", help="题目 id（{学科}-NNN 或 全局编号）")
    parser.add_argument("verdict", help="✅ / ⚠️ / ❌")
    parser.add_argument("notes", help="本次训练简注，一句话")
    parser.add_argument("--drills", default="", help="标准命令，英文逗号分隔")
    parser.add_argument("--wrong", default="", help="错点描述，英文逗号分隔")
    args = parser.parse_args()

    q = resolve_question(args.id_or_no)
    today = str(date.today())
    verdict = args.verdict.strip()

    # 更新统计字段
    q["last_attempt_at"] = today
    if verdict == "✅":
        q["correct_streak"] = int(q.get("correct_streak", 0) or 0) + 1
        # weak_count 不动（历史累计错次数，不因答对而减）
    else:  # ⚠️ 或 ❌
        q["weak_count"] = int(q.get("weak_count", 0) or 0) + 1
        q["correct_streak"] = 0
        q["last_wrong_at"] = today

    # 追加训练记录到 notes（list of entry）
    note_entry = {
        "date": today,
        "verdict": verdict,
        "notes": args.notes,
    }
    if args.drills:
        note_entry["drills"] = [d.strip() for d in args.drills.split(",") if d.strip()]
    if args.wrong:
        note_entry["wrong"] = [w.strip() for w in args.wrong.split(",") if w.strip()]

    # notes 字段约定为 list（2026-05-18 大重构后 schema 已统一）
    existing = q.get("notes")
    if not isinstance(existing, list):
        existing = []  # 兜底：旧数据残留
    existing.append(note_entry)
    q["notes"] = existing

    # 写回 question.json
    _qdata.save_question(q, write_back=True)

    print(
        f"[update_weak] ✓ 编号{q['编号']} [{q['subject']}] {verdict}  "
        f"streak={q['correct_streak']}  weak={q['weak_count']}"
    )


if __name__ == "__main__":
    main()
