#!/bin/bash
# 一键刷新题库 → 推到 GitHub + 同步 Anki
# 用法: bash refresh_exam.sh
# 或在 Claude 里说「刷新题库」
#
# 流程（v5 · 2026-05-18 大重构后）：
#   Step 0   doctor.py --quick              ← 体检：扫路径/题数/skill 引用，发现漂移立即报
#   Step 1   build_exam_data.py             ← question.json → web/exam_data.json
#   Step 2   build_progress_data.py         ← question.json 的 weak 字段 → web/progress_data.json
#   Step 3   push_exam_to_anki.py           ← question.json → Anki 实操题::{学科}（幂等）
#   Step 4   build_subject_bank.py          ← question.json → 04实操题集/{学科}/anki归档/{学科}-{源文件}.md（副产物）
#   Step 5   检查变化并 git commit
#   Step 6   git push
#
# v5 改动：
#   1. 数据源从 9 份 题库.json + 9 份 薄弱点.json 改为单一 question.json
#   2. Step 0 加 doctor.py 体检，防止路径/题数等漂移在静默中跑
#   3. Step 3 anki 路径修正：旧目录名(anki+工具) → anki/
#   4. Step 3 不再吞错：脚本不存在硬报错，仅当 AnkiConnect 连不上才软警告

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WEB_DIR="$SCRIPT_DIR/web"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
# 2026-05-18 GitHub 备份重组：question.json 物理位置移到 工具/data/
QFILE="$SCRIPT_DIR/data/question.json"

# 前置检查：question.json 必须存在
if [ ! -f "$QFILE" ]; then
    echo "❌ 致命：question.json 不存在: $QFILE"
    echo "   请先运行 Phase 1 合并脚本生成全局题库"
    exit 1
fi
echo "✓ question.json: $QFILE ($(stat -f%z "$QFILE") bytes)"

cd "$SCRIPT_DIR"

echo ""
echo "🩺 [0/6] 体检（doctor.py --quick）..."
if [ -f doctor.py ]; then
    python3 doctor.py --quick || { echo "❌ 体检不通过，终止刷新"; exit 1; }
else
    echo "  ⚠️  doctor.py 尚未落地，跳过体检（Phase 3 待补）"
fi

echo ""
echo "🔄 [1/6] 重建 exam_data.json..."
python3 build_exam_data.py

echo ""
echo "📈 [2/6] 重建 progress_data.json..."
python3 build_progress_data.py

echo ""
echo "🎴 [3/6] 同步 Anki 实操题牌组（增量，幂等）..."
ANKI_SCRIPT="$SCRIPT_DIR/anki/push_exam_to_anki.py"
if [ ! -f "$ANKI_SCRIPT" ]; then
    echo "❌ 致命：找不到 $ANKI_SCRIPT"
    echo "   路径修正后仍缺文件，请检查 anki/ 目录"
    exit 1
fi
# 执行并捕获 stderr 分情况处理
ANKI_LOG=$(mktemp)
if python3 "$ANKI_SCRIPT" 2>"$ANKI_LOG"; then
    echo "  ✓ Anki 同步完成"
else
    rc=$?
    if grep -qiE "Connection refused|AnkiConnect|ConnectionError|URLError" "$ANKI_LOG"; then
        echo "  ⚠️  AnkiConnect 连不上，跳过（不影响 web 刷新）"
        cat "$ANKI_LOG"
    else
        echo "❌ 致命：push_exam_to_anki.py 执行失败（非 Anki 连接问题）"
        cat "$ANKI_LOG"
        rm -f "$ANKI_LOG"
        exit $rc
    fi
fi
rm -f "$ANKI_LOG"

echo ""
echo "📝 [4/6] 生成 anki 副产物 md（学科+源文件归档）..."
if [ -f build_subject_bank.py ]; then
    python3 build_subject_bank.py --all || echo "  ⚠️  副产物 md 生成失败，不阻断"
else
    echo "  ⚠️  build_subject_bank.py 未落地，跳过"
fi

echo ""
echo "📊 [5/6] 检查变化并提交..."
cd "$WEB_DIR"
if git diff --quiet exam_data.json progress_data.json index.html; then
    echo "  ⚠️  题库/进度/页面均无变化，跳过提交"
    echo ""
    echo "✅ 完成（Anki 已同步，GitHub 无变化）"
    exit 0
fi

STATS=$(python3 -c "
import json
d = json.load(open('exam_data.json'))
subs = d.get('subjects', [])
print(' / '.join(f\"{s['name']} {s['q_count']}题\" for s in subs))
" 2>/dev/null || echo "题库已更新")

git add exam_data.json progress_data.json index.html 2>/dev/null || true
git commit -m "data: 刷新题库+进度 $(date +%Y-%m-%d) · $STATS"

echo ""
echo "🚀 [6/6] 推送到 GitHub..."
git push origin main

echo ""
echo "✅ 完成！1-2 分钟内线上生效："
echo "   https://aerfagogogo.github.io/zhuwang-type-drill/"
echo ""
