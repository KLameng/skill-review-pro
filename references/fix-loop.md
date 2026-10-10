# 修复→复测闭环（GAP-7，v1.2 新增）

> 目的：复审给出 hard/soft 后，修复是否落地、是否清零、是否引入新问题，必须有结构化闭环，
> 而不是"给了报告就完事"。本文件定义 修复 → 复测 → 清零 → 归档 的工作流。

## 闭环工作流

```
复审出 hard/soft 清单
  → 每条 hard 登记到 review_report.json 的 fixes[]（GAP-6 schema）
  → 修复（同文件串行，每批改完验证旧表述清零）
  → 复测：重跑 static_check / consistency_check / counts_check / 群级 L4 回归
  → 清零判定：hard 全 verified，L4 达阈值，无新增 hard
  → 归档 + 更新 registry（对比上一轮标记漂移）
```

## fixes[] 记录格式（写入 JSON）

每条 hard/soft 必须登记：

```json
{
  "issue": "圈定表缺良性码，良性路径不可达",
  "severity": "hard",
  "action": "圈定表补 BS1/BS2/BS3/BP4/BA1 + 映射补 BA1 + 子技能升格 BA1",
  "verify_command": "python acmg_l4_combine_check_v2.py",
  "status": "fixed",          // open | fixed | verified | waived
  "verified": true,           // 复测通过
  "evidence": "良性域缺口 0，方案A 24/24=100%"
}
```

- `status` 状态机：`open → fixed → verified`，或 `open → waived`（waive 必附理由）。
- `verify_command` 是每条修复的**可重跑复测命令**（static_check / consistency_check / 回归脚本）。
- `verified=true` 必须有 `evidence` 支撑（复测输出摘要），不得空标。

## 复测必跑清单（修复后）

1. `static_check.py <目录|群>` —— frontmatter/引用/L5 无新增反模式；
2. `consistency_check.py <目录|群>` —— 跨文件一致性无新增矛盾；
3. `counts_check.py` —— 数字口径（若适用）；
4. 群级 L4 回归 —— 行为不达标清零（金标准命中率达阈值）；
5. grep 旧表述清零（旧阈值/旧名称/旧 key → 0 命中）。

## 清零判定

- **hard = 0** 且全部 `verified`（或已 `waived` 附理由）；
- **L4**：若适用，金标准命中率 ≥ 设定阈值；
- **无新增 hard**（对比修复前清单）。

满足才可发版，结论 `ready`。否则回到修复步。

## 与 registry / 持续治理联动

- 复测后的新 review_report.json 追加到 `reviews/<skill>.json`；
- 对比上一轮：标记哪些 hard 已清零、哪些 soft 升级为 hard 候选（超 2 个版本周期未修的 open soft）；
- 修复本身若改动规则/阈值，登记重评估触发（指南升版、数据升版）。
