# 主网自动化竞赛 · 训练系统

> 一个为浙江主网自动化竞赛设计的网页刷题系统。  
> 基于 Obsidian vault 题集 + Python 脚本 + GitHub Pages。

🌐 **训练入口**：https://aerfagogogo.github.io/zhuwang-type-drill/

---

## 🌊 工作流

```mermaid
flowchart LR
    A([📝 录题<br/>到 vault]) --> B([🔄 刷新题库<br/>一键脚本])
    B --> C([💻 进网页<br/>训练中心])
    C --> D([❌ 错题<br/>自动汇总])
    D --> E([✦ 特训<br/>AI 变式题])
    E --> C

    style A fill:#fff7ed,stroke:#fb923c,stroke-width:2px
    style B fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    style C fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    style D fill:#fee2e2,stroke:#ef4444,stroke-width:2px
    style E fill:#ede9fe,stroke:#8b5cf6,stroke-width:2px
```

每天的训练就是这条线：录题 → 刷新 → 训练 → 错题 → 特训。

---

## 🏗️ 数据流

```mermaid
flowchart TD
    Q[("📁 04 题集<br/>vault MD")]
    KP[("📁 03 资料库<br/>PDF / KP")]

    Q --> BE["build_exam_data.py"]
    BE --> EJ["exam_data.json"]
    EJ --> WEB["🌐 GitHub Pages<br/>(训练中心 + 试卷)"]
    WEB --> U["👤 浏览器训练"]

    U -.错题存 localStorage.-> U
    U -.卡了喊 Claude.-> CL["🤖 Claude"]
    CL -.查.-> KP
    CL -.写答案.-> Q

    style Q fill:#fef3c7,stroke:#f59e0b
    style KP fill:#fef3c7,stroke:#f59e0b
    style BE fill:#e0e7ff,stroke:#6366f1
    style EJ fill:#dcfce7,stroke:#16a34a
    style WEB fill:#dbeafe,stroke:#3b82f6
    style U fill:#fce7f3,stroke:#be185d
    style CL fill:#fae8ff,stroke:#a855f7
```

- **本地 (vault)**：题集和资料库都在 Obsidian 里。
- **脚本**：`build_exam_data.py` 把 MD 题集 → JSON。
- **网页**：纯静态站，所有训练状态用 `localStorage` 存浏览器。
- **Claude**：碰到不会的题让我查 KP / 资料库回答。

---

## 🎯 口令字典（你说 → 我做）

| 你说 | 我做 |
|---|---|
| **「刷新题库」** | 跑 `bash refresh_exam.sh`（build + commit + push） |
| **「为 <学科> 批量生成答案」** | 读资料库 → 给每题写草稿答案 |
| **「修 <学科>-NNN 答案：<问题>」** | 改 MD → 刷新题库 → 推 |
| **「出 <学科> 惩罚清单」** | `punishment.py gen <学科> 3` |
| **「惩罚检查 <学科>」** | `punishment.py check <学科>` |
| 粘训练 JSON | 找 `flagged` 修答案；找 `wrong/dontknow` 更薄弱点 |

---

## 📦 入库

题集放在 `04实操题集/<学科>/`，**一题一文件**：

```
04实操题集/
├── 操作系统/      57 题
├── 系统平台/      76 题
├── 数据库/        34 题
├── 基础平台/      54 题
├── 网络分析/      14 题
├── 稳态监控/      28 题
├── 综合智能告警/   7 题
└── 调度数据网/     2 题
```

**frontmatter 模板**：
```yaml
---
id: <学科>-NNN
学科: <学科>
题源: <来源 第X题>
关联KP: "[[KP1]], [[KP2]]"
tags: [命令名, 业务词]
---
```

**正文骨架**：`## 题面` → `## 答案`。仅此两段。

各学科答案格式细则见 vault 顶层 README。

---

## 🚀 训练

| 入口 | 用途 |
|---|---|
| **训练中心** https://aerfagogogo.github.io/zhuwang-type-drill/ | 主页 · 学科卡片仪表盘 |
| **试卷训练** `.../exam.html` | 答题 + API 批卷 + 内嵌盲敲 |
| **速记本** `.../notes.html` | 零碎知识点（不绑题） |

**批卷**：用 AIHUBMIX gpt-4o-mini，每题 ≈ ¥0.001。  
**首次设置**：在「🔧 高级设置」里填 API Key，本地存 localStorage。

**试卷标记按钮**：

| 按钮 | 含义 |
|---|---|
| ← 上一题 / ⏭ 跳过 | 导航 |
| ❌ 不会 | 进薄弱点 |
| ⚠️ 答案有误 | 标记反馈 |
| 提交批卷 | API 评分 |

`correct_streak >= 3` 视为过关。

---

## 🛠️ 脚本一览

```
99-工作流/
├── refresh_exam.sh         一键：build + commit + push
├── build_exam_data.py      MD 题集 → exam_data.json
├── build_index.py          资料库索引（PDF/DOC 全文抽取）
├── punishment.py           盲敲惩罚清单生成/检查
├── gen_drill_url.py        生成盲敲 URL
└── fix_tags.py             修复 tag 格式
```

---

## 📌 版本

| Tag | 日期 | 内容 |
|---|---|---|
| v1.0 | 2026-05-15 | **当前** · UI 改造：Vibe Island 风格学科卡片仪表盘 |
| v0.6 | 5/14 | 速记本 + 训练页导出 |
| v0.5 | 5/14 | 一站式（API 批卷 + 内嵌盲敲） |
| v0.3 | 5/13 | 试卷训练 v1 |
| v0.1 | 5/13 | 打字训练初版 |

**回滚**：
```bash
cd web && git checkout v0.6 && git push -f origin main
```

**项目地址**：https://github.com/aerfagogogo/zhuwang-type-drill
