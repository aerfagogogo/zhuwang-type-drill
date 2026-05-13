#!/usr/bin/env python3
"""
惩罚清单工具:
  python3 punishment.py gen <subject>   生成清单（默认 3 遍）
  python3 punishment.py gen <subject> 5 生成清单（5 遍）
  python3 punishment.py check <subject> 检查进度；全勾完 → 归档 + 更新薄弱点
"""
import json, sys, re, datetime
from pathlib import Path
from collections import OrderedDict

ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛/04实操题集")
PASS_THRESHOLD = 3   # correct_streak >= 此值视为过关，不入清单

def path_for(subject):
    base = ROOT / subject
    return {
        "weak": base / "薄弱点.json",
        "list": base / "惩罚清单.md",
        "arch_dir": base / "惩罚归档",
    }

def gen(subject, reps=3):
    p = path_for(subject)
    if not p["weak"].exists():
        print(f"找不到 {p['weak']}"); return
    data = json.load(p["weak"].open(encoding="utf-8"))

    # 收集所有未过关条目的 drills，按 (id, drill) dedup
    items = OrderedDict()  # key=(id,drill) -> {entry, drill, point}
    for entry in data:
        if entry.get("correct_streak", 0) >= PASS_THRESHOLD:
            continue
        for note in entry.get("notes", []):
            wrongs = note.get("wrong", [])
            drills = note.get("drills", [])
            for i, drill in enumerate(drills):
                point = wrongs[i] if i < len(wrongs) else "(未注明)"
                key = (entry["id"], drill)
                if key not in items:
                    items[key] = {"id": entry["id"], "title": entry["title"],
                                  "drill": drill, "point": point}

    if not items:
        p["list"].write_text("# 惩罚清单\n\n暂无未过关条目，去刷新题吧。\n", encoding="utf-8")
        print("无未过关条目，已写空清单")
        return

    # 按 id 分组
    by_id = OrderedDict()
    for v in items.values():
        by_id.setdefault(v["id"], []).append(v)

    today = datetime.date.today().isoformat()
    lines = [
        "---", f"tags: [惩罚清单, {subject}]", f"created: {today}",
        f"reps: {reps}", "status: 进行中", "---", "",
        f"# 惩罚清单 · {subject}", "",
        f"> 每条盲敲 **{reps} 遍**，完成勾上。**全勾完跟 Claudian 说「惩罚检查」**。", "",
    ]
    total = 0
    for eid, lst in by_id.items():
        title = lst[0]["title"]
        lines += [f"## {eid}", f"*{title}*", ""]
        for k, v in enumerate(lst, 1):
            lines += [f"### 错点 {k}：{v['point']}"]
            for _ in range(reps):
                lines.append(f"- [ ] `{v['drill']}`")
                total += 1
            lines.append("")

    lines += ["---", f"进度：0/{total}", ""]
    p["list"].write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 {p['list']} （{total} 项）")

def check(subject):
    p = path_for(subject)
    if not p["list"].exists():
        print("没有清单，先 gen"); return
    text = p["list"].read_text(encoding="utf-8")
    done = len(re.findall(r"^- \[x\] ", text, re.MULTILINE | re.IGNORECASE))
    todo = len(re.findall(r"^- \[ \] ", text, re.MULTILINE))
    total = done + todo
    if total == 0:
        print("清单是空的"); return
    print(f"进度：{done}/{total}")
    if todo > 0:
        # 列出未完成的命令（dedup）
        undone = re.findall(r"^- \[ \] `(.+?)`", text, re.MULTILINE)
        uniq = list(dict.fromkeys(undone))
        print(f"\n剩 {todo} 条未勾，涉及命令：")
        for c in uniq[:10]:
            print(f"  - {c}")
        return

    # 全勾完 → 归档 + 更新薄弱点
    p["arch_dir"].mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()
    arch = p["arch_dir"] / f"惩罚清单_{today}.md"
    arch.write_text(text.replace("status: 进行中", f"status: 已完成 {today}"), encoding="utf-8")
    p["list"].unlink()

    data = json.load(p["weak"].open(encoding="utf-8"))
    affected = re.findall(r"^## (\S+)$", text, re.MULTILINE)
    for entry in data:
        if entry["id"] in affected:
            entry["weak_count"] = max(0, entry.get("weak_count", 0) - 1)
            entry.setdefault("punishment_done", []).append(today)
    json.dump(data, p["weak"].open("w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"\n✅ 全部完成！\n  归档: {arch.name}\n  薄弱点 weak_count -1: {affected}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cmd, subject = sys.argv[1], sys.argv[2]
    if cmd == "gen":
        reps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        gen(subject, reps)
    elif cmd == "check":
        check(subject)
    else:
        print(__doc__)
