// 自动生成自 outline.json by build_outline_md.py — 勿手改
window.OUTLINE_DATA = {
  "version": "v0.1",
  "generated": "2026-05-18",
  "comment": "D6.0 备考考点大纲 SSOT。Tag 命名规范：KP::学科::N阶段::考点名，录题时把 tag 复制到 Anki Note 的 Tags 字段（可多个）。keywords 给录入工具自动推荐用。",
  "categories": [
    {
      "id": "linux",
      "name": "一、Linux 系统基础",
      "tag_segment": "Linux",
      "fallback_subject": "操作系统",
      "sections": [
        {
          "id": "linux_intro",
          "name": "1.1 入门：基础命令与日常操作",
          "tag_segment": "1入门",
          "kps": [
            {
              "id": "linux_intro_perm",
              "name": "权限管理",
              "desc": "rwx、属主属组、chmod/chown/chgrp",
              "keywords": [
                "chmod",
                "chown",
                "chgrp",
                "rwx",
                "属主",
                "属组",
                "权限"
              ]
            },
            {
              "id": "linux_intro_disk",
              "name": "磁盘存储",
              "desc": "df -h、df -i、du -sh、分区挂载卸载",
              "keywords": [
                "df",
                "du",
                "mount",
                "umount",
                "分区",
                "挂载",
                "磁盘"
              ]
            },
            {
              "id": "linux_intro_proc",
              "name": "进程服务",
              "desc": "ps、top、kill、killall",
              "keywords": [
                "ps",
                "top",
                "kill",
                "killall",
                "进程"
              ]
            },
            {
              "id": "linux_intro_net",
              "name": "网络时间",
              "desc": "ping、telnet、netstat、ifconfig、ip addr、date",
              "keywords": [
                "ping",
                "telnet",
                "netstat",
                "ifconfig",
                "ip addr",
                "date",
                "ss"
              ]
            },
            {
              "id": "linux_intro_cron",
              "name": "crontab定时任务",
              "desc": "crontab、分时日月周语法",
              "keywords": [
                "crontab",
                "cron",
                "定时任务"
              ]
            },
            {
              "id": "linux_intro_log",
              "name": "日志基础",
              "desc": "/var/log、grep 过滤",
              "keywords": [
                "/var/log",
                "grep",
                "日志",
                "journalctl"
              ]
            },
            {
              "id": "linux_intro_shell",
              "name": "Shell基础",
              "desc": "变量、参数、管道、重定向、条件组",
              "keywords": [
                "bash",
                "shell",
                "管道",
                "重定向",
                "变量",
                "参数"
              ]
            }
          ]
        },
        {
          "id": "linux_advanced",
          "name": "1.2 进阶：Shell 脚本与系统优化",
          "tag_segment": "2进阶",
          "kps": [
            {
              "id": "linux_adv_text",
              "name": "高级文本sed_awk_find",
              "desc": "sed、awk、find",
              "keywords": [
                "sed",
                "awk",
                "find",
                "xargs"
              ]
            },
            {
              "id": "linux_adv_resource",
              "name": "资源管理",
              "desc": "top、vmstat、iostat、sar、lsof",
              "keywords": [
                "vmstat",
                "iostat",
                "sar",
                "lsof",
                "free",
                "mpstat"
              ]
            },
            {
              "id": "linux_adv_service",
              "name": "服务管理",
              "desc": "service、systemctl、开机自启",
              "keywords": [
                "systemctl",
                "service",
                "systemd",
                "开机自启",
                "chkconfig"
              ]
            },
            {
              "id": "linux_adv_ntp",
              "name": "时间同步",
              "desc": "NTP 服务、ntpdate",
              "keywords": [
                "ntp",
                "ntpdate",
                "chrony",
                "时间同步"
              ]
            },
            {
              "id": "linux_adv_pkg",
              "name": "压缩传输",
              "desc": "tar、gzip、scp、sftp、md5sum",
              "keywords": [
                "tar",
                "gzip",
                "scp",
                "sftp",
                "md5sum",
                "rsync"
              ]
            }
          ]
        },
        {
          "id": "linux_ops",
          "name": "1.3 运维：故障排查与维护",
          "tag_segment": "3运维",
          "kps": [
            {
              "id": "linux_ops_diag",
              "name": "故障定位",
              "desc": "日志→权限→配置→进程",
              "keywords": [
                "排查",
                "定位",
                "日志",
                "dmesg"
              ]
            },
            {
              "id": "linux_ops_common",
              "name": "常见故障",
              "desc": "服务无法启动、磁盘满、CPU 高、OOM、网络不通",
              "keywords": [
                "OOM",
                "磁盘满",
                "CPU",
                "无法启动",
                "网络不通"
              ]
            },
            {
              "id": "linux_ops_file",
              "name": "文件异常",
              "desc": "权限错误、误删恢复",
              "keywords": [
                "误删",
                "恢复",
                "权限错误",
                "extundelete"
              ]
            },
            {
              "id": "linux_ops_auto",
              "name": "自动化",
              "desc": "备份、巡检、日志切割",
              "keywords": [
                "logrotate",
                "备份",
                "巡检",
                "自动化"
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "dm",
      "name": "二、达梦数据库 (DM)",
      "tag_segment": "DM",
      "fallback_subject": "数据库",
      "sections": [
        {
          "id": "dm_intro",
          "name": "2.1 入门：基础认知与常用操作",
          "tag_segment": "1入门",
          "kps": [
            {
              "id": "dm_intro_arch_db",
              "name": "数据库架构",
              "desc": "库、表、行、列、主键外键",
              "keywords": [
                "主键",
                "外键",
                "表",
                "行",
                "列"
              ]
            },
            {
              "id": "dm_intro_arch_dm",
              "name": "达梦架构",
              "desc": "实例、数据库、表空间",
              "keywords": [
                "实例",
                "表空间",
                "tablespace",
                "达梦架构"
              ]
            },
            {
              "id": "dm_intro_sql",
              "name": "基础SQL",
              "desc": "SELECT、INSERT、UPDATE、DELETE",
              "keywords": [
                "select",
                "insert",
                "update",
                "delete",
                "基础sql"
              ]
            },
            {
              "id": "dm_intro_tool",
              "name": "disql工具",
              "desc": "disql 登录、spool、执行脚本",
              "keywords": [
                "disql",
                "spool",
                "脚本执行"
              ]
            },
            {
              "id": "dm_intro_backup",
              "name": "dexp_dimp备份",
              "desc": "dexp 导出、dimp 导入",
              "keywords": [
                "dexp",
                "dimp",
                "逻辑备份",
                "导入导出"
              ]
            }
          ]
        },
        {
          "id": "dm_advanced",
          "name": "2.2 进阶：SQL 高级、权限与约束",
          "tag_segment": "2进阶",
          "kps": [
            {
              "id": "dm_adv_sql",
              "name": "高级SQL",
              "desc": "多表关联、子查询、GROUP BY、聚合函数",
              "keywords": [
                "join",
                "子查询",
                "group by",
                "聚合"
              ]
            },
            {
              "id": "dm_adv_tx",
              "name": "事务死锁",
              "desc": "COMMIT、ROLLBACK、行锁、表锁、死锁、阻塞",
              "keywords": [
                "commit",
                "rollback",
                "死锁",
                "行锁",
                "表锁",
                "阻塞",
                "事务"
              ]
            },
            {
              "id": "dm_adv_role",
              "name": "权限角色",
              "desc": "系统权限、对象权限、角色管理",
              "keywords": [
                "grant",
                "revoke",
                "role",
                "角色",
                "权限"
              ]
            },
            {
              "id": "dm_adv_constraint",
              "name": "约束管理",
              "desc": "主键、唯一、非空、外键",
              "keywords": [
                "主键",
                "唯一",
                "非空",
                "外键",
                "约束",
                "constraint"
              ]
            },
            {
              "id": "dm_adv_obj",
              "name": "数据库对象",
              "desc": "视图、索引、序列、触发器、存储过程",
              "keywords": [
                "视图",
                "索引",
                "序列",
                "触发器",
                "存储过程",
                "view",
                "index",
                "trigger"
              ]
            }
          ]
        },
        {
          "id": "dm_ops",
          "name": "2.3 运维：集群、备份恢复、故障处理",
          "tag_segment": "3运维",
          "kps": [
            {
              "id": "dm_ops_dts",
              "name": "DTS数据迁移",
              "desc": "DTS 工具",
              "keywords": [
                "dts",
                "数据迁移",
                "migration"
              ]
            },
            {
              "id": "dm_ops_phy_backup",
              "name": "物理备份",
              "desc": "dmnman、全量/增量/归档备份",
              "keywords": [
                "dmnman",
                "归档",
                "全量",
                "增量",
                "物理备份"
              ]
            },
            {
              "id": "dm_ops_ha",
              "name": "高可用",
              "desc": "DataWatch 主备、DMDSC 集群、DMHS 同步",
              "keywords": [
                "datawatch",
                "dmdsc",
                "dmhs",
                "主备",
                "集群",
                "高可用"
              ]
            },
            {
              "id": "dm_ops_trouble",
              "name": "数据库故障处理",
              "desc": "无法启动、连接失败、锁阻塞、慢 SQL",
              "keywords": [
                "无法启动",
                "连接失败",
                "锁阻塞",
                "慢sql",
                "数据库故障"
              ]
            },
            {
              "id": "dm_ops_security",
              "name": "安全规范",
              "desc": "密码策略、审计、权限最小化",
              "keywords": [
                "密码策略",
                "审计",
                "权限最小化",
                "audit"
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "d6",
      "name": "三/四、D6.0 + SCADA",
      "tag_segment": "D6",
      "fallback_subject": "基础平台",
      "sections": [
        {
          "id": "d6_intro",
          "name": "3.1 入门：架构认知与安装部署",
          "tag_segment": "1入门",
          "kps": [
            {
              "id": "d6_intro_modules",
              "name": "核心模块",
              "desc": "SCADA、FES、人机、平台",
              "keywords": [
                "SCADA",
                "FES",
                "人机",
                "平台模块",
                "核心模块"
              ]
            },
            {
              "id": "d6_intro_deploy",
              "name": "部署模式",
              "desc": "主管、集群、分布式",
              "keywords": [
                "主管",
                "集群",
                "分布式",
                "部署模式"
              ]
            },
            {
              "id": "d6_intro_install",
              "name": "安装步骤",
              "desc": "平台、人机前置、FES 前置采集",
              "keywords": [
                "安装",
                "人机前置",
                "fes前置",
                "部署步骤"
              ]
            },
            {
              "id": "d6_intro_config",
              "name": "基础配置",
              "desc": "hosts、IP 映射、时间同步",
              "keywords": [
                "hosts",
                "ip映射",
                "时间同步",
                "基础配置"
              ]
            },
            {
              "id": "d6_intro_startup",
              "name": "sys_ctl启停",
              "desc": "sys_ctl start/stop/restart",
              "keywords": [
                "sys_ctl",
                "启停",
                "start",
                "stop",
                "restart"
              ]
            }
          ]
        },
        {
          "id": "d6_advanced",
          "name": "3.2 进阶：平台功能、配置与权限",
          "tag_segment": "2进阶",
          "kps": [
            {
              "id": "d6_adv_components",
              "name": "核心组件",
              "desc": "消息总线、文件服务、对象化计算",
              "keywords": [
                "消息总线",
                "文件服务",
                "对象化计算",
                "msgbus"
              ]
            },
            {
              "id": "d6_adv_user",
              "name": "平台权限管理",
              "desc": "用户、用户组、遥控权限",
              "keywords": [
                "用户管理",
                "用户组",
                "遥控权限",
                "grant"
              ]
            },
            {
              "id": "d6_adv_zone",
              "name": "责任区",
              "desc": "定义、划分、绑定设备",
              "keywords": [
                "责任区",
                "设备绑定",
                "zone"
              ]
            },
            {
              "id": "d6_adv_ui",
              "name": "界面配置",
              "desc": "总控台、告警管理、菜单、颜色",
              "keywords": [
                "总控台",
                "告警管理",
                "菜单",
                "颜色配置",
                "界面"
              ]
            },
            {
              "id": "d6_adv_inspect",
              "name": "日常巡检",
              "desc": "服务、进程、端口、磁盘、CPU、内存、日志",
              "keywords": [
                "巡检",
                "端口",
                "磁盘",
                "cpu",
                "内存",
                "巡检脚本"
              ]
            },
            {
              "id": "d6_adv_cfg_fault",
              "name": "配置故障",
              "desc": "hosts 填误、节点名错误、权限不足",
              "keywords": [
                "hosts错误",
                "节点名",
                "权限不足",
                "配置错误"
              ]
            }
          ]
        },
        {
          "id": "d6_ops",
          "name": "3.3 运维：平台运检与故障处理",
          "tag_segment": "3运维",
          "kps": [
            {
              "id": "d6_ops_data",
              "name": "数据故障",
              "desc": "不刷新、采样异常、限值不生效",
              "keywords": [
                "不刷新",
                "采样异常",
                "限值",
                "数据故障"
              ]
            },
            {
              "id": "d6_ops_alarm",
              "name": "告警升级",
              "desc": "无法登录、巡检失败、告警不弹窗",
              "keywords": [
                "告警",
                "弹窗",
                "无法登录",
                "巡检失败"
              ]
            },
            {
              "id": "d6_ops_backup",
              "name": "备份升级",
              "desc": "配置备份、补丁安装、回退方案",
              "keywords": [
                "配置备份",
                "补丁",
                "回退",
                "升级"
              ]
            },
            {
              "id": "d6_ops_scada",
              "name": "SCADA基础",
              "desc": "采集→传输→处理→展示",
              "keywords": [
                "scada",
                "采集",
                "传输",
                "展示",
                "数据流"
              ]
            },
            {
              "id": "d6_ops_datatype",
              "name": "数据类型",
              "desc": "遥测、遥信、SOE、事件",
              "keywords": [
                "遥测",
                "遥信",
                "SOE",
                "事件",
                "yc",
                "yx"
              ]
            },
            {
              "id": "d6_ops_fes",
              "name": "FES配置",
              "desc": "规约配置、通道、装置、点表",
              "keywords": [
                "fes",
                "规约",
                "通道",
                "装置",
                "点表",
                "104"
              ]
            },
            {
              "id": "d6_ops_remote",
              "name": "遥控操作",
              "desc": "操作票、五防、对点、执行确认",
              "keywords": [
                "遥控",
                "操作票",
                "五防",
                "对点",
                "执行确认"
              ]
            },
            {
              "id": "d6_ops_accident",
              "name": "事故推图",
              "desc": "智能告警、事故溯源、CIM 模型",
              "keywords": [
                "事故推图",
                "智能告警",
                "事故溯源",
                "cim",
                "推图"
              ]
            }
          ]
        }
      ]
    }
  ]
};
