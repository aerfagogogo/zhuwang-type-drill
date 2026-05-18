#!/usr/bin/env bash
# auto_rebuild_bank.sh — PostToolUse hook：MD 改动后自动重建对应学科 题库.json
#
# 触发条件（Claude Code 在 settings.json 里配 matcher）：
#   Edit/Write 触及 50-项目/主网自动化竞赛/04实操题集/<学科>/NNN-*.md
#
# 工作流：
#   1. 从 stdin 拿 hook payload JSON
#   2. 抽 file_path → 提取 <学科> 段
#   3. 跑 build_subject_bank.py <学科>
#   4. 失败也不阻塞（exit 0），只往 stderr 报告
#
# 调试：
#   echo '{"tool_input":{"file_path":"50-项目/主网自动化竞赛/04实操题集/数据库/001-x.md"}}' | bash auto_rebuild_bank.sh

set -uo pipefail

VAULT="/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间"
WORKFLOW="$VAULT/50-项目/主网自动化竞赛/99-工作流"
LOG="$WORKFLOW/.auto_rebuild_bank.log"

# 读 hook payload
payload=$(cat)
file_path=$(echo "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
')

# 没拿到路径就退出
[ -z "$file_path" ] && exit 0

# 只处理 04实操题集/<学科>/*.md，且文件名是 NNN-*.md 格式
if [[ "$file_path" != *"/04实操题集/"*"/"*".md" ]]; then
    exit 0
fi
basename=$(basename "$file_path")
if [[ ! "$basename" =~ ^[0-9]+-.*\.md$ ]]; then
    exit 0
fi

# 抽 <学科> 段
subject=$(echo "$file_path" | sed -E 's|.*/04实操题集/([^/]+)/.*|\1|')
[ -z "$subject" ] && exit 0

# 跳过非常规学科
case "$subject" in
    源文件|模拟卷) exit 0 ;;
esac

# 跑重建（静默 + 记日志）
{
    echo "── $(date '+%Y-%m-%d %H:%M:%S') ──"
    echo "trigger: $file_path"
    python3 "$WORKFLOW/build_subject_bank.py" "$subject" 2>&1
} >> "$LOG" 2>&1

exit 0
