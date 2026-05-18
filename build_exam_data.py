#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_exam_data.py v5 · 2026-05-18 大重构后重写
================================================

输入：
  question.json     全局题库（通过 _qdata 适配器读）
  outline.json      PDF 大纲结构化版（工具/web/outline.json）

输出：
  工具/web/exam_data.json  网页用的层级数据
  结构：
  {
    "version": "v0.5",
    "generated": "YYYY-MM-DD",
    "tag_prefix": "KP::",
    "subjects": [
      { "name": "操作系统", "key": "linux", "q_count": N,
        "sections": [
          { "code": "1.1", "name": "...", "q_count": M, "kps": [
              { "code": "1.1.1", "name": "...", "q_count": K,
                "questions": [{"编号":N, "title":..., "题面":..., "答案":..., "归属大纲":..., "tags":[...], "题源":...}] }
          ]}
        ]}
    ]
  }

设计要点：
  - 不再依赖任何 题库.json / 薄弱点.json / 大纲索引.json
  - 题归到 outline.kp 的依据：question["归属大纲"] == kp["code"]
  - 学科未在 outline 出现的（如 竞赛环境）：输出一个特殊 "subject" 容器 sections=[]，questions 直挂
  - "归属大纲" 为空的题：归到该 subject 容器的 _unsorted 占位 section
"""

import json
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qdata

ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛")
WEB = ROOT / "工具/web"
OUTLINE_FILE = WEB / "outline.json"

# subject → key（css class，对齐 index.html）
SUBJ_KEYS = {
    "操作系统": "os",
    "数据库": "db",
    "基础平台": "platform",
    "系统平台": "platform",
    "稳态监控": "stable",
    "综合智能告警": "alert",
    "网络分析": "net",
    "调度数据网": "dispatch",
    "竞赛环境": "lab",
}


def question_view(q):
    """从 question.json 单题派生网页用的视图"""
    return {
        "编号": q["编号"],
        "title": q.get("title", ""),
        "题面": q.get("题面", ""),
        "答案": q.get("答案", ""),
        "题源": q.get("题源", ""),
        "tags": q.get("tags", []),
        "归属大纲": q.get("归属大纲", ""),
        "deck": q.get("deck", ""),
        "weak_count": q.get("weak_count", 0),
        "correct_streak": q.get("correct_streak", 0),
    }


def main():
    outline = json.loads(OUTLINE_FILE.read_text(encoding="utf-8"))
    questions = _qdata.all_questions()

    # 按 归属大纲 KP code 索引题目
    by_kp = {}
    unsorted_by_subject = {}  # 学科 → 无 KP 题
    for q in questions:
        code = q.get("归属大纲")
        if code:
            by_kp.setdefault(code, []).append(q)
        else:
            unsorted_by_subject.setdefault(q["subject"], []).append(q)

    # 按 outline 章节展开，同时收集每个 outline category 的"承载学科"
    # 一个 category 可能有多个 subject（如基础平台/系统平台 都对应 D6.0）
    subjects_list = []
    seen_subjects_in_outline = set()
    for cat in outline["categories"]:
        cat_subjects = cat.get("subjects", []) or []
        # 该章节聚集的所有题 = 该章 KP 下所有 question.json 题
        sections_out = []
        cat_total = 0
        for sec in cat["sections"]:
            kps_out = []
            sec_total = 0
            for kp in sec["kps"]:
                qs = by_kp.get(kp["code"], [])
                kps_out.append({
                    "code": kp["code"],
                    "name": kp["name"],
                    "desc": kp.get("desc", ""),
                    "q_count": len(qs),
                    "questions": [question_view(q) for q in qs],
                })
                sec_total += len(qs)
            sections_out.append({
                "code": sec["code"],
                "name": sec["name"],
                "q_count": sec_total,
                "kps": kps_out,
            })
            cat_total += sec_total

        subjects_list.append({
            "name": cat["name"],
            "ordinal": cat.get("ordinal", ""),
            "id": cat.get("id", ""),
            "key": SUBJ_KEYS.get(cat_subjects[0], "os") if cat_subjects else "misc",
            "subjects": cat_subjects,  # question.json 中归属本章节的 subject 列表
            "q_count": cat_total,
            "sections": sections_out,
        })
        for s in cat_subjects:
            seen_subjects_in_outline.add(s)

    # 处理 outline 没覆盖的学科（竞赛环境等）
    all_subjects = _qdata.subjects()
    for s in all_subjects:
        if s in seen_subjects_in_outline:
            continue
        qs = [q for q in questions if q["subject"] == s]
        subjects_list.append({
            "name": s,
            "ordinal": "外",
            "id": f"misc-{SUBJ_KEYS.get(s, 'misc')}",
            "key": SUBJ_KEYS.get(s, "misc"),
            "subjects": [s],
            "q_count": len(qs),
            "sections": [{
                "code": "0.0",
                "name": "大纲外",
                "q_count": len(qs),
                "kps": [{
                    "code": "0.0.0",
                    "name": "未对齐 PDF 大纲",
                    "desc": "本学科未在系统实操学习脑图.pdf 中出现",
                    "q_count": len(qs),
                    "questions": [question_view(q) for q in qs],
                }],
            }],
        })

    out = {
        "version": "v0.5",
        "generated": str(date.today()),
        "tag_prefix": outline.get("tag_prefix", "KP::"),
        "source": "question.json + outline.json",
        "subjects": subjects_list,
    }
    target = WEB / "exam_data.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 写入: {target}  ({target.stat().st_size} bytes)")
    for s in subjects_list:
        print(f"  {s['ordinal']}. {s['name']}: {s['q_count']} 题")


if __name__ == "__main__":
    main()
