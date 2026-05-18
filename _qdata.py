#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_qdata.py · 全局题库数据访问适配器（2026-05-18 大重构后新增）

所有需要读取题库数据的脚本统一通过本模块访问 question.json，
避免脚本里写死路径、避免重复实现 schema 解析。

路径策略（2026-05-18 GitHub 备份重组后）：
    物理位置：工具/data/question.json （git tracked）
    项目根兼容：50-项目/主网自动化竞赛/question.json 是软链 → 工具/data/question.json
    本模块用脚本相对路径定位，跨机器/克隆后无需改路径
"""

import json
from pathlib import Path
from datetime import datetime

# 工具/_qdata.py → 工具/data/question.json
QFILE = (Path(__file__).resolve().parent / "data" / "question.json")


def load():
    """读完整 question.json，返回 {version, total, schema, questions: [...]}"""
    if not QFILE.exists():
        raise FileNotFoundError(f"question.json 不存在: {QFILE}")
    return json.loads(QFILE.read_text(encoding="utf-8"))


def all_questions():
    """返回所有题（list）"""
    return load()["questions"]


def by_subject(subject):
    """按学科过滤"""
    return [q for q in all_questions() if q["subject"] == subject]


def subjects():
    """所有学科名（去重保序）"""
    seen = []
    for q in all_questions():
        if q["subject"] not in seen:
            seen.append(q["subject"])
    return seen


def by_no(no):
    """按全局编号查找单题"""
    for q in all_questions():
        if q["编号"] == int(no):
            return q
    return None


def save_question(updated_question, write_back=True):
    """更新单题：根据 编号 找到并替换。
    write_back=True 立即写回；False 仅返回更新后的 doc 不落盘（批量场景）。
    """
    doc = load()
    for i, q in enumerate(doc["questions"]):
        if q["编号"] == updated_question["编号"]:
            doc["questions"][i] = updated_question
            break
    else:
        raise KeyError(f"找不到编号 {updated_question.get('编号')}")
    doc["last_updated_at"] = datetime.now().isoformat(timespec="seconds")
    if write_back:
        QFILE.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def save_all(doc):
    """整体写回 question.json（用于批量更新场景）"""
    doc["last_updated_at"] = datetime.now().isoformat(timespec="seconds")
    QFILE.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


# ============== 兼容旧 schema 的视图（让旧脚本最少改动接入）==============

def legacy_subject_bank(subject):
    """返回该学科的"伪 题库.json" 数据结构，字段名对齐旧 schema：
    {
      "subject": "操作系统",
      "version": "...",
      "generated": "...",
      "q_count": N,
      "questions": [{"id":"操作系统-001", "subject":..., "title":..., "题面":..., "答案":..., "tags":..., "归属大纲":...}]
    }
    旧脚本（build_exam_data.py 等）可调用本函数得到与旧 题库.json 等价的视图，
    再走原有逻辑（不必感知 question.json）。
    """
    qs = by_subject(subject)
    # 旧 id 格式 = {学科}-{NNN}（学科内顺序号），编号从 1 开始
    questions = []
    for i, q in enumerate(qs, start=1):
        questions.append({
            "id": f"{subject}-{i:03d}",
            "编号": q["编号"],          # 同时保留全局编号
            "subject": q["subject"],
            "title": q["title"],
            "题面": q["题面"],
            "答案": q["答案"],
            "题源": q.get("题源", ""),
            "tags": q.get("tags", []),
            "归属大纲": q.get("归属大纲", ""),
            "deck": q.get("deck", f"实操题::{subject}"),
        })
    doc = load()
    return {
        "subject": subject,
        "version": doc.get("version", "2.0"),
        "generated": doc.get("generated_at", ""),
        "q_count": len(questions),
        "questions": questions,
    }


def legacy_subject_weak(subject):
    """返回该学科的"伪 薄弱点.json" 数据结构（list of weak records）"""
    qs = by_subject(subject)
    weak = []
    for i, q in enumerate(qs, start=1):
        weak.append({
            "id": f"{subject}-{i:03d}",
            "编号": q["编号"],
            "subject": subject,
            "title": q["title"],
            "weak_count": q.get("weak_count", 0),
            "correct_streak": q.get("correct_streak", 0),
            "last_wrong_at": q.get("last_wrong_at"),
            "last_attempt_at": q.get("last_attempt_at"),
            "notes": q.get("notes", ""),
            "tags": q.get("tags", []),
        })
    return weak


if __name__ == "__main__":
    # 自检
    doc = load()
    print(f"question.json 共 {doc['total']} 题")
    print(f"学科: {subjects()}")
    print(f"操作系统 题数: {len(by_subject('操作系统'))}")
