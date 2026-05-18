#!/usr/bin/env python3
# ⚠️ DEPRECATED · 2026-05-18 大重构后已废弃
# ============================================================
# 本脚本依赖的「学科/题库.json」和「学科/薄弱点.json」已被合并到全局 question.json，
# 不再需要 hydrate 同步动作。新增题直接通过 import_source.py 录入即可。
# 跑本脚本会失败（找不到旧 json 文件）。已加入 sys.exit 兜底防误调。
# 历史数据已合并进 question.json，本脚本仅作历史代码留档。
# ============================================================
import sys
print("❌ init_weak.py 已废弃（2026-05-18 大重构后）。"
      "新方案下 question.json 是单一 SSOT，无需 hydrate。"
      "如需录入新题用 工具/import_source.py。")
sys.exit(2)

"""
init_weak.py — 用「题库.json」hydrate「薄弱点.json」

设计意图
========
- 题库.json 是 SSOT（派生自 MD），薄弱点.json 跟随它的 id 集合
- 题库新增 id（你录入了新题）→ 自动给薄弱点补一条初始记录
- 题库删除 id（题被移除）→ 薄弱点对应记录打 `orphan: true`，**保留历史训练记录不删**
- 薄弱点.json 不存在 → 用题库全量初始化（新学科第一次开训练）

用法
====
    python3 init_weak.py <学科>              # 单学科
    python3 init_weak.py --all              # 全部学科
    python3 init_weak.py 数据库 --dry-run    # 看会变什么，不写盘

初始记录 schema
==============
{
  "id": "数据库-001",
  "subject": "数据库",
  "title": "...",
  "md_path": "001-...md",
  "weak_count": 0,
  "correct_streak": 0,
  "last_wrong_at": null,
  "last_attempt_at": null,
  "notes": []
}

输出报告
========
每学科一行：新增 N / orphan M / 总计 T
"""
import argparse
import json
import sys
from pathlib import Path

VAULT_ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间")
TIKAN = VAULT_ROOT / "50-项目/主网自动化竞赛/04实操题集"

SKIP_DIRS = {"源文件", "模拟卷"}


# ─────────────────────────────────────────────────────────────
# 单学科处理
# ─────────────────────────────────────────────────────────────
def hydrate_one(subject: str, dry_run: bool = False) -> int:
    subj_dir = TIKAN / subject
    bank_path = subj_dir / "题库.json"
    weak_path = subj_dir / "薄弱点.json"

    if not bank_path.exists():
        print(f"[!] {subject}: 题库.json 不存在，请先跑 build_subject_bank.py", file=sys.stderr)
        return 1

    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    bank_questions = bank["questions"]
    bank_ids = {q["id"] for q in bank_questions}
    bank_index = {q["id"]: q for q in bank_questions}

    # 读现有薄弱点（不存在则空列表）
    if weak_path.exists():
        weak = json.loads(weak_path.read_text(encoding="utf-8"))
    else:
        weak = []
    weak_ids = {e["id"] for e in weak}
    weak_index = {e["id"]: e for e in weak}

    # 1) 题库有、薄弱点没有 → 新增初始记录
    to_add_ids = bank_ids - weak_ids
    added = 0
    for qid in sorted(to_add_ids):
        q = bank_index[qid]
        new_entry = {
            "id": qid,
            "subject": subject,
            "title": q.get("title", ""),
            "md_path": q.get("md_path", ""),
            "weak_count": 0,
            "correct_streak": 0,
            "last_wrong_at": None,
            "last_attempt_at": None,
            "notes": [],
        }
        weak.append(new_entry)
        added += 1

    # 2) 薄弱点有、题库没有 → 标记 orphan（保留训练记录）
    to_orphan_ids = weak_ids - bank_ids
    orphaned = 0
    for qid in to_orphan_ids:
        if not weak_index[qid].get("orphan"):
            weak_index[qid]["orphan"] = True
            orphaned += 1

    # 3) 反向操作：以前是 orphan 的，现在题库又有了 → 清掉 orphan 标记
    restored = 0
    for qid in (bank_ids & weak_ids):
        if weak_index[qid].pop("orphan", False):
            restored += 1

    # 排序：按 id 升序，方便人看
    weak.sort(key=lambda e: e["id"])

    if not dry_run:
        weak_path.write_text(
            json.dumps(weak, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    tag = "(dry-run)" if dry_run else ""
    print(
        f"  ✓ {subject}: 新增 {added} / orphan {orphaned} / 恢复 {restored} / 总计 {len(weak)}  {tag}"
    )
    return 0


# ─────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="用 题库.json hydrate 薄弱点.json")
    parser.add_argument("subject", nargs="?", help="学科名（如：数据库）；--all 时省略")
    parser.add_argument("--all", action="store_true", help="处理全部学科")
    parser.add_argument("--dry-run", action="store_true", help="只看变化不写盘")
    args = parser.parse_args()

    if args.all:
        subjects = [
            d.name for d in sorted(TIKAN.iterdir())
            if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith(".")
            and (d / "题库.json").exists()
        ]
        print(f"[init_weak] hydrate {len(subjects)} 个学科")
        rc = 0
        for s in subjects:
            rc |= hydrate_one(s, dry_run=args.dry_run)
        sys.exit(rc)
    elif args.subject:
        sys.exit(hydrate_one(args.subject, dry_run=args.dry_run))
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
