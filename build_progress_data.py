#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_progress_data.py v3 · 2026-05-18 大重构后重写
=====================================================

输入：
  question.json     全局题库（含 weak_count/correct_streak/last_wrong_at/last_attempt_at/notes）
  AnkiConnect       可选；GUI 学科卡片状态（reps/ease/lapses）

输出：
  工具/web/progress_data.json

进度数据来源（双轨）：
  - CLI 学科（操作系统/数据库/竞赛环境）：question.json 的 weak 字段（CV 训练写入）
  - GUI 学科（系统平台/稳态监控/...）：AnkiConnect 读 `实操题::{学科}` 卡片状态
    - Anki 不可用时回退到 question.json 的 weak 字段

输出 schema：
{
  "version": "v0.3",
  "generated": "YYYY-MM-DD",
  "subjects": {
    "操作系统": {"total":58, "attempted":7, "passed":0, "wrong_pending":3, "last_attempt_at":"...", "source":"weak"}
  },
  "questions": {
    "{编号}": {"weak_count":..., "correct_streak":..., "last_verdict":..., "source":"weak"|"anki", ...}
  }
}
"""

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qdata

ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛")
WEB = ROOT / "工具/web"
ANKI_URL = "http://127.0.0.1:8765"

CLI_SUBJECTS = {"操作系统", "数据库", "竞赛环境"}
PASS_STREAK = 3
ANKI_PASS_REPS = 3
ANKI_PASS_EASE = 2500


def ank(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", ANKI_URL,
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        raise RuntimeError("curl failed")
    res = json.loads(r.stdout)
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect [{action}]: {res['error']}")
    return res["result"]


def anki_available():
    try:
        ank("version")
        return True
    except Exception:
        return False


def get_last_verdict(notes):
    if not isinstance(notes, list) or not notes:
        return None
    last = notes[-1]
    if isinstance(last, dict):
        if "verdict" in last:
            return last["verdict"]
        if "wrong" in last:
            return "❌" if last["wrong"] else "✅"
    return None


def process_weak(subject, qs, q_map, summary):
    total = len(qs)
    attempted = passed = wrong_pending = 0
    latest = None

    for q in qs:
        ws = int(q.get("correct_streak", 0) or 0)
        wc = int(q.get("weak_count", 0) or 0)
        laa = q.get("last_attempt_at")
        attempted_q = laa is not None
        passed_q = ws >= PASS_STREAK

        q_map[str(q["编号"])] = {
            "编号": q["编号"],
            "subject": subject,
            "title": q.get("title", ""),
            "last_verdict": get_last_verdict(q.get("notes")),
            "weak_count": wc,
            "correct_streak": ws,
            "last_attempt_at": laa,
            "attempted": attempted_q,
            "passed": passed_q,
            "source": "weak",
        }
        if attempted_q:
            attempted += 1
            if laa and (latest is None or laa > latest):
                latest = laa
        if passed_q:
            passed += 1
        if wc > 0 and not passed_q:
            wrong_pending += 1

    summary[subject] = {
        "total": total, "attempted": attempted,
        "passed": passed, "wrong_pending": wrong_pending,
        "last_attempt_at": latest, "source": "weak",
    }


def process_anki(subject, qs, q_map, summary):
    """从 AnkiConnect 读卡片状态。Front 里用 [#编号] 标识题目。"""
    deck = f"实操题::{subject}"
    try:
        note_ids = ank("findNotes", query=f'deck:"{deck}"')
    except Exception as e:
        print(f"  [!] Anki {deck}: {e}")
        return False
    if not note_ids:
        summary[subject] = {"total": len(qs), "attempted": 0, "passed": 0,
                            "wrong_pending": 0, "last_attempt_at": None, "source": "anki"}
        return True

    notes_info = ank("notesInfo", notes=note_ids)
    card_ids = ank("findCards", query=f'deck:"{deck}"')
    cards_info = ank("cardsInfo", cards=card_ids)
    card_by_note = {c["note"]: c for c in cards_info}

    # 建立 编号 → q 索引
    q_by_no = {q["编号"]: q for q in qs}

    attempted = passed = wrong_pending = 0
    counted_nos = set()
    for note in notes_info:
        nid = note["noteId"]
        front = note["fields"].get("Front", {}).get("value", "")
        m = re.search(r"\[#(\d+)\]", front)
        if not m:
            continue
        no = int(m.group(1))
        counted_nos.add(no)
        card = card_by_note.get(nid, {})
        reps = card.get("reps", 0)
        ease = card.get("factor", 0)
        lapses = card.get("lapses", 0)
        attempted_q = reps > 0
        passed_q = reps >= ANKI_PASS_REPS and ease >= ANKI_PASS_EASE
        wrong_pending_q = lapses > 0 and not passed_q

        q_map[str(no)] = {
            "编号": no,
            "subject": subject,
            "title": q_by_no.get(no, {}).get("title", ""),
            "reps": reps, "ease_factor": ease, "lapses": lapses,
            "attempted": attempted_q, "passed": passed_q,
            "source": "anki",
        }
        if attempted_q: attempted += 1
        if passed_q: passed += 1
        if wrong_pending_q: wrong_pending += 1

    summary[subject] = {
        "total": len(qs), "attempted": attempted, "passed": passed,
        "wrong_pending": wrong_pending, "last_attempt_at": None, "source": "anki",
    }
    return True


def main():
    use_anki = anki_available()
    print("Anki ✅ — GUI 学科走 AnkiConnect" if use_anki else "Anki ❌ — 全部回退到 weak 字段")

    summary = {}
    q_map = {}
    for subject in _qdata.subjects():
        qs = _qdata.by_subject(subject)
        if use_anki and subject not in CLI_SUBJECTS:
            ok = process_anki(subject, qs, q_map, summary)
            if not ok:
                process_weak(subject, qs, q_map, summary)
        else:
            process_weak(subject, qs, q_map, summary)

    out = {
        "version": "v0.3",
        "generated": str(date.today()),
        "subjects": summary,
        "questions": q_map,
    }
    target = WEB / "progress_data.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 写入: {target}")
    for n, s in summary.items():
        src = "📋" if s["source"] == "weak" else "🎴"
        print(f"  {src} {n}: {s['attempted']}/{s['total']} 已练 / {s['passed']} 过关 / {s['wrong_pending']} 待消化")


if __name__ == "__main__":
    main()
