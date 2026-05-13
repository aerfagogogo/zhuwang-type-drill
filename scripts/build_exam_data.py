#!/usr/bin/env python3
"""
扫 04实操题集/<学科>/*.md → 抽题面 → 写 web/exam_data.json
用法: python3 build_exam_data.py
"""
import json
import re
from pathlib import Path

ROOT = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛/04实操题集")
WEB = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛/99-工作流/web")

# 扫描哪些学科
SUBJECTS = ["操作系统"]  # 后续可加 "D60基础平台", "达梦数据库", "综合试题"

SKIP_FILES = {"惩罚清单.md", "薄弱点.json", "MOC.md"}

def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm_text = m.group(1)
    fm = {}
    for line in fm_text.splitlines():
        mm = re.match(r"^(\S+?):\s*(.+)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"\'')
    return fm, text[m.end():]

def extract_question(body):
    """抽 ## 题目 / ## 题面 段落内容（直到下一个 ## 为止）。"""
    m = re.search(r"^##\s+题[目面]\s*\n(.+?)(?=\n##\s|\Z)", body, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""

def extract_answer(body):
    """抽 ## 答案 段落（包括代码块）。"""
    m = re.search(r"^##\s+答案\s*\n(.+?)(?=\n##\s|\Z)", body, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""

def main():
    out = {}
    for subj in SUBJECTS:
        subj_dir = ROOT / subj
        if not subj_dir.exists():
            print(f"[!] 跳过 {subj}（目录不存在）"); continue
        questions = []
        for md in sorted(subj_dir.glob("*.md")):
            if md.name in SKIP_FILES:
                continue
            text = md.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(text)
            qid = fm.get("id") or md.stem
            # 标题用文件名（已包含序号），去掉扩展名
            title = md.stem
            qtext = extract_question(body)
            if not qtext:
                print(f"[!] {md.name} 没找到 ## 题目/## 题面，跳过")
                continue
            questions.append({
                "id": qid,
                "title": title,
                "题面": qtext,
                "标答": extract_answer(body),
                "题源": fm.get("题源", ""),
            })
        out[subj] = questions
        print(f"  {subj}: {len(questions)} 题")
    WEB.mkdir(exist_ok=True)
    target = WEB / "exam_data.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入: {target}")

if __name__ == "__main__":
    main()
