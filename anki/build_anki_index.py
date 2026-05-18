#!/usr/bin/env python3
"""
扫描所有 Anki 牌组 → 输出题库索引 JSON。
- 每个 deck 的卡数 + tag top 分布
- 主题字典（关键词 → AnkiConnect 检索短语）
- 不抓 Front 内容（避免大数据），主题匹配实时查 AnkiConnect

用法: python3 build_anki_index.py
输出: 🎯每日背诵/题库索引.json
"""
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

INDEX_FILE = Path("/Users/sunyiting/Library/Mobile Documents/iCloud~md~obsidian/Documents/苍茫云海间/50-项目/主网自动化竞赛/🎯每日背诵/题库索引.json")

# ---- 主题字典（关键词 → AnkiConnect 检索短语）----
# 修改 TOPICS 来增加/调整主题。Claude 后续可根据新增内容增量更新此字典。
TOPICS = {
    "动态限额": {
        "keywords": ["动态限额", "sca_sec", "断面限额", "限额导入", "sca_sec_cal", "sca_sec_imp", "sca_sec_query_server", "输电断面", "智能稳定限额"],
        "kp_files": ["动态限额_sca_sec.md", "动态限额_输电断面.md"],
        "domain": "D6.0",
    },
    "计划值处理": {
        "keywords": ["计划值", "sca_plan", "KV库", "计划当前值", "矩形插值", "梯形插值", "AGC", "sca_plan_load", "计划电量"],
        "kp_files": ["计划值处理_sca_plan.md"],
        "domain": "D6.0",
    },
    "统计计算": {
        "keywords": ["sca_limit_cal", "sca_cal", "sca_extre_cal", "遥测越限", "设备重过载", "遥测跳变", "极值统计", "积分电量", "实时负载率", "heavy_load", "p_rate"],
        "kp_files": ["遥测越限_sca_limit_cal.md", "统计计算_设备重过载.md", "统计计算_遥测跳变.md", "统计计算_极值与电量.md", "统计计算_实时负载率.md"],
        "domain": "D6.0",
    },
    "周期计算": {
        "keywords": ["周期计算", "yc_change_judge_time", "遥测不刷新", "三相不平衡", "合格率", "is_write_yc_status"],
        "kp_files": ["周期计算框架.md", "周期计算_遥测不刷新插件.md"],
        "domain": "D6.0",
    },
    "采样定义": {
        "keywords": ["采样", "sample_tool", "采样定义", "采样查询", "query_sample"],
        "kp_files": ["采样定义工具.md", "sample_tool.md"],
        "domain": "D6.0",
    },
    "SCADA进程": {
        "keywords": ["sca_analog", "sca_point", "sca_dbg", "sca_guard", "scada_area", "遥测处理", "遥信处理", "事故分闸"],
        "kp_files": ["sca_analog_遥测处理.md", "sca_point_遥信处理.md", "sca_dbg_调试工具.md", "sca_guard.md"],
        "domain": "D6.0",
    },
    "FES进程与工具": {
        "keywords": ["fes_assign", "fes_exchange", "fes_status", "fes_display", "fes_showreal", "fes_simdata", "FES", "前置", "通道表", "通讯厂站", "104规约", "IEC104", "simulator"],
        "kp_files": ["FES主要进程清单.md", "fes_display.md", "fes_showreal.md", "fes_simdata.md", "simulator_前置模拟器.md", "通道表.md", "通讯厂站表.md"],
        "domain": "D6.0",
    },
    "DBI与表": {
        "keywords": ["dbi", "DBI", "断路器表", "前置遥测定义表", "前置遥信定义表", "遥测限值参数表", "数字控制表", "规约表"],
        "kp_files": ["DBI使用技巧.md", "断路器基本信息表.md", "前置遥测定义表.md", "前置遥信定义表.md", "数字控制表.md", "规约表.md"],
        "domain": "D6.0",
    },
    "画图与人机": {
        "keywords": ["Designer", "Explorer", "曲线", "表格视图", "onClick", "脚本", "源JSON编辑器", "云端图形", "Echarts", "treeView"],
        "kp_files": ["Designer列表怎么建.md", "Explorer与Designer.md", "云端图形维护.md"],
        "domain": "D6.0",
    },
    "Linux基础": {
        "keywords": ["ls ", "cd ", "chmod", "chown", "find", "grep", "awk", "sed", "tar", "cat", "vi ", "vim", "ps ", "top ", "lsof", "df ", "du ", "stat ", "uname"],
        "kp_files": ["Linux命令--help快速读法.md"],
        "domain": "Linux",
    },
    "Linux网络": {
        "keywords": ["ifconfig", "route ", "netstat", "ip addr", "ip route", "bond0", "eth", "ping ", "scp ", "ssh ", "NTP", "ntpdate"],
        "kp_files": ["Linux路由表速查与排错.md"],
        "domain": "Linux",
    },
    "crontab": {
        "keywords": ["crontab", "定时任务", "cron"],
        "kp_files": [],
        "domain": "Linux",
    },
    "用户与权限": {
        "keywords": ["useradd", "userdel", "passwd", "chage", "PAM", "pam_tally", "口令", "账户锁定", "权限"],
        "kp_files": [],
        "domain": "Linux",
    },
    "shell脚本": {
        "keywords": ["shell", "脚本", "bash", "alias", "echo", "if then", "for in"],
        "kp_files": [],
        "domain": "Linux",
    },
}


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


def main():
    print("🔍 扫描 Anki 牌组...")
    decks = ank("deckNames")
    print(f"  发现 {len(decks)} 个牌组")

    deck_info = {}
    for deck in sorted(decks):
        if deck == "系统默认":
            continue
        notes = ank("findNotes", query=f'deck:"{deck}"')
        deck_info[deck] = {
            "card_count": len(notes),
            "tags_top": [],
        }
        # 抽 tag 分布（最多 30 张样本，每张拉 tags）
        if notes:
            sample = notes[:min(30, len(notes))]
            try:
                infos = ank("notesInfo", notes=sample)
                tag_counter = Counter()
                for n in infos:
                    for t in n.get("tags", []):
                        tag_counter[t] += 1
                deck_info[deck]["tags_top"] = [t for t, _ in tag_counter.most_common(10)]
            except Exception as e:
                deck_info[deck]["tags_top"] = []
        print(f"  · {deck}: {deck_info[deck]['card_count']} 卡 · top tags: {deck_info[deck]['tags_top'][:3]}")

    # 估算每个主题在哪些 deck 高频出现（仅展示用，不参与搜索逻辑）
    print("\n🎯 估算主题分布（基于 tag 名称模糊匹配，仅参考）...")
    topic_decks = {}
    for topic, info in TOPICS.items():
        keywords = info["keywords"]
        matched = []
        for deck, dinfo in deck_info.items():
            for tag in dinfo["tags_top"]:
                if any(kw.lower() in tag.lower() or tag.lower() in kw.lower() for kw in keywords):
                    matched.append(deck)
                    break
        topic_decks[topic] = sorted(set(matched))

    # 输出 JSON
    output = {
        "version": "1.0",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "decks": deck_info,
        "topics": {
            t: {**TOPICS[t], "ranks_high_in_decks": topic_decks.get(t, [])}
            for t in TOPICS
        },
        "usage": {
            "查找薄弱点相关卡": "用 reset_by_topic.py <主题名>",
            "调字典": "改 build_anki_index.py 顶部 TOPICS dict 后重跑",
            "强制重建": "重跑 build_anki_index.py 即可",
        },
    }

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 索引写入: {INDEX_FILE}")
    print(f"   牌组数: {len(deck_info)}")
    print(f"   主题数: {len(TOPICS)}")


if __name__ == "__main__":
    main()
