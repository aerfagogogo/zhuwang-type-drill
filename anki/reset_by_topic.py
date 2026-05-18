#!/usr/bin/env python3
"""
按主题/关键词把 Anki 卡推到今天到期 (setDueDate days=0)。
学习历史完整保留，只动到期日 = 你打开 Anki 立刻看到它们。

用法：
  python3 reset_by_topic.py 动态限额
  python3 reset_by_topic.py 动态限额 --dry-run        # 只查不动
  python3 reset_by_topic.py 动态限额 --decks 客观题  # 只查客观题相关 deck
  python3 reset_by_topic.py "sca_sec 计划值"          # 自定义关键词（OR 关系）
  python3 reset_by_topic.py --list-topics             # 列所有主题
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

INDEX_FILE = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛/🎯每日背诵/题库索引.json")


def ank(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    res = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://127.0.0.1:8765",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, check=True)
    r = json.loads(res.stdout)
    if r.get("error"):
        raise RuntimeError(f"AnkiConnect 错误 [{action}]: {r['error']}")
    return r["result"]


def load_index():
    if not INDEX_FILE.exists():
        sys.exit(f"❌ 索引不存在: {INDEX_FILE}\n先跑 build_anki_index.py")
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def list_topics(idx):
    print("📚 可用主题：\n")
    for name, info in idx["topics"].items():
        kws = ", ".join(info["keywords"][:4])
        more = f" (+{len(info['keywords'])-4} 个关键词)" if len(info["keywords"]) > 4 else ""
        print(f"  • {name}")
        print(f"      关键词: {kws}{more}")
    print(f"\n共 {len(idx['topics'])} 个主题")


def build_query(keywords, decks=None):
    """拼接 AnkiConnect 搜索查询。
    AnkiConnect 搜索语法跟 Anki 浏览器一致：
      - 默认按 Front 和 Back 全文搜
      - "kw OR kw"
      - deck:"xxx" 限定 deck
    """
    # 关键词部分：用 OR 连接，每个加引号防止空格被切
    kw_parts = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        # 关键词带空格 → 加引号
        if " " in kw:
            kw_parts.append(f'"{kw}"')
        else:
            kw_parts.append(kw)
    kw_query = "(" + " OR ".join(kw_parts) + ")"

    if decks:
        deck_query = "(" + " OR ".join(f'deck:"{d}*"' for d in decks) + ")"
        return f"{deck_query} {kw_query}"
    return kw_query


def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic", nargs="?", help="主题名（在索引内）/ 或自定义关键词字符串（空格分隔）")
    p.add_argument("--list-topics", action="store_true", help="列出所有主题")
    p.add_argument("--dry-run", action="store_true", help="只查不动")
    p.add_argument("--decks", nargs="*", default=None, help="限定 deck（前缀模式，可写父 deck 名）")
    p.add_argument("--days", default="0", help="到期日偏移：0=今天，1=明天，'1-3'=随机 1-3 天后")
    p.add_argument("--limit", type=int, default=None, help="只处理前 N 张")
    args = p.parse_args()

    idx = load_index()

    if args.list_topics:
        list_topics(idx)
        return

    if not args.topic:
        sys.exit("❌ 缺主题名或关键词。--list-topics 看可用主题。")

    # 决定关键词来源
    if args.topic in idx["topics"]:
        keywords = idx["topics"][args.topic]["keywords"]
        print(f"📌 主题: {args.topic}")
        print(f"   关键词: {', '.join(keywords[:6])}{'...' if len(keywords)>6 else ''}")
    else:
        # 当作自定义关键词，按空格切
        keywords = args.topic.split()
        print(f"📌 自定义关键词: {keywords}")

    # 构造 query
    query = build_query(keywords, args.decks)
    print(f"   AnkiConnect query: {query}\n")

    # 查
    print("🔍 搜索...")
    cards = ank("findCards", query=query)
    if not cards:
        print("  ⚠️ 未匹配到任何卡片")
        return
    print(f"  匹配 {len(cards)} 张卡")

    # 取 cardsInfo 看分布
    info = ank("cardsInfo", cards=cards[:min(200, len(cards))])
    deck_counter = {}
    for c in info:
        d = c.get("deckName", "?")
        deck_counter[d] = deck_counter.get(d, 0) + 1
    print("\n  分布（前 200 张样本）:")
    for d, n in sorted(deck_counter.items(), key=lambda x: -x[1]):
        print(f"    · {d}: {n} 张")

    # limit
    target_cards = cards if args.limit is None else cards[:args.limit]
    print(f"\n🎯 准备 setDueDate(days={args.days}) {len(target_cards)} 张")

    if args.dry_run:
        print("⏸ --dry-run 模式：不实际推送")
        return

    confirm = input("\n确认推送？[y/N] ").strip().lower()
    if confirm != "y":
        print("已取消")
        return

    # AnkiConnect setDueDate 单次最多 100 张，分批
    BATCH = 100
    ok = err = 0
    for i in range(0, len(target_cards), BATCH):
        batch = target_cards[i:i+BATCH]
        try:
            r = ank("setDueDate", cards=batch, days=args.days)
            if r:
                ok += len(batch)
            else:
                err += len(batch)
        except Exception as e:
            print(f"  ❌ 批次 {i//BATCH+1}: {e}")
            err += len(batch)
        print(f"  进度: {ok+err}/{len(target_cards)}", end="\r")
    print(f"\n\n✅ 已设置 {ok} 张今天到期")
    if err:
        print(f"❌ 失败 {err} 张")
    print("\n打开 Anki，这些卡会出现在牌组队首。")


if __name__ == "__main__":
    main()
