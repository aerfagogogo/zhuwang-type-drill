# 主网自动化竞赛 · 工作手册

**常用入口**：操作系统训练 · 达梦训练 · 竞赛环境训练 · 变式训练 · 出模拟卷 · 刷新题库（`bash refresh_exam.sh`）

> **本 README 是项目 SSOT**（流程/规则维度）。与 memory、与"印象"冲突时**以本文档为准**。
> **2026-05-18 v6 大重构**：题库从 9 份分散 json 合并为单一 `question.json`，MD 文档退役（仅作 Anki 推题副产物），网页改名「训练中心 / 惩罚 / 变式训练」，新增「整理 anki」skill 等。完整改造经过见 [[2026-05-18-主网竞赛大重构]] 经验贴。

---

## 0 · 速览

```
内容 SSOT       → question.json（项目根，291 题）
流程 SSOT       → 本 README
大纲 SSOT       → 工具/web/outline.json（8 章 106 KP，对齐系统实操学习脑图.pdf）
体检入口        → 工具/doctor.py --quick | --full
一键刷新        → 工具/refresh_exam.sh （Step 0 自动跑 doctor）
```

## 1 · 数据分层 SSOT

| 层级 | 文件 | 谁写 |
|---|---|---|
| 流程/规则 | `README.md`（本文件） | 用户 + Claudian 协议 |
| 题目内容 | `question.json` | Claudian 录入 + 用户在 Anki 编辑后回写 |
| 大纲结构 | `工具/web/outline.json` | PDF 大纲解析（对齐系统实操学习脑图.pdf） |
| 派生网页数据 | `工具/web/exam_data.json` `progress_data.json` | `build_exam_data.py` / `build_progress_data.py` 派生 |
| Anki 牌组进度 | Anki 本机数据库 | 用户日常复习 + AnkiConnect 读 |
| Anki 推题副产物 | `04实操题集/{学科}/anki归档/*.md` | `build_subject_bank.py` 派生（**不要手编**） |

**铁律**：
- `question.json` 是题目内容的唯一编辑入口（Anki 端临时编辑通过「整理 anki」skill 同步回来）
- `04实操题集/{学科}/anki归档/*.md` 是只读副产物，**严禁手改**——下次 build_subject_bank 会覆盖

## 2 · question.json schema

每题字段（全部 13 项必备，doctor 体检校验）：

```json
{
  "编号": 78,                              // 全局自增整数
  "subject": "操作系统",                    // 学科 = 04实操题集 文件夹名
  "deck": "实操题::操作系统",                // Anki 牌组路径
  "title": "024-NTP 对时 + 定时重启",
  "题面": "...",
  "答案": "...",                            // 部分题可能为空字符串（待用户上机后补）
  "题源": "杭州培训·凝思 第一·题24",
  "tags": ["操作系统", "Shell 脚本与系统优化", "资源管控"],  // 单层，无特殊字符
  "归属大纲": "1.2.3",                      // PDF 大纲叶节点编号；竞赛环境学科为空
  "weak_count": 0,
  "correct_streak": 0,
  "last_wrong_at": null,
  "last_attempt_at": null,
  "notes": ""                               // 训练记录 list 或空 string
}
```

**字段写入方**：

| 字段 | 谁写 |
|---|---|
| 编号 / subject / deck | `import_source.py` 录入时定 |
| title / 题面 / 答案 / 题源 | `import_source.py` + 用户在 Anki 编辑 → 「整理 anki」回写 |
| tags / 归属大纲 | Claudian 录入时初判（参照 outline.json）；用户在 Anki 调整 → 「整理 anki」回写 |
| weak_count / correct_streak / last_wrong_at / last_attempt_at / notes | CV 训练写入（操作系统/数据库/竞赛环境）+ Anki 反向同步（其他学科）|

## 3 · 学科分布（2026-05-18 实测）

| 学科 | 题数 | 训练轨 |
|---|---|---|
| 系统平台 | 76 | Anki 客观题 |
| 操作系统 | 58 | CV 实操（ks-wh01）|
| 基础平台 | 54 | Anki 客观题 |
| 数据库 | 37 | CV 实操（ks-his01）|
| 稳态监控 | 28 | Anki 客观题 |
| 竞赛环境 | 15 | CV 实操（Docker） |
| 网络分析 | 14 | Anki 客观题 |
| 综合智能告警 | 7 | Anki 客观题 |
| 调度数据网 | 2 | Anki 客观题 |
| **合计** | **291** | |

## 4 · 工作流

### 4.1 日常学习闭环

```
新题来源（老师发的 word/xlsx/txt）
  └── 用户分类放入 04实操题集/{学科}/源文件/
        │
        ▼ 运行 import_source.py
  题目录入 question.json（编号自增 + tags 留空 + 归属大纲留空）
        │
        ├── Claudian 用 outline.json 语义初判 tags + 归属大纲
        │
        ▼ 运行 refresh_exam.sh
  - 派生 exam_data.json / progress_data.json
  - 推 Anki 实操题::{学科} 牌组（push_exam_to_anki.py）
  - 生成 anki归档/{学科}-{题源}.md 副产物
        │
        ▼
  ╔══════════════════════╗     ╔══════════════════════╗
  ║ CLI 实操学科         ║     ║ GUI / 客观题学科       ║
  ║ 操作系统 / 数据库     ║     ║ 系统平台 / 稳态监控 等  ║
  ║ 竞赛环境              ║     ║                       ║
  ║                      ║     ║                       ║
  ║ → 触发 CV 训练 skill ║     ║ → 用户在 Anki 复习     ║
  ║   读 question.json   ║     ║   备注/订正/加 tag     ║
  ║   出题 → 实操 → 评判 ║     ║                       ║
  ║   update_weak.py 写  ║     ║ → 「整理 anki」skill   ║
  ║   weak_count++ etc   ║     ║   anki_sync.py 回写    ║
  ╚══════════════════════╝     ╚══════════════════════╝
        │                              │
        └───────────┬──────────────────┘
                    ▼
            训练中心网页展示
            （以 PDF 大纲为骨架，按 KP 聚合题，
              点 KP 节点看薄弱题 + 题面预览）
```

### 4.2 触发词速查

| 用户说 | 触发什么 |
|---|---|
| 「刷新题库」 | `bash 工具/refresh_exam.sh` |
| 「Linux 训练 / 操作系统训练」 | `.claude/skills/操作系统训练.md` |
| 「达梦训练 / 数据库训练」 | `.claude/skills/达梦训练.md` |
| 「竞赛环境训练」 | `.claude/skills/竞赛环境训练.md` |
| 「整理 anki / 弄一下 anki」 | `.claude/skills/整理anki.md` |
| 「变式训练 / 对这题变式」 | `.claude/skills/变式训练.md` |
| 「出模拟卷」 | `.claude/skills/出模拟卷.md` |

## 5 · 脚本生态

位于 `工具/` 目录，所有脚本通过 `_qdata.py` 适配器统一访问 question.json。

| 脚本 | 作用 | 何时跑 |
|---|---|---|
| `_qdata.py` | 共享数据适配器（读写 question.json） | 被其他脚本 import，不直接跑 |
| `doctor.py` | 体检脚本（quick + full 两级） | refresh_exam 自动跑；用户怀疑漂移时手动跑 |
| `refresh_exam.sh` | 一键刷新：体检 → 派生 → 推 Anki → 生成副产物 → git commit | 每次录新题 / 训练完一轮后 |
| `import_source.py` | word/xlsx/txt 源文件 → question.json 录入桥 | 拿到老师发的新题文件时 |
| `build_exam_data.py` | question.json + outline.json → exam_data.json | 由 refresh_exam.sh 调用 |
| `build_progress_data.py` | question.json 的 weak + AnkiConnect → progress_data.json | 同上 |
| `build_subject_bank.py` | question.json → anki归档/*.md 副产物 | 同上 |
| `push_exam_to_anki.py` | question.json → Anki 牌组（增量、幂等） | 同上 |
| `update_weak.py` | 写 question.json 的 weak 字段（CV 训练落盘）| CV 训练 skill 内部调用 |
| `anki_sync.py` | Anki 端编辑 → question.json 回写 | 整理 anki skill 触发 |
| `build_index.py` | 资料库索引（与本流程独立） | 不动 |

### 5.1 体检 (doctor) 使用示范

```bash
# 快体检：路径/题数/skill 文件存在性，~1 秒
python3 工具/doctor.py --quick

# 深体检：加 question.json ↔ outline.json 一致性、学科分布
python3 工具/doctor.py --full
```

退出码：0 全过 / 1 有警告 / 2 致命错误。refresh_exam.sh 在 Step 0 跑 quick，致命退出。

## 6 · 网页

位于 `工具/web/`，发布到 GitHub Pages: https://aerfagogogo.github.io/zhuwang-type-drill/

| 文件 | 作用 |
|---|---|
| `index.html` | 入口聚合页 |
| `training-center.html` | **训练中心** · 以 PDF 大纲为骨架，按 KP 聚合题 + 显示薄弱状态 + 题面预览（2026-05-18 改名自「D6.0 备考训练中心」）|
| `exam.html` | **变式训练**入口（2026-05-18 砍掉「一站式训练」其他功能） |
| `drill.html` | **惩罚** · CV 训练做错时弹的盲敲页（2026-05-18 改名自「盲敲惩罚」，qid 改用全局编号） |
| `mockup.html` | UI 方案预览（设计基础，含两套配色 token） |
| `exam_data.json` | 派生：网页主数据 |
| `progress_data.json` | 派生：进度数据（CLI 学科取 weak、GUI 学科取 Anki） |
| `outline.json` | PDF 大纲结构化（106 KP）|

**UI 设计参考**：
- 暗色 dashboard 风格（参考 `/Users/sunyiting/Desktop/123.txt` 设计 token）
- 字体：DM Mono（等宽数字） + Noto Sans SC（中文）
- 配色 token 见 `mockup.html` 方案 A（Claude Native 暖橙）/ 方案 B（Vibe Island 玻璃岛）
- 全面 UI 重做留作后续单独迭代任务，不在 2026-05-18 重构范围

## 7 · skill 清单

位于 `.claude/skills/`（vault 根目录），按 frontmatter description 自动触发。

| Skill | 作用 | 触发词样例 |
|---|---|---|
| 操作系统训练.md | 凝思 Linux 实操（ks-wh01） | linux 训练、操作系统训练 |
| 达梦训练.md | DM8 实操（ks-his01） | 达梦训练、数据库训练 |
| 竞赛环境训练.md | Docker 仿真环境训练 | 竞赛环境训练、网络训练 |
| 变式训练.md | 出变式题（不计成绩） | 变个题、对这题变式 |
| 出模拟卷.md | 生成模拟卷 | 出模拟卷 |
| 主观题训练.md | 主观题盲答评分 | 主观题训练、粘多行要点 |
| **整理anki.md**（v0.1 新）| Anki ↔ question.json 同步 | 整理 anki、弄一下 anki |
| Anki错题重学.md | Anki 错题专项刷 | （按 frontmatter）|
| anki分析.md / anki同步.md | 现有 Anki 工具，与「整理 anki」职能可能重叠，后续视情况合并 | |
| 制作闪卡.md / 考过题标记.md / 错题标注.md | 现有辅助 skill | |
| 考试宝转换.md | 用户独立工具 | （不属于本项目重构范围） |

**2026-05-18 已归档**（最后快照在 `70-归档/skills版本/<名>/v_废弃_2026-05-18.md`）：
- 念能力训练.md（与新流程不匹配）
- 竞赛训练.md（过时）
- 错题标注.md → 已删
- 杭州培训-*.md（4 份，杭州培训已并入主网）

## 8 · 故障排查

| 症状 | 检查 |
|---|---|
| refresh_exam.sh 报 anki 路径错 | 看是否 push_exam_to_anki.py 在 `工具/anki/` 下（v5 修过的 bug） |
| Anki 推题后题数没变 | doctor --full 看 question.json 与 outline.json 一致性 |
| drill.html 找不到题 | `?qid=` 必须是全局编号；旧风格 `qid=操作系统-001` 也兼容但不推荐 |
| 「整理 anki」无差异 | Anki 端 Front 是否含 `[#编号]`（旧推送是 `[操作系统-001]`，需先重新 push 一次） |

## 9 · 同步 GitHub（常规动作）

**仓库结构**（2026-05-18 v6 大重构后）：
- **git root = `工具/`**（项目工具代码 + question.json + web + README 都在这）
- **远端 = `https://github.com/aerfagogogo/zhuwang-type-drill.git`**（public，main 分支）
- **GitHub Pages 入口**：`https://aerfagogogo.github.io/zhuwang-type-drill/`
  - root 的 `工具/index.html` 是跳转页，自动重定向到 `/web/`
  - 实际内容来自 `工具/web/` 子目录
- **vault 主仓库**（vault 根目录）保持本地 git，不推远端

**GitHub 双重作用**：工具代码备份（防丢 + 跨机 pull） + 网页发布（GitHub Pages）。

**日常工作流**（铁律）：

```bash
# 1. 拉最新（每次本地改之前必跑）
cd "/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛/工具"
git pull origin main

# 2. 本地改（python 脚本 / question.json / README / web HTML 等）
#    路径说明：
#    - question.json 物理位置 = 工具/data/question.json
#      （项目根 question.json 是软链回指，本地仍可用旧路径访问）
#    - README.md 物理位置 = 工具/README.md
#      （项目根 README.md 是软链回指）

# 3. 体检（强制）
python3 doctor.py --quick || exit 1

# 4. 提交 + 推
git add -A
git diff --cached --stat   # 看清要 commit 什么
git commit -m "$(cat <<'EOF'
<一句话概括>

<分类要点>

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
git push origin main
```

**触发场景**（CV 自动按此协议跑）：
- 改了 `工具/*.py` / `工具/*.sh` / `工具/web/*` / `工具/data/question.json` / `工具/README.md` / 工具下任何 tracked 文件
- 用户说「同步 github」「推 github」「commit + push」「上传」「更新远程」

**自动 push 入口**：`refresh_exam.sh` Step 5/6 仍自动跑（派生数据 + 推 Anki + git commit + push）。

**每日 squash auto-sync commit**（每日收尾跑一次，可选）：
```bash
N=$(git log --oneline --since="today 00:00" | wc -l)
git rebase -i HEAD~$N    # 把 auto-sync 行的 pick 改成 squash 或 fixup
```

**铁律细节**：
- commit message 第一行不超过 70 字符，正文用空行 + 要点列表
- 涉及破坏性 git 操作（`reset --hard / push --force / branch -D / filter-repo`）必须用户**明确同意**才执行
- 体检不过禁止 push
- 触发条件命中后 CV 提示 commit message 草稿，等用户**点头**再真正提交
- 关键路径如 `.env / credentials.json` 等敏感文件，永远不要 `git add -A`，改成具名添加

**vault 主仓库**（vault 根目录）保留本地 git，不推远端。vault 内除工具目录之外的改动（如 `.claude/skills/*` / `04实操题集/*` / `20-经验/*`）走 vault 本地 commit。

## 10 · 历史变更

- **2026-05-18 v6 大重构**：本次。完整设计决策与执行回顾见 [[2026-05-18-主网竞赛大重构]] 经验贴。
- **2026-05-18 v6.1 Codex 审查后修正**：6 处问题修完（doctor full 真正可用 / merge 脚本路径修正 / 变式训练.md 对齐 / 惩罚 URL 补 drill.html / 活文件残留清理 / notes 字段统一 list）。
- 之前历史变更通过 git log 追溯。
