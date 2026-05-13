# 99-工作流 · Claudian 操作手册

> 本文档是**你（用户）告诉我（Claudian）怎么干活**的字典 + 工作流总览。
> 你只需要记几个口令，剩下我跑。

最近一次更新：2026-05-14 ｜ Web 仓库版本：v0.4

---

## 1. 项目快照

| 维度 | 状态 |
|---|---|
| **操作系统** 题集（57 题） | ✅ 答案 v1 已批量生成 · 用户校正中 |
| **达梦数据库** 题集 | ⚪ 题面已录入 · 答案待生成 |
| **D60 基础平台** 题集 | ⚪ 题面已录入 · 答案待生成 |
| **系统平台** 题集 | ⚪ 未建（短答题型，处理方式不同） |
| **综合试题** | ⚪ 未建 |
| 资料库索引（PDF/MD/DOCX 全文） | ✅ 406 条目 + 14MB 抽取文本 |
| 试卷训练网页 `exam.html` | ✅ v2 一站式（API 批卷 + 内嵌盲敲） |
| 惩罚清单网页 `index.html` | ✅ v2 题目导向 |
| AIHUBMIX API 集成 | ✅ 默认 `gpt-4o-mini`（可换） |
| 距离考试 | 约 2 周 |

---

## 2. 工具一览（全部在本目录）

| 脚本 | 干啥 | 何时跑 |
|---|---|---|
| `build_index.py` | 扫 `03资料库/` 所有格式 → 写 `资料库索引.json` + `.extracted-text/` | 资料库加新文件时 |
| `build_exam_data.py` | 扫 `04实操题集/<学科>/*.md` 抽题面+标答 → 写 `web/exam_data.json` | vault 改了题面或答案后 |
| `punishment.py` | 读 `<学科>/薄弱点.json` → 写 `<学科>/惩罚清单.md`（带 checkbox） | 想看本地 MD 版清单时 |
| `gen_drill_url.py` | 读 薄弱点 → 输出网页惩罚预填 URL | 想发个一键训练链接时 |

详细用法在第 5 节。

---

## 3. 网页

| URL | 用途 |
|---|---|
| https://aerfagogogo.github.io/zhuwang-type-drill/exam.html | **一站式训练**：答题 → API 批卷 → 错点 → 盲敲 → 下一题（主入口） |
| https://aerfagogogo.github.io/zhuwang-type-drill/ | **惩罚清单独立模式**：直接练命令（不答题） |

**GitHub 仓库**：https://github.com/aerfagogogo/zhuwang-type-drill  
push 后 30-60s 自动重新部署。

---

## 4. 口令字典（你说 → 我做）

| 你说 | 我做 |
|---|---|
| 「**重建资料库索引**」 | `python3 build_index.py` |
| 「**重建资料库索引 --force**」 | `python3 build_index.py --force`（全部重抽 PDF） |
| 「**重建题库 JSON**」 | `build_exam_data.py` + 推 web 仓库 |
| 「**出 <学科> 惩罚清单**」 | `punishment.py gen <学科> 3` |
| 「**惩罚检查 <学科>**」 | `punishment.py check <学科>` → 全勾完自动归档 + 减 weak_count |
| 「**惩罚 URL <学科>**」 | `gen_drill_url.py <学科>` 给我链接 |
| 「**修 <学科>-NNN 答案：<问题>**」 | 改对应 MD → 跑 build_exam_data → 推 |
| 「**为 <学科> 批量生成答案**」 | 根据资料库 + 知识，给每题写草稿答案（**仅草稿**，需用户校正） |
| 粘贴 exam 训练 JSON | 读 entries → 找 `mark:flagged` 修答案；找 `verdict:wrong/dontknow` 更新薄弱点；regen 惩罚清单 |
| 粘贴打字训练 JSON | 读击键数据，分析哪条命令熟、哪条卡 |

---

## 5. 工具详细用法

### 5.1 资料库索引 · `build_index.py`

```bash
cd 99-工作流
python3 build_index.py          # 增量（已抽过的跳过）
python3 build_index.py --force  # 重抽全部
```

输出：
- `03资料库/资料库索引.json` — 全文搜索用
- `03资料库/.extracted-text/<镜像>.txt` — 每个非 MD 文件的纯文本副本

支持格式：MD / PDF / TXT / DOC / DOCX / XLSX / XLS / PPTX / PPT

### 5.2 题库 JSON · `build_exam_data.py`

```bash
cd 99-工作流 && python3 build_exam_data.py
# 然后推 web
cd web && git add exam_data.json && git commit -m "data: refresh" && git push
```

会抽 `04实操题集/<学科>/*.md` 里的 `## 题面` 和 `## 答案` 两段。

### 5.3 惩罚清单 MD · `punishment.py`

```bash
python3 punishment.py gen 操作系统 3   # 每条 drill 重复 3 遍
python3 punishment.py check 操作系统    # 检查 → 全勾完归档
```

输出 `04实操题集/<学科>/惩罚清单.md`，Obsidian 里勾 checkbox，全勾完自动迁到 `惩罚归档/`。

### 5.4 惩罚 URL · `gen_drill_url.py`

```bash
python3 gen_drill_url.py 操作系统
# 输出一个超长 URL，直接打开即载入预填命令
```

---

## 6. 跨学科扩展规划

### 6.1 已完成

| 学科 | 题数 | 答案类型 | 机器可判错？ |
|---|---|---|---|
| 操作系统 | 57 | shell 命令 + 配置 | ✅ 可（API 对照标答） |

### 6.2 待开展

| 学科 | 题型 | 答案生成 | 机器判错？ |
|---|---|---|---|
| 系统平台 | 简答题 / 实操步骤 | 用户口述 + AI 整理 | ⚠️ 半可（语义对比，准确率低） |
| 达梦数据库 | SQL + 步骤 | shell + SQL 混合 | ✅ 大部分可 |
| D60 基础平台 | 步骤性操作 | 用户口述 | ⚠️ 半可 |
| 综合试题 | 杂 | 混合 | 视题而定 |

### 6.3 学科扩展操作步骤

1. 在 `04实操题集/<新学科>/` 建文件夹
2. 把题源（doc/PDF/手抄）整理成 `NNN-标题.md`（按规范）
3. 跟 Claudian 说「**为 <新学科> 批量生成答案**」→ 我读资料库给草稿
4. **用户校正**（白天上机验证 / 翻教材 / 凭记忆）
5. 校正完，跟我说「**重建题库 JSON**」→ 推到网页
6. 在 `build_exam_data.py` 里把新学科加进 `SUBJECTS` 列表
7. 开练

---

## 7. 答案生成铁则

**第一遍答案的正确性由用户负责，不是 AI。**

具体协议：

| 步骤 | 谁干 | 说明 |
|---|---|---|
| ① **首版生成** | AI（我） | 基于资料库 + 知识，写草稿到 `## 答案` |
| ② **上机校正** | 用户 | 白天去机房实跑，对的留下，错的标 ⚠️ |
| ③ **修正发布** | AI（我） | 根据用户反馈改 MD，跑 build_exam_data，推 |
| ④ **训练验证** | 用户 | 试卷网页上重答，确认答案够用 |

**2026-05-14 教训**：Q004（账户锁定 + 口令有效期）首版答案漏了 `chage` 简便写法，是用户实测后发现的。所以**任何 AI 生成的答案在用户线下验证前都是草稿**。

---

## 8. 数据规范

### 8.1 题目 MD（`04实操题集/<学科>/NNN-标题前 15 字.md`）

frontmatter：
```yaml
---
id: <学科>-NNN
学科: <学科>
题源: <来源 第X题>
关联KP: "[[KP1]], [[KP2]]"
tags: [命令, 业务词]
创建: YYYY-MM-DD
---
```

正文：
```markdown
## 题面
xxx

## 答案

\`\`\`bash
# 第一步：xxx做啥
命令1

# 第二步：xxx做啥
命令2
\`\`\`
```

**注意**：必须严格用 `## 题面` 或 `## 题目`（脚本正则识别），`## 答案`（必须包含）。

### 8.2 Tag 规则

只能 `字母 / 数字 / _ / - / 中文`。含空格或 `>` 等会被 Obsidian 截断。

### 8.3 薄弱点 JSON（`04实操题集/<学科>/薄弱点.json`）

```json
[{
  "id": "操作系统-001",
  "title": "...",
  "md_path": "001-xxx.md",
  "weak_count": 1,
  "correct_streak": 0,
  "last_wrong_at": "2026-05-14",
  "last_attempt_at": "2026-05-14",
  "notes": [{
    "date": "2026-05-14",
    "variant": "试卷训练 v2",
    "wrong": ["错点1"],
    "drills": ["命令1"]
  }]
}]
```

`correct_streak >= 3` 视为过关，下次不进惩罚清单。

---

## 9. Git 版本管理

### 9.1 Web 仓库（zhuwang-type-drill）

每个里程碑打 tag 方便回滚：

| Tag | 时间 | 状态 |
|---|---|---|
| `v0.1` | 2026-05-13 | 打字训练初版（dazidazi 风格） |
| `v0.2` | 2026-05-13 | 加 localStorage 持久化 + 历史统计 |
| `v0.3` | 2026-05-13 | 试卷训练 v1（手贴 JSON）+ exam_data.json |
| `v0.4` | 2026-05-14 | **当前** · 一站式（AIHUBMIX API 批卷 + 内嵌盲敲）+ 5 个标记按钮 |

回滚命令：
```bash
cd web && git checkout v0.3   # 回到 v0.3 (Pages 自动重新部署)
```

查看历史：
```bash
cd web && git log --oneline
```

### 9.2 Vault

Vault 本身是 git repo（用户级），但 `99-工作流/` 默认未追踪。  
要纳入版本控制：
```bash
cd "/Users/.../苍茫云海间"
git add 50-项目/主网自动化竞赛/99-工作流/{*.py,*.md}
git commit -m "workflow snapshot YYYY-MM-DD"
```

### 9.3 GitHub 镜像

主要内容（脚本 + 工作流 README）同步到 web 仓库的 `/scripts` 和 `/README.md`，作为远程备份。

---

## 10. 已知问题 / TODO

- [ ] AIHUBMIX 不同模型 JSON 输出兼容性（gpt-4o-mini ✅ / claude / gemini 待测）
- [ ] 试卷页无「未答清单」入口，跳过的题靠「← 上一题」找回
- [ ] 惩罚清单"再来一次"统计只在本会话累积，不跨会话
- [ ] 系统平台、达梦、D60 题答案 v1 未生成
- [ ] iPad 端键盘输入未测试
- [ ] `gen_drill_url.py` 还没接入到 exam.html 自动跳转（用户希望批卷完自动跳惩罚清单）
- [ ] 试卷页面没有「跳到指定题号」功能

---

## 11. 紧急救援

| 出问题 | 怎么办 |
|---|---|
| Web 页面挂了 / 错版本 | `cd web && git checkout <上个 tag> && git push -f origin main` |
| 资料库索引坏了 | 删 `03资料库/资料库索引.json`，重跑 `build_index.py` |
| 薄弱点污染了顶层 JSON | `cd 04实操题集/操作系统 && cp 薄弱点.json 薄弱点.bak.json` 再清 |
| iCloud 同步冲突 | Obsidian 设置里手动 resolve |
| GitHub 推不动 | 看 `gh auth status`，token 可能过期 |
