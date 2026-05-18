#!/usr/bin/env python3
"""
🎯每日背诵/<YYYY-MM-DD>.md  →  Anki（绕过 Obsidian-to-Anki 插件，走 AnkiConnect 直推）
+ 自动 setDueDate 到今天（或 frontmatter due_days 指定）
+ 自动归档原训练 JSON 到 70-归档/JSON历史归档/<学科>_<日期>.json

用法：
    python3 push_daily_to_anki.py <md路径> [--dry-run] [--no-archive]

例：
    python3 push_daily_to_anki.py "../../🎯每日背诵/2026-05-16.md"
    python3 push_daily_to_anki.py "../../🎯每日背诵/2026-05-16.md" --dry-run
    python3 push_daily_to_anki.py "../../🎯每日背诵/2026-05-16.md" --no-archive

依赖：AnkiConnect 在 127.0.0.1:8765 运行（Anki 桌面开着即可）

frontmatter 字段（脚本读这些；其他字段忽略）：
    cards-deck:  实操题::操作系统    # 必填；推到哪个牌组
    anki_tags:   [tag1, tag2, ...]   # 必填；全局 tag
    due_days:    0                    # 选填，默认 0 = 今天到期
    source_json: /abs/path/xxx.json   # 选填；填了的话 Source 字段会写文件名 + 题号；
                                      #        归档时也根据它定位原 JSON 文件

⚠️ frontmatter 限制：值必须单行，不含未转义的冒号（脚本不依赖 pyyaml，简单解析）。

行为：
1. 解析 frontmatter
2. 按 "### N." 拆分 MCQ 块，每块需含：题干、A/B/C/D 选项、答案：X、解析：（可选）
3. addNotes 到指定牌组，模型 Obsidian-basic-source（字段 Front/Back/Skeleton/Source）
4. 同牌组按 Front 文本判重 → 重跑安全
5. 新加的卡片批量 setDueDate days=<due_days>
6. 写日志到 .push_history.jsonl（同目录）
7. 默认归档：把 source_json 指向的文件挪到 70-归档/JSON历史归档/<学科>_<日期>.json
   - 学科从 JSON 的 subject 字段读，剥掉 "特训-" 前缀；读不到退回 "未分类"
   - 用 --no-archive 关掉（调试时用）
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ANKI_URL = "http://127.0.0.1:8765"
MODEL = "Obsidian-basic-source"
SCRIPT_DIR = Path(__file__).resolve().parent
LOG_FILE = SCRIPT_DIR / ".push_history.jsonl"
# vault 根 = 99-工作流/anki工具 的上 4 级（anki工具/99-工作流/主网自动化竞赛/50-项目/vault）
VAULT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
# 归档目录：vault 的 70-归档/JSON历史归档/（扁平），文件名 <学科>_<日期>.json
ARCHIVE_ROOT = VAULT_ROOT / "70-归档" / "JSON历史归档"


# ─────── AnkiConnect ───────
def ank(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    res = subprocess.run(
        ["curl", "-s", "-X", "POST", ANKI_URL,
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, check=True)
    r = json.loads(res.stdout)
    if r.get("error"):
        raise RuntimeError(f"AnkiConnect [{action}]: {r['error']}")
    return r["result"]


# ─────── frontmatter ───────
def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm_raw = m.group(1)
    rest = text[m.end():]
    fm = {}
    for line in fm_raw.splitlines():
        if ":" not in line:
            continue
        # 只在第一个冒号处切，保留值里的冒号（比如绝对路径 /Users/.../xx.json 不会断）
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
        else:
            v = v.strip('"').strip("'")
        fm[k] = v
    return fm, rest


# ─────── MCQ 解析（宽松版）───────
def parse_cards(body):
    """
    解析:
        ### N. 题面
        A. opt1
        B. opt2
        C. opt3
        D. opt4   (可选挂 #card #tag)
        答案：X
        X. opt_repeat     ← 可选；缺这行也能解析，Back 用对应字母的原选项文本兜底
        解析：xxx           ← 可选
    """
    cards = []
    blocks = re.split(r"\n(?=### \d+\.)", body)
    for blk in blocks:
        # 题号 + 题干
        head = re.match(r"### (\d+)\.\s*(.+?)\n(.*)", blk, re.DOTALL)
        if not head:
            continue
        num = head.group(1)
        q = head.group(2).strip()
        rest = head.group(3)

        # 抽 A./B./C./D. 选项（每行一项，到第一个非选项行止）
        opt_lines = []
        opt_map = {}   # {"A": "opt1", ...}
        inline_tags = []
        consumed = 0
        for line in rest.splitlines(keepends=True):
            m = re.match(r"([A-D])\.\s+(.+)", line)
            if m:
                letter = m.group(1)
                content = m.group(2).rstrip()
                # 抽 #tag
                tags_in_line = re.findall(r"#(\S+)", content)
                if tags_in_line:
                    inline_tags.extend(tags_in_line)
                    content = re.sub(r"\s*#\S+", "", content).rstrip()
                opt_map[letter] = content
                opt_lines.append(f"{letter}. {content}")
                consumed += len(line)
            else:
                if opt_lines:
                    break
                consumed += len(line)
        tail = rest[consumed:]

        if len(opt_map) < 2:
            print(f"  ⚠️  卡{num}: 选项不足 ({len(opt_map)} 个)，跳过")
            continue

        # 答案
        ans_m = re.search(r"答案[:：]\s*([A-D])", tail)
        if not ans_m:
            print(f"  ⚠️  卡{num}: 没找到「答案：X」行，跳过")
            continue
        ans = ans_m.group(1)

        # 解析（可选）
        exp_m = re.search(r"解析[:：]\s*(.+?)(?=\n\n|\n### |\Z)", tail, re.DOTALL)
        exp = exp_m.group(1).strip() if exp_m else ""

        # 答案文本：优先答案行下方的 "X. xxx" 重复行；否则从 opt_map 兜底
        ans_text_m = re.search(rf"\n{ans}\.\s*(.+)", tail)
        ans_text = ans_text_m.group(1).strip() if ans_text_m else opt_map.get(ans, "")

        clean_tags = [t for t in inline_tags if t != "card"]

        front_html = "<p>" + q + "<br>" + "<br>".join(opt_lines) + "</p>"
        back_html = f"答案：{ans}<br>{ans_text}<br>解析：{exp}".strip()

        cards.append({
            "num": num,
            "front": front_html,
            "back": back_html,
            "inline_tags": clean_tags,
        })
    return cards


def build_source(source_json, md_name, num):
    """Source 字段：优先用 frontmatter source_json 的文件名（去 .json）+ 题号；
    没填就退回 MD 文件名 + 题号。"""
    if source_json:
        stem = Path(source_json).stem  # 训练_特训-操作系统_2026-05-15-2
        return f"{stem} · {md_name} 第{num}题"
    return f"{md_name} 第{num}题"


def _extract_subject(src_path):
    """从 JSON 的 subject 字段抽学科，剥 '特训-' 前缀；读失败回 '未分类'。"""
    try:
        data = json.loads(src_path.read_text(encoding="utf-8"))
        subj = (data.get("subject") or "").strip()
        if not subj:
            return "未分类"
        for prefix in ("特训-", "训练-", "练习-"):
            if subj.startswith(prefix):
                subj = subj[len(prefix):]
                break
        # 防御性清洗：不允许目录分隔符
        return subj.replace("/", "_").replace("\\", "_") or "未分类"
    except Exception:
        return "未分类"


def _extract_date(src_path: Path) -> str:
    """从文件名抽 YYYY-MM-DD；抽不到回退到 mtime 日期。"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", src_path.name)
    if m:
        return m.group(1)
    return datetime.fromtimestamp(src_path.stat().st_mtime).strftime("%Y-%m-%d")


def _next_available(target_dir: Path, subject: str, date_str: str) -> Path:
    """目标 <学科>_<日期>.json；撞名递增 -2/-3/-4…"""
    base = target_dir / f"{subject}_{date_str}.json"
    if not base.exists():
        return base
    i = 2
    while True:
        cand = target_dir / f"{subject}_{date_str}-{i}.json"
        if not cand.exists():
            return cand
        i += 1


def archive_source_json(source_json, dry_run=False):
    """归档原训练 JSON → JSON历史归档/<学科>_<日期>.json；撞名加 -2/-3。"""
    if not source_json:
        print("⏭  归档：frontmatter 无 source_json，跳过")
        return None
    src = Path(source_json).expanduser()
    if not src.exists():
        print(f"⏭  归档：源文件不存在 {src}")
        return None
    subject = _extract_subject(src)
    date_str = _extract_date(src)
    if not ARCHIVE_ROOT.exists():
        if dry_run:
            print(f"   [dry-run] 会创建归档目录 {ARCHIVE_ROOT}")
        else:
            ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    dst = _next_available(ARCHIVE_ROOT, subject, date_str)
    if dry_run:
        print(f"   [dry-run] 会移动 {src.name} → {dst.name}")
        return str(dst)
    shutil.move(str(src), str(dst))
    rel = dst.relative_to(VAULT_ROOT) if dst.is_relative_to(VAULT_ROOT) else dst
    print(f"📦 已归档原 JSON → {rel}")
    return str(dst)


def write_log(record):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─────── main ───────
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md_path", help="🎯每日背诵/YYYY-MM-DD.md 的路径")
    ap.add_argument("--dry-run", action="store_true", help="只解析+查重，不真推到 Anki")
    ap.add_argument("--no-archive", action="store_true", help="关掉自动归档（默认推完后把 source_json 移到 70-归档/JSON历史归档/<学科>_<日期>.json）")
    args = ap.parse_args()

    md_path = Path(args.md_path).expanduser().resolve()
    if not md_path.exists():
        print(f"❌ 文件不存在: {md_path}")
        sys.exit(1)
    text = md_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    deck = fm.get("cards-deck", "实操题::操作系统")
    fm_tags = fm.get("anki_tags") or []
    if isinstance(fm_tags, str):
        fm_tags = [fm_tags]
    try:
        due_days = int(fm.get("due_days", 0))
    except (TypeError, ValueError):
        due_days = 0
    source_json = fm.get("source_json", "")

    print(f"📄 文件: {md_path.name}")
    print(f"📚 牌组: {deck}")
    print(f"🏷  全局 tags: {fm_tags}")
    print(f"⏰ 到期天数 (0=今天): {due_days}")
    print(f"🔗 source_json: {source_json or '(未填)'}")
    if args.dry_run:
        print("🧪 模式: DRY-RUN（不会真的推）")

    cards = parse_cards(body)
    print(f"🃏 解析出 {len(cards)} 张卡")
    if not cards:
        print("❌ 没解析出任何卡片，退出")
        sys.exit(1)

    # 查重（按 Front 纯文本）
    try:
        ank("createDeck", deck=deck)
        existing = ank("findNotes", query=f'deck:"{deck}"')
    except RuntimeError as e:
        print(f"❌ AnkiConnect 连不上: {e}")
        sys.exit(2)

    existing_fronts = set()
    if existing:
        for i in range(0, len(existing), 100):
            infos = ank("notesInfo", notes=existing[i:i+100])
            for n in infos:
                f = n.get("fields", {}).get("Front", {}).get("value", "")
                plain = re.sub(r"<[^>]+>", "", f).strip()
                existing_fronts.add(plain)

    new_notes = []
    skipped = []
    for c in cards:
        plain_front = re.sub(r"<[^>]+>", "", c["front"]).strip()
        if plain_front in existing_fronts:
            skipped.append(c["num"])
            continue
        tags = list(dict.fromkeys(fm_tags + c["inline_tags"]))
        new_notes.append({
            "deckName": deck,
            "modelName": MODEL,
            "fields": {
                "Front": c["front"],
                "Back": c["back"],
                "Skeleton": "",
                "Source": build_source(source_json, md_path.name, c["num"]),
            },
            "tags": tags,
            "options": {"allowDuplicate": False},
        })

    if skipped:
        print(f"  · 跳过重复 {len(skipped)} 张: {','.join(skipped)}")

    if not new_notes:
        print("✅ 没有新卡要推（全部已存在）")
        return

    if args.dry_run:
        print(f"\n🧪 [dry-run] 会推 {len(new_notes)} 张到 {deck}")
        print(f"   首张预览:")
        print(f"     Front: {new_notes[0]['fields']['Front'][:120]}...")
        print(f"     Back:  {new_notes[0]['fields']['Back'][:120]}...")
        print(f"     Source:{new_notes[0]['fields']['Source']}")
        print(f"     Tags:  {new_notes[0]['tags']}")
        if not args.no_archive:
            archive_source_json(source_json, dry_run=True)
        return

    print(f"⬆️  推送 {len(new_notes)} 张到 Anki...")
    ids = ank("addNotes", notes=new_notes)
    added = [i for i in ids if i is not None]
    failed_idx = [i for i, x in enumerate(ids) if x is None]
    print(f"   成功 {len(added)} 张 / 失败 {len(failed_idx)} 张")
    if failed_idx:
        for idx in failed_idx:
            f = new_notes[idx]
            preview = re.sub(r"<[^>]+>", " ", f["fields"]["Front"])[:60]
            print(f"   ❌ 失败: {preview}... (常见原因: 字段缺失 / duplicate / 标签非法)")

    if not added:
        write_log({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "md": str(md_path),
            "deck": deck,
            "added": 0,
            "skipped": len(skipped),
            "failed": len(failed_idx),
        })
        return

    # setDueDate
    notes_info = ank("notesInfo", notes=added)
    card_ids = []
    for n in notes_info:
        card_ids.extend(n.get("cards", []))

    if card_ids and due_days >= 0:
        print(f"📅 setDueDate cards={len(card_ids)} days={due_days}")
        ank("setDueDate", cards=card_ids, days=str(due_days))
        print(f"✅ 到期日设到 今天起 +{due_days} 天")

    # 写日志
    write_log({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "md": str(md_path),
        "deck": deck,
        "added": len(added),
        "skipped": len(skipped),
        "failed": len(failed_idx),
        "noteIds": added,
        "source_json": source_json,
    })

    # 归档（默认开；--no-archive 关）
    if not args.no_archive:
        archive_source_json(source_json, dry_run=False)

    print(f"\n🎉 完成。本地 Anki 立即可背；如开了 AnkiWeb / 手机同步，自己在 Anki 里点一下同步。")


if __name__ == "__main__":
    main()
