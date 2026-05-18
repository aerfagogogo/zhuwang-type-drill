#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doctor.py · 主网自动化竞赛系统体检脚本（2026-05-18 大重构后新增）

作用：替代人工 grep README 防漂移。每次 refresh_exam.sh 跑之前先 quick 体检。

模式：
  python3 doctor.py --quick    快速体检（关键路径 + 关键文件存在性）
  python3 doctor.py --full     深度体检（含 question.json 与 outline.json 一致性 / Anki 牌组等）
  python3 doctor.py            默认 --quick

退出码：
  0 全部通过
  1 有 ⚠️ 警告但可继续
  2 有 ❌ 致命错误，refresh_exam.sh 应停止
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间")
PROJECT = ROOT / "50-项目/主网自动化竞赛"
TOOLS = PROJECT / "工具"
WEB = TOOLS / "web"
SKILLS = ROOT / ".claude/skills"

OK = "✅"
WARN = "⚠️"
ERR = "❌"

errors = []
warnings = []
checks_passed = 0


def check(label, ok, msg="", level="error"):
    """level: error / warn"""
    global checks_passed
    if ok:
        print(f"  {OK} {label}")
        checks_passed += 1
    elif level == "warn":
        print(f"  {WARN} {label} — {msg}")
        warnings.append((label, msg))
    else:
        print(f"  {ERR} {label} — {msg}")
        errors.append((label, msg))


def quick(exit_at_end=True):
    """运行 quick 体检。
    exit_at_end=True → 末尾 summary() 后 sys.exit；
    exit_at_end=False → 仅打印汇总，让调用方决定如何收尾（full 模式会用到）。
    """
    print("\n🩺 === doctor.py · quick 体检 ===\n")

    print("[1] 核心数据文件")
    qfile = TOOLS / "data" / "question.json"
    check("question.json 存在", qfile.exists(), f"缺 {qfile}")
    if qfile.exists():
        try:
            q = json.loads(qfile.read_text(encoding="utf-8"))
            qs = q.get("questions", [])
            check(f"question.json 题数 = {len(qs)}", len(qs) > 0, "题数为 0")
            # 字段一致性
            if qs:
                fields_set = {tuple(sorted(x.keys())) for x in qs}
                check(f"字段一致性 ({len(fields_set)} 种组合)", len(fields_set) == 1, "字段不统一")
                # 必备字段
                required = {"编号", "subject", "deck", "title", "题面", "答案", "tags", "归属大纲",
                            "weak_count", "correct_streak", "last_wrong_at", "last_attempt_at", "notes"}
                missing = required - set(qs[0].keys())
                check(f"必备字段齐全 ({len(required)} 项)", not missing, f"缺字段 {missing}")
        except json.JSONDecodeError as e:
            check("question.json 可解析", False, f"JSON 解析失败: {e}")

    outline = WEB / "outline.json"
    check("outline.json 存在", outline.exists())

    print("\n[2] 关键脚本路径")
    for name in [
        "refresh_exam.sh",
        "build_subject_bank.py",
        "build_exam_data.py",
        "build_progress_data.py",
        "update_weak.py",
        "anki/push_exam_to_anki.py",
        "doctor.py",
    ]:
        p = TOOLS / name
        check(f"工具/{name}", p.exists())

    print("\n[3] 网页文件")
    for name in ["index.html", "training-center.html", "exam.html", "drill.html"]:
        p = WEB / name
        check(f"web/{name}", p.exists())

    print("\n[4] 现行 skill 文件（不应有已归档的）")
    archived = ["念能力训练.md", "竞赛训练.md", "错题标注.md",
                "杭州培训-出主观题.md", "杭州培训-知识点.md",
                "杭州培训-训练方法.md", "杭州培训-题集.md"]
    for name in archived:
        p = SKILLS / name
        check(f"已归档 {name} 不存在", not p.exists(),
              f"已归档 skill 仍残留在 .claude/skills/，2026-05-18 协议要求删除",
              level="warn")
    # 必备 skill
    for name in ["操作系统训练.md", "达梦训练.md", "竞赛环境训练.md", "变式训练.md", "出模拟卷.md"]:
        p = SKILLS / name
        check(f"必备 skill {name}", p.exists())

    print("\n[5] refresh_exam.sh 内部路径引用")
    rs = (TOOLS / "refresh_exam.sh").read_text(encoding="utf-8")
    bad = re.findall(r"anki工具/", rs)
    check("refresh_exam.sh 无旧路径 anki工具/", not bad,
          f"refresh_exam.sh 仍引用 anki工具/ ({len(bad)} 处)")

    print("\n[6] question.json schema 健康度")
    qfile = TOOLS / "data" / "question.json"
    if qfile.exists():
        try:
            q = json.loads(qfile.read_text(encoding="utf-8"))
            qs = q.get("questions", [])
            non_list_notes = [x["编号"] for x in qs if not isinstance(x.get("notes"), list)]
            check(f"notes 字段全部为 list ({len(qs)} 题)", not non_list_notes,
                  f"{len(non_list_notes)} 题 notes 不是 list",
                  level="error")
        except Exception:
            pass

    if exit_at_end:
        summary_and_exit()


def full():
    quick(exit_at_end=False)
    print("\n🩺 === full 体检（深度）===\n")

    print("[F1] question.json 与 outline.json 一致性")
    qfile = TOOLS / "data" / "question.json"
    ofile = WEB / "outline.json"
    if qfile.exists() and ofile.exists():
        q = json.loads(qfile.read_text(encoding="utf-8"))
        o = json.loads(ofile.read_text(encoding="utf-8"))
        valid_codes = set()
        for cat in o["categories"]:
            for sec in cat["sections"]:
                for kp in sec["kps"]:
                    valid_codes.add(kp["code"])
        qs = q.get("questions", [])
        legal = sum(1 for x in qs if x["归属大纲"] in valid_codes)
        empty = sum(1 for x in qs if not x["归属大纲"])
        illegal = len(qs) - legal - empty
        check(f"归属大纲合法 {legal} / 空 {empty} / 非法 {illegal}",
              illegal == 0,
              f"{illegal} 题归属大纲非 outline 合法 KP code")

    print("\n[F2] 学科分布合理性")
    if qfile.exists():
        from collections import Counter
        q = json.loads(qfile.read_text(encoding="utf-8"))
        sub = Counter(x["subject"] for x in q["questions"])
        for s, n in sub.most_common():
            check(f"  {s}: {n} 题", n > 0)

    summary_and_exit()


def summary_and_exit():
    print(f"\n=== 体检结果 ===")
    print(f"  通过: {checks_passed}")
    print(f"  警告: {len(warnings)}")
    print(f"  错误: {len(errors)}")
    if errors:
        print(f"\n{ERR} 致命错误：")
        for label, msg in errors:
            print(f"  - {label}: {msg}")
        sys.exit(2)
    if warnings:
        print(f"\n{WARN} 警告（不阻断）：")
        for label, msg in warnings:
            print(f"  - {label}: {msg}")
        sys.exit(1)
    print(f"\n{OK} 全部通过")
    sys.exit(0)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--quick"
    if mode == "--full":
        full()
    else:
        quick()
