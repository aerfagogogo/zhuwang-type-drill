#!/usr/bin/env python3
"""
把全局 question.json 推到 Anki 实操题::{学科} 子牌组。
2026-05-18 大重构后：从 9 份 学科/题库.json 改为单一 question.json，数据源由 _qdata 适配器统一提供。
幂等：按 Front 里的 [编号] 检重，已存在跳过；Back 为空时补上答案。

用法：
    python3 push_exam_to_anki.py                 # 推所有学科
    python3 push_exam_to_anki.py 操作系统         # 只推指定学科
    python3 push_exam_to_anki.py --dry-run        # 预览，不改 Anki
    python3 push_exam_to_anki.py 系统平台 --dry-run

支持的学科（来自 question.json 实际包含的学科）：
    操作系统 / 数据库 / 竞赛环境 / 系统平台 / 稳态监控
    综合智能告警 / 网络分析 / 调度数据网 / 基础平台

Front 格式：  [#{编号}] {title}
              {题面}

Back 格式：   {答案}（markdown 简单转 HTML）

Tags：  主网竞赛  {学科}  {题源标签...}  大纲_{归属大纲}
Deck：  q.deck（即 "实操题::{学科}"）
"""
import json, re, subprocess, sys
from pathlib import Path

# 引入共享适配器（_qdata.py 在 工具/ 根目录）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _qdata

ANKI_URL = "http://127.0.0.1:8765"
MODEL = "Obsidian-basic-source"  # 字段: Front / Back / Skeleton / Source

DRY = "--dry-run" in sys.argv
# 过滤掉 --dry-run，剩下的是学科名
SUBJECTS_ARG = [a for a in sys.argv[1:] if not a.startswith("--")]


# ─────── AnkiConnect ───────
def ank(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params})
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", ANKI_URL,
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, check=True)
    result = json.loads(r.stdout)
    if result.get("error"):
        raise RuntimeError(f"AnkiConnect [{action}]: {result['error']}")
    return result["result"]


# ─────── Markdown → HTML（简化）───────
def md_to_html(text: str) -> str:
    if not text:
        return ""
    # 代码块 ```lang\n...\n```
    text = re.sub(r"```[a-z]*\n(.*?)```", lambda m: f"<pre><code>{m.group(1)}</code></pre>", text, flags=re.DOTALL)
    # 行内代码 `...`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # 加粗 **...**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # wikilink 图片 ![[...]] → 略去（Anki 无法渲染）
    text = re.sub(r"!\[\[.*?\]\]", "[图片省略]", text)
    # wikilink [[...]] → 文本
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", text)
    # 换行 → <br>
    text = text.replace("\n", "<br>\n")
    return text.strip()


# ─────── 主逻辑 ───────
def push_subject(subject: str):
    questions = _qdata.by_subject(subject)
    if not questions:
        print(f"  ⚠️  {subject}: question.json 中无该学科题目，跳过")
        return

    # deck 字段直接取 q.deck（schema 规定 = "实操题::{subject}"）
    deck = questions[0].get("deck") or f"实操题::{subject}"
    print(f"\n{'[DRY] ' if DRY else ''}▶  {subject}  ({len(questions)} 题 → {deck})")

    # 确保牌组存在
    if not DRY:
        ank("createDeck", deck=deck)

    added = updated = skipped = 0

    for q in questions:
        qid = f"#{q['编号']}"  # Anki 端用 #编号 作为稳定标识符
        title = q.get("title", "")
        tian  = q.get("题面", "")
        ans   = q.get("答案", "") or ""
        tags_raw = q.get("tags", []) or []
        outline = q.get("归属大纲", "")
        source_val = q.get("题源", "")

        # Front: [#编号] title \n\n 题面
        front_html = (
            f"<p><strong>[{qid}]</strong> {title}</p>"
            f"<hr>{md_to_html(tian)}"
        )
        back_html  = md_to_html(ans) if ans.strip() else ""
        source_html = f"<p>{source_val}</p>" if source_val else ""

        # tags list（Anki tag 不能有空格，用下划线）
        anki_tags = ["主网竞赛", subject]
        for t in (tags_raw if isinstance(tags_raw, list) else []):
            anki_tags.append(str(t).replace(" ", "_"))
        if outline:
            anki_tags.append(f"大纲_{str(outline).replace('.','_')}")

        # 检重：按 Front 里的 [#编号] 查
        existing = ank("findNotes", query=f'deck:"{deck}" "Front:*[{qid}]*"') if not DRY else []

        if existing:
            # 已存在——如果 Back 为空则补上
            if not DRY and back_html:
                info = ank("notesInfo", notes=existing[:1])[0]
                cur_back = info["fields"].get("Back", {}).get("value", "")
                if not cur_back.strip():
                    ank("updateNoteFields", note={
                        "id": existing[0],
                        "fields": {"Back": back_html}
                    })
                    updated += 1
                    continue
            skipped += 1
            continue

        # 新增
        note = {
            "deckName": deck,
            "modelName": MODEL,
            "fields": {
                "Front":    front_html,
                "Back":     back_html,
                "Skeleton": "",
                "Source":   source_html,
            },
            "tags": anki_tags,
        }
        if not DRY:
            ank("addNote", note=note)
        added += 1

    print(f"    新增 {added} | 补Back {updated} | 跳过 {skipped}")
    return added, updated, skipped


# ─────── 入口 ───────
if __name__ == "__main__":
    # 确认 Anki 在线
    try:
        ver = ank("version")
        print(f"AnkiConnect v{ver} ✅")
    except Exception as e:
        print(f"❌ 无法连接 Anki: {e}")
        sys.exit(1)

    # 决定要处理的学科列表
    all_subjects = _qdata.subjects()
    if SUBJECTS_ARG:
        subjects_to_push = [s for s in SUBJECTS_ARG if s in all_subjects]
        missing = [s for s in SUBJECTS_ARG if s not in all_subjects]
        for m in missing:
            print(f"⚠️  question.json 中无学科: {m}（可用: {all_subjects}）")
    else:
        subjects_to_push = all_subjects

    total_added = total_updated = total_skipped = 0
    for s in subjects_to_push:
        result = push_subject(s)
        if result:
            a, u, sk = result
            total_added += a; total_updated += u; total_skipped += sk

    print(f"\n{'[DRY] ' if DRY else ''}{'=' * 40}")
    print(f"  新增 {total_added} | 补Back {total_updated} | 跳过 {total_skipped}")
    if DRY:
        print("  → 没有真正改动。去掉 --dry-run 正式执行。")
