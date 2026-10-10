---
name: skill-review-pro
version: 1.5.2
description: >-
  技能复审与行为实证 SOP。适用于所有 SKILL.md 形式技能的文档质量复审、逻辑审查、行为级实证、安全红线扫描与发版前检查——检查自洽性、逻辑可执行、触发精准度、数字口径、运行时正确性与安全反模式，不含技能价值或方向评价。支持技能群/多技能聚合扫描与跨文件一致性校验。
  五层复审法：L1 文档自洽 → L2 逻辑审查 → L2.5 外部权威值核验 → L3 实战推演 → L4 行为级实证（条件式）→ L5 安全红线扫描，配持续治理（registry + 重评估）。P0 外部值可溯源、P1 外部升版重审、P2 克隆检测（文本+脚本哈希）、P3 文档随包、P4 群级模式识别、P5 临床轻量 L4、P6 非交付物检查。
  支持**一键复审**（`scripts/run_review.py` 一个命令跑全部机器层 + 生成语义复核清单）与两段式（机器初筛 + 人/AI 语义复核），可接入 CI/pre-commit/定时重审。
  当用户说"复审这个技能""审核SKILL.md""检查技能质量""发版前检查""行为级评测这个技能""安全审查这个技能""一键复审""跑一遍检查"时使用。
---

# 技能复审与行为实证 SOP（skill-review-pro）

> 通用技能复审标准作业流程：文档自洽 → 逻辑审查 → 实战推演 → 行为级实证 → 安全红线 → 持续治理。
> 版本：v1.5.2（v1.5.1 修复 run_review.py 群模式 counts_check 传参 bug + 本次将群模式 counts_check 增强为逐个对子技能运行，真正审到每个技能的数字口径）

---

## 1 技能定位

本技能是**所有 SKILL.md 形式技能的通用复审 / 审核 / 发版前检查 / 行为级评测 / 安全审查**作业流程。

核心方法论：**五层复审法**，配合：

- **取舍原则**（价值 × 维护税，决定每层是否启用）
- **技能画像分流**（文档型 / 数据资产型 / 脚本型 / 行为型 / 混合型）
- **群/多技能聚合**（v1.2：技能群根目录一键聚合扫描 + 跨技能一致性）
- **问题分级**（hard / soft）+ **发版门禁**
- **soft 闭环**（生命周期 + 时限 + 超期升级）
- **修复→复测闭环**（v1.2：fixes[] 记录 + verify_command + 清零判定，见 `references/fix-loop.md`）
- **案例库**（强制归档）
- **机器可读输出**（review_report.json，含群聚合与 fixes 字段）+ **持续治理 registry**

本 SOP 是强制流程。未通过复审的技能不得发版。

**复审输入**：被审技能目录（含 SKILL.md）路径由用户点名或上下文定位；SKILL.md 必须完整读取全文，不得只读摘要或凭印象复审。多文件技能按 §3 画像适配补读 references / scripts。

**异常处理**：被审技能目录不存在、SKILL.md 缺失或读取失败 → 报告中标注"阻塞"，说明原因与已尝试动作，不得声称已通过。阻塞未解除前不得进入发版门禁。

---

## 2 取舍原则（先定标准再干活）

每层能力是否启用，用**两把尺子**判定，避免"为加而加"拖慢流程：

1. **价值 = 输出确定性 × 后果严重性**
   - 输出是否确定性可核对（分类、格式、结果字段、schema）？
   - 是否有可核对的金标准 / 预期输出？
   - 后果严重性（临床 / 金融 / 安全 > 文档 / 创作）？
2. **维护税 = 每次复审的额外成本 + 长期维护负担**

**规则**：

- 三项确定性 / 后果全高 → 对应层**必跑**；
- 部分满足 → **可选**，由执行者按维护税取舍；
- 纯文档 / 创作型 → 标注 **N/A**，**必须保持轻快**，不得因加层拖慢每次复审。
- 凡只对少数技能有效、却每次复审都加税的能力 → **条件式启用**。

---

## 3 技能画像与 L4 适用性

复审前先判定被审技能画像，据此分配各层权重；**不适用项显式标记 N/A 并附理由，不得假装通过**。

| 画像 | 判定 | 检查项适配 |
|---|---|---|
| 文档型 | 仅 SKILL.md + 纯文档/创作/说明性数据，输出**不可契约核对**（无金标准可实证） | L1/L2/L3 重点；**L4 N/A**（无金标准可实证）；L5 静态扫描仍适用；重点数字口径跨文件一致 |
| 数据资产型 | 文档 + 数据资产，**无执行脚本**，但输出**可契约核对**（坐标库+校准集/golden、crosswalk、schema、金标准样例集、映射表等） | L1/L2/L3 重点；**L4 必跑**（用金标准样例集跑回归算命中率/装下率，非运行执行代码）；L5 静态扫描适用；数字口径用 `counts_check.py` 必查 |
| 脚本型 | 含 `scripts/` 或嵌入可执行代码块 | L1-L5 全部适用；L2 自动化静态检查、L4 行为实证为重点 |
| 行为型（确定性高后果） | 有执行引擎/脚本，输出可契约核对、有金标准、后果严重（临床/金融/安全/判定） | **L4 必跑**；L5 必跑；L1-L3 照常 |
| 混合型 | 文档 + 脚本均有 | 全部适用；脚本部分按脚本型执行 |

**画像判定要点**：数据资产型与文档型的边界 = **输出是否可契约核对**（是否有金标准样例集/权威标签可对）。坐标分类法、跨地图映射、schema、合规义务表等"带判定输出的数据资产"技能 → 数据资产型；纯说明/创作文档 → 文档型。数据资产型与行为型的边界 = **有无执行脚本/引擎**。

**L4 适用性判定**（值不值得跑行为实证）：判定结果写入报告"L4 判定"行。

1. 输出是否确定性可核对？
2. 是否有可核对金标准 / 预期输出？
3. 后果严重性是否高？

三项全"是" → **L4 必跑**；部分 → 可选；纯文档/创作 → **N/A**。

**画像与 L4 的一致性（统一判据）**：L4 适用性三问对**所有画像统一生效**，不受画像分流一刀切——数据资产型/行为型只要"输出可契约核对 + 有金标准"即 **L4 必跑**（数据资产型的实证方式 = 用自带金标准样例集跑回归，算命中率/装下率，不要求有执行脚本）；仅纯文档/创作型（无金标准可核对）才 **N/A**。**画像表与 L4 三问冲突时，以 L4 三问为准。**

执行规则：

1. 画像判定结果写入报告（Trigger 行下注明画像）。
2. N/A 项计入报告计数，格式"X passed / Y N/A / Z pending"，每条 N/A 必须附一句理由。
3. 文档型 / 数据资产型技能的数字口径检查为**必查项**：SKILL.md 中出现的计数必须与实际条数逐一核对，用 `counts_check.py` 自动化。

---

## 4 五层复审法

执行顺序：L1 → L2 → L3 → （L4 若适用）→ L5 → 分级 → 修复 → 发布 → 归档 → 写入 registry。

### L1 文档自洽（审什么：文档写得对不对）

通读 SKILL.md 检查：frontmatter 完整、规则无矛盾、术语一致、流程闭环、引用核对、触发精准度、设计质量（渐进式披露、上下文效率）。方法与硬伤信号见 `references/checklist.md` L1。

### L2 逻辑审查（审什么 + 怎么判：能不能照做）

检查步骤可执行、代码正确、输入规格、异常兜底、版本无关性、输出规格、交叉引用、代码块逻辑自洽。**同时运行自动化静态检查**：执行 `scripts/static_check.py <被审目录>`，自动核验 frontmatter 合法、引用路径存在（含 `cross_skill_refs` 跨技能引用豁免、跳过代码块内伪链接）、反模式命中；**数字口径必查项执行 `scripts/counts_check.py <被审目录>`**；**跨文件一致性执行 `scripts/consistency_check.py <目录|群>`**（v1.4：计数声明 vs 实际、跨技能引用、显式当前版本自声明、`references/consistency_manifest.json` 术语一致性断言，以及**克隆检测双通道**——SKILL.md 文本相似度（>85%）+ 脚本内容哈希同源，把"圈定表↔子技能映射↔汇总规则"类跨文件矛盾与"文档分叉但执行体同源"双胞胎自动化）。结果并入 L2 与 L5 证据。详见 `references/checklist.md` L2。

> **群/多技能聚合（v1.2）**：`static_check.py <技能群根目录>` 自动识别群（根无 SKILL.md 但有含 SKILL.md 的子目录），一键聚合扫描 N 个成员技能并汇总 FAIL/WARN；`consistency_check.py --group` 同步做群级跨文件一致性。报告用 `gen_report.py --group` 生成群聚合 JSON（含 `subskills[]`、`group_size`）。

> **一键复审（v1.5，推荐入口）**：直接执行 `scripts/run_review.py <被审目录>`（群加 `--group`），
> 一个命令自动跑完 static/counts/consistency/external 四层机器检查，输出合并 Markdown 报告 +
> `review_report.json` + `semantic_review_points.md`（两段式语义复核清单），并按 FAIL 数返回退出码
> （有 FAIL=1，可挂 CI/pre-commit 阻断）。**机器初筛 → 人/AI 语义复核**两段式：脚本只负责能确定判的
> 格式/计数/引用/反模式/外部值溯源，语义层（外部值真伪、克隆对区分、L4 是否真跑）由 `semantic_review_points.md`
> 逐条列出，复核者照单处理。接入 CI 见 `references/ci-guide.md`。

### L2.5 外部权威值核验（v1.3，P0+P1：审外部值对不对）

> L1–L5 保证"内部自洽"，不保证"引用的外部权威值正确"。外部值（ClinGen 阈值、ACMG 规则、
> 法规数值、指南切点）文档内部全一致也可能整体错（案例 C-14：PTEN BA1 内部一致但 vs 官网差 18 倍）。
> **凡技能引用外部权威事实（阈值/规则/法规/指南数值），必须执行本层。**

执行 `scripts/external_check.py <被审目录>`（单技能）或 `--group <群根目录>`（群）：

1. **识别外部值声明**：阈值/频率类数字（如 `<0.00001`、`>0.01`、`0.002%`）且上下文命中
   阈值关键词（AF/MAF/频率/等位基因/BA1/BS1/PM2 等）。
2. **绑定来源**：每个外部值必须紧邻来源标记（URL / cspec / genome.network / PMID / ClinGen / VCEP /
   版本号 / 年份）。**未绑定来源的外部值 = hard**（无法溯源验证对错/是否过期）——不得静默放行。
3. **锁版本（P1）**：外部值应带版本（cspec vX.Y / 年份）；无版本 = WARN，登记"待核验版本"，
   供持续治理触发"外部权威升版→重审"。
4. **取值正确性由执行者按来源去权威站核验**（脚本不联网，只保证"可溯源"）；核验结果与结论写入报告
   "外部值核验"字段。

结果并入 L2 证据。详见 `references/checklist.md` L2.5。

### L3 实战推演（文档走查，非运行时）

化身执行 agent，用真实输入从头走一遍文档链路，找卡点、需临场发挥点、无留痕删除、口径不一致。**明确边界：L3 是文档走查，不是运行时实证；需要真跑验证时走 L4**。详见 `references/checklist.md` L3。

**L3 走查留痕（可复核性）**：走查必须记录**轨迹**——每条链路记"输入 → 每步动作 → 产物/卡点"四列；"口径一致 / 卡点清零"结论必须引用该轨迹中的具体条目，不得只写结论。走查轨迹并入报告或存档（报告加 `walkthrough` 字段）。

### L4 行为级实证（条件式：把技能真跑起来测效果）

仅当 §3 判定 L4 适用时执行。步骤：

1. **构建测试集**：正/负触发样本、任务场景、边界、历史 bug；有金标准时用权威标签（不得自编）。规模建议 ≥20 条或按可用金标准定。**数据资产型优先复用技能自带金标准样例集/校准集。** 金标准来源见 `references/golden-source-guide.md`（v1.2，按领域给权威来源建议）。
2. **无技能基线对照**：同一批任务分别"不带技能"与"带技能"跑，对比成功率、错误类型。
3. **确定性契约检查**：脚本核验输出格式、文件、字段、schema、目录是否符合约定。
4. **重复运行可靠性**：同一用例跑 N≥3 次，检查结果稳定性。
5. **精度 / 召回**：有金标准时计算。
6. **成本 / 时延代理**：token 数、耗时做相对指标，**明确标注非真实计费**。
7. **结果留档**：写入 `review_report.json` 的 `behavior` 字段与持续治理 registry。

通过阈值由执行者按技能后果严重性设定并在报告注明；临床/金融/安全类技能阈值从严。详见 `references/checklist.md` L4。

> **群级 L4（v1.2）**：多子技能协作的技能群，在单技能测试外另做**群组合逻辑回归**——沉淀互斥矩阵/联合规则/分值系统为机读契约，从金标准抽"证据码+等级→预期分级"用例，跑三域（致病/良性/边界）与双方案（经典+分值）对齐。模板见 `references/l4-group-testset-template.md`。

### L5 安全红线扫描（怎么判：安不安全）

对技能目录执行静态扫描，检查：凭据/密钥访问、网络外泄形态、混淆（base64/hex/minified）、动态执行（eval/exec/管道下载）、持久化（后门/自启）、破坏性操作（rm/覆盖关键文件）。可复用 `scripts/static_check.py` 的反模式扫描结果。命中任一红线 → 至少记 soft，高风险（凭据外泄、动态执行、持久化）记 hard。详见 `references/checklist.md` L5。

---

## 5 持续治理（registry + 重评估 + 修复闭环）

复审结束除产出报告外，必须：

1. **写入 registry**：将 `review_report.json` 追加到技能 registry 索引（命名 `reviews/<skill>.json` 累积条目），供趋势与漂移比对。
2. **登记重评估触发**：记录技能下次需重审的触发条件——技能改动、数据/指南升版（如 ACMG 版本更新）、**外部权威值升版（P1：external_check.py 锁定的来源版本过期 / 权威站更新）**、依赖变更、用户点名、或按需设置定时重审（cron）。
3. **漂移监控**：技能版本变化后，对比新旧两轮复审结果，标记新增 hard / soft / 行为阈值下滑。
4. **修复→复测闭环（v1.2）**：对每条 hard/soft 登记到 `fixes[]`（含 `verify_command`），修复后重跑 static_check / consistency_check / 群级 L4，清零判定（hard=0 且 L4 达标且无新增）后才发版。详见 `references/fix-loop.md`。

---

## 6 问题分级

### hard -- 必须修复后才能发版

| 类型 | 判据 |
|---|---|
| 流程断裂 | 某步骤无入口/无产物/无失败出口，执行者必然卡住 |
| 代码错误 | 嵌入代码语法错误、数据结构矛盾，照抄必报错 |
| 规则矛盾 | 文档内部互斥，或数字/计数前后不一致 |
| 载体缺失 | 引用了不存在的脚本/文件/步骤 |
| 静默失效 | 异常路径无报错、无警告，流程显示成功 |
| **行为不达标**（L4） | 确定性契约失败、金标准精度低于设定阈值 |
| **安全红线**（L5） | 凭据外泄、动态执行、持久化等高风险反模式 |

**发版门禁**：hard 清零；且 L4 若适用必须通过设定阈值。

### soft -- 不阻断发版，记录跟踪

| 类型 | 判据 |
|---|---|
| 可操作性 | 步骤含糊、参数说明不足，需临场发挥 |
| 版本硬编码 | 具体数字/名称写死，应参数化 |
| 留痕不足 | 缺日志/清单/警告，结果不可追溯 |
| 防漂移 | 命名规范/目录约定未硬规则化 |
| 声明边界 | 功能触发条件/适用范围未注明 |
| **小样本假精度**（L4） | 测试集过小、分布偏斜，精度数字不可外推 |

### soft 闭环协议

soft 不阻断本次发版，但必须可跟踪，**禁止静默搁置**：

1. **记录**：报告 soft 表每条必带 `状态` 与 `修复时限` 两列。
2. **状态机**：`open → fixed → verified`；或 `open → waived`，waive 必须附理由。
3. **修复时限**：默认"下次发版前复查"——任何 TRIGGER_02/TRIGGER_03 复审开始时，先逐条核对全部 open soft 是否已修；**超过 2 个版本周期仍未修的 open soft 升级为 hard 候选**。
4. **复查触发**：下次发版 / 数据升版 / 框架升级 / 用户点名，任一发生即触发 open soft 复查。

---

## 7 修复与发布协议

1. **同文件编辑严格串行**：同一文件一次只允许一个编辑流，严禁并行修改。
2. **每批编辑后验证**：每改完一批，验证旧表述清零（grep 旧阈值/名称/措辞 -> 0 命中）；同时执行清单计数自检（所有声明计数与清单实际条目一致）。
3. **发版**：修复全部落地后按技能发版流程发布新版本。
4. **发版后端到端验证**：用真实输入把完整链路从头跑一遍，产物与报告逐项核对；复审记录留档；hard 必归档、soft 典型者归档入案例库。

---

## 8 报告模板与机器可读输出

### Markdown 报告

```
## Skill Review Report: [Skill Name]

**Trigger**: TRIGGER_01 / TRIGGER_02 / TRIGGER_03
**画像**: 文档型 / 数据资产型 / 脚本型 / 行为型 / 混合型
**L4 判定**: 必跑 / 可选 / N/A（理由）
**Checklist**: X passed / Y N/A / Z pending（共 N 项）

### Hard Issues (N)
| # | Location | Issue | Notes |

### Soft Suggestions (N)
| # | Location | Issue | 状态 | 修复时限 | Notes |

### Walkthrough（L3 走查轨迹）
| 链路 | 输入 | 每步动作 | 产物/卡点 |

### Behavioral (L4) —— 仅 L4 适用时
测试集规模 / 基线 vs 技能成功率 / 确定性契约 / 重复运行 / 精度·召回 / 成本代理 / 阈值与结论

### External Values (L2.5) —— 仅含外部权威值声明时
未绑定来源的外部值（hard）/ 未锁版本（WARN）/ 按来源核验的结果与结论

### Patterns (P4) —— 仅群级报告
系统性根因：N 个技能共享同类 hard/soft（按类型聚类，见 patterns[]）

### Security (L5)
命中项 / 严重级别 / 处置

### Gate
Hard: X -> [cleared/not cleared]
L4: [passed/not passed/N/A]
Open soft: N
Fixes: N verified / M open（见 fixes[]）
Conclusion: [ready/not ready]
```

### 机器可读输出（review_report.json）

复审完成后**必须同步输出结构化 JSON**（与报告同内容，供 registry 与程序化统计）。骨架可用 `scripts/gen_report.py` 生成，避免格式漂移。v1.2 新增 `subskills[]`（群聚合）、`fixes[]`（修复→复测闭环）、`group_size`（群规模）：

```json
{
  "skill": "[name]",
  "version": "[被审技能版本]",
  "trigger": "TRIGGER_01 | TRIGGER_02 | TRIGGER_03",
  "profile": "document | data_asset | script | behavioral | hybrid",
  "l4_applies": true | false,
  "date": "YYYY-MM-DD",
  "checklist": { "passed": N, "na": N, "pending": N, "total": <由清单实际条目数计算，禁止硬编码> },
  "walkthrough": [ { "链路": "...", "输入": "...", "动作": "...", "产物/卡点": "..." } ],
  "hard": [ { "location": "...", "issue": "..." } ],
  "soft": [ { "id": "S1", "location": "...", "issue": "...", "status": "open | fixed | verified | waived", "deadline": "next_release | immediate" } ],
  "behavior": { "test_set_n": 0, "baseline_success": 0, "skill_success": 0, "deterministic_contract": "pass | fail", "repeat_n": 0, "precision": 0, "recall": 0, "cost_proxy_tokens": 0, "threshold": "...", "conclusion": "pass | fail | na" },
  "security": [ { "pattern": "...", "level": "hard | soft" } ],
  "subskills": [ { "name": "...", "passed": N, "fails": N } ],          // 群聚合（v1.2）
  "group_root": "...", "group_size": N,                                 // 群聚合（v1.2）
  "fixes": [ { "issue": "...", "severity": "hard|soft", "action": "...",
               "verify_command": "...", "status": "open|fixed|verified|waived",
               "verified": false, "evidence": "..." } ],                // 修复闭环（v1.2）
  "archive": [ { "title": "...", "level": "hard | soft", "check": "L4 | L5 | D4 | ...", "profile": "..." } ],
  "gate": { "hard_cleared": true, "l4_passed": true, "open_soft": 0, "conclusion": "ready | not_ready" }
}
```

**存档约定**：JSON 存入工作区，命名 `review_<skill>_<date>.json`，并追加到 registry（§5）。

---

## 9 引用资源

- `references/checklist.md`：L1–L5 与持续治理的详细检查清单、方法与硬伤信号。
- `references/cases.md`：案例库（强制归档目标）。
- `references/golden-source-guide.md`（v1.2）：L4 金标准来源库（按领域给权威来源建议 + 自建样例集规则）。
- `references/l4-group-testset-template.md`（v1.2）：群级 L4 测试集模板（互斥矩阵/联合规则/分值系统→用例表）。
- `references/fix-loop.md`（v1.2）：修复→复测→清零→归档闭环。
- `references/ci-guide.md`（v1.5）：CI 接入指引——pre-commit hook、GitHub Actions、豆包定时重审（cron）三套配置示例。
- `scripts/static_check.py`：L2 自动化静态检查 + L5 反模式静态扫描（含 `cross_skill_refs` 豁免、代码块伪链接跳过、env-key/无 shell subprocess 安全豁免；**支持技能群聚合 `--group`**）。
- `scripts/consistency_check.py`（v1.4）：跨文件一致性扫描——计数声明 vs 实际、跨技能引用、显式当前版本自声明、`references/consistency_manifest.json` 术语一致性断言；**克隆检测双通道**：SKILL.md 文本相似度（>85%）+ 脚本内容哈希同源（捕获文档分叉但执行体相同的双胞胎）。
- `scripts/counts_check.py`：数字口径核对（文档型/数据资产型必查）——提取 SKILL.md 计数声明 + json 结构摘要 + 可选 manifest 精确断言。
- `scripts/external_check.py`（v1.5）：外部权威值溯源核验（P0+P1）——识别阈值/频率类外部值声明，断言其绑定来源与版本，输出"外部值清单"；未绑定来源 = FAIL。v1.5 去误报：箭头 `->`/`→` 排除、示例引导词行豁免、行级 `<!-- ext-ignore -->` 手动豁免。
- `scripts/gen_report.py`：review_report.json 骨架生成（防格式漂移；支持 `--group` 群聚合、`--fix` 修复记录、`--collect` 群级模式识别）。
- `scripts/run_review.py`（v1.5）：**一键复审入口**——一个命令跑完 static/counts/consistency/external 四层机器检查，生成合并 Markdown 报告 + JSON + `semantic_review_points.md`（两段式语义复核清单），退出码可挂 CI/pre-commit。

---

## 10 核心原则

1. **文档自洽 != 逻辑正确** -- L1 是门槛不是终点。
2. **代码必须能跑** -- 嵌入代码不是装饰，执行者会照抄；该真跑时走 L4，不靠"看起来对"。
3. **数字必须对得上** -- 同一数字跨文件一致，计数随清单实际条数。
4. **版本特有值必须参数化** -- 除非随外部事实变化，则显式版本绑定并声明重核验条件。
5. **异常路径必须有兜底** -- 没有兜底 = 执行者必然卡住。
6. **静默是比报错更危险的炸弹** -- 不报错不告警 = 错误一路流入下游。
7. **价值 × 维护税取舍** -- 不为加层而加层，纯文档型保持轻快；高后果技能从严。
8. **行为实证只信真实运行** -- 文档写得漂亮不等于分类/输出正确，临床/金融/安全类必须看实际结果；数据资产型用金标准样例集回归实证，不靠"文档对"代替"输出对"。
9. **画像分流不是一刀切** -- L4 适用与否由"输出可契约核对 + 有金标准"统一判定，画像表只是起点，冲突时以 L4 三问为准。

---

## 11 版本信息

| 版本 | 日期 | 变更要点 |
|------|------|---------|
| v1.0 | 2026-09-29 | 首版：基于 skill-review-sop-v2 演进——五层复审法（新增 L4 行为级实证、L5 安全红线）、取舍原则、画像分流含行为型、持续治理（registry + 重评估）、自动化静态检查脚本 |
| v1.1 | 2026-09-30 | 广谱完善（两轮使用暴露点落地）：①画像分流新增"数据资产型"（文档+可契约核对输出+金标准），修复"文档型一刀切 L4 N/A 致行为实证缺失"盲区；②L4 适用性三问对全画像统一生效（画像表与 L4 三问冲突时以三问为准）；③L3 走查留痕（walkthrough 轨迹可复核）；④新增 `counts_check.py`（数字口径核对：声明提取+json 摘要+可选 manifest 断言）与 `gen_report.py`（报告骨架）；⑤`static_check.py` 支持 `cross_skill_refs` 跨技能引用白名单声明，消除误报；⑥案例库补 C-13 数据资产型画像案例 |
| v1.2 | 2026-10-09 | 群/多技能 + 跨文件一致性 + 静态去误报 + 闭环（用 ACMG 27 技能混合型大群压测暴露点落地）：①`static_check.py` 支持技能群聚合（`--group`，根目录自动识别）；②`static_check.py` L5 去误报——收紧凭据判定为"字面量密钥赋值/密钥文件/密钥形态字面量"、env 读 key 与无 shell 列表参数 subprocess 判安全豁免、跳过代码块伪链接；③新增 `consistency_check.py`（跨文件一致性：计数声明 vs 实际、跨技能引用、显式当前版本自声明、`consistency_manifest.json` 术语一致性断言——把"圈定表↔子技能映射↔汇总规则"类跨文件矛盾自动化）；④`gen_report.py` 群聚合（`--group`/`subskills[]`/`group_size`）+ 修复闭环（`--fix`/`fixes[]`）；⑤新增 `references/golden-source-guide.md`（L4 金标准来源库）、`l4-group-testset-template.md`（群级 L4 模板）、`fix-loop.md`（修复→复测→清零闭环）；⑥JSON 读取 BOM 容错 |
| v1.3 | 2026-10-09 | 外部值核验 + 六项优化（用 ACMG 36 技能大群 + PTEN 阈值 18 倍翻车暴露点落地）：**P0 外部权威值核验层**——新增 `scripts/external_check.py`，识别阈值/频率类外部值声明、断言绑定来源与版本，未绑定来源=hard（补"内部自洽≠外部正确"盲区，案例 C-14）；**P1 外部升版重审触发**——外部值锁版本，权威升版（如 ClinGen cspec 更新）触发重评估；**P2 克隆检测**——`consistency_check.py` 加 SKILL.md 两两相似度比对（>85% 标克隆对）；**P3 文档随包检查**——`consistency_check.py` 检查正文引用的《xx》文档在包内有无随附；**P4 群级模式识别**——`gen_report.py --collect` 聚合子技能 hard/soft 按类型聚类出系统性根因（patterns[]）；**P5 临床轻量 L4**——`golden-source-guide.md` 加"单证据码片段回归"指引（降临床技能 L4 门槛）；**P6 非交付物检查**——`static_check.py` 查 __pycache__/.pyc/临时文件（WARN） |
| v1.4 | 2026-10-10 | P2 克隆检测升级为"文本+脚本哈希"双通道（用 v1.3 重审 ACMG 36 群暴露点落地）：`consistency_check.py` 克隆检测不再只看 SKILL.md 文本相似度（漏掉"文档分叉但共享同一脚本"的双胞胎，如 ev-variant-literature-patient ↔ variant-literature-patient 共用 main.py、相似度<85% 被 v1.3 放过），新增对两技能可执行脚本内容 sha256 比对——共享内容哈希一致的脚本即标"脚本同源克隆对"。实测 4 对文本克隆 → 12 对（新增 8 对脚本同源，需人工区分"共享通用 helper"与"真双胞胎"）；案例库补 C-15 |
| v1.5 | 2026-10-10 | 自审自身暴露点落地（审核技能自身也要被审）：**P0 去误报**——`external_check.py` 修复"教学示例/箭头"误报（①箭头 `->`/`→` 后的数字不再被当比较符；②示例引导词行豁免：如/例如/例：/示例/举例/教学/示意；③行级 `<!-- ext-ignore -->` 手动豁免标记）；**P0 补 version**——SKILL.md frontmatter 增 `version` 字段（self-consistency 自检达标）；**P1 一键化**——新增 `scripts/run_review.py`，一个命令跑完全部机器层 + 生成合并报告 + `semantic_review_points.md` 两段式语义复核清单，退出码可挂 CI；**P1 两段式**——机器初筛 + 人/AI 语义复核（外部值真伪、克隆对区分、L4 是否真跑显式列清单）；**P2 CI 接入**——新增 `references/ci-guide.md`（pre-commit/GitHub Actions/豆包 cron 配置）；案例库补 C-16 |
| v1.5.1 | 2026-10-10 | 修 `run_review.py` 群模式传参 bug：一键复审对 `counts_check` 误传 `--group`（counts_check 不支持群参数），导致群复审时数字口径核对误报"被审目录不存在: --group"。修复为仅对 `static_check`/`consistency_check`/`external_check` 三个支持群模式的脚本追加 `--group`。用修复后的增强版复审 ACMG v14 技能群：外部值溯源 FAIL 18→0、机器层全部通过、语义复核全部豁免，结论 ready。 |
| v1.5.2 | 2026-10-10 | 群模式 counts_check 增强：v1.5.1 虽已修复"counts_check 不误收 --group"，但群模式下仍把**群根目录**直接传给 counts_check——群根无 SKILL.md，数字口径实际审不到任何子技能。本版改为在群模式下对**每个子技能逐个运行 counts_check**（find_subs 枚举含 SKILL.md 的子目录，逐技能扫数字口径），真正审到每个成员技能。用 3 技能临时群实测：counts_check 不再报"被审目录不存在"，static/consistency/external 群聚合正常，一键复审 exit 0。 |
