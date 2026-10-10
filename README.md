# Skill-Review-Pro：AI Skill 质量保障工具（技能复审与行为实证 SOP）

> **给每个 SKILL.md 技能一条可执行、可验证、可发版的质量流水线。**
> 作者：KLameng · MIT License · 中文权威版（main）

## 它是什么

一套**通用、开箱即用**的 SKILL.md 技能复审 / 审核 / 发版前检查 / 行为级评测 / 安全审查作业流程。

当你想确认"这个技能能不能进生产直接用、质量靠不靠谱"时，用它：一个命令跑机器层检查，再按清单做语义复核，输出一份带**问题分级**和**发版门禁**的评审报告。

核心是 **五层复审法**：

| 层 | 审什么 | 怎么判 |
|---|---|---|
| **L1 文档自洽** | 文档写得对不对 | 规则无矛盾、术语一致、流程闭环、触发精准 |
| **L2 逻辑审查** | 能不能照做 | 步骤可执行、代码正确、输入规格、异常兜底（自动化 `static_check.py` / `counts_check.py` / `consistency_check.py`） |
| **L2.5 外部值核验** | 引用的权威值对不对 | 每个外部阈值/规则/法规绑定来源 + 版本，锁升版重审（`external_check.py`） |
| **L3 实战推演** | 文档走查 | 用真实输入从头走链路，记录轨迹找卡点 |
| **L4 行为级实证** | 真跑起来测效果 | 条件式：测试集 + 无技能基线 + 确定性契约 + 重复性 + 精度/召回 |
| **L5 安全红线扫描** | 安不安全 | 凭据外泄 / 动态执行 / 网络外泄 / 持久化 / 破坏性操作 |

配套**持续治理**：registry 累积 + 重评估触发 + 漂移监控 + **修复→复测→清零闭环**（修完重跑、清零才发版）。

## 为什么需要它

SKILL.md 这种"技能化 AI 工具"正在爆发，但**质量保障是空白**：很多技能文档自洽、实际一跑就崩，或引用了过期的权威值、或埋了安全红线。这个工具解决"技能能不能发版"的判断，把质量从"凭感觉"变成"可追溯的流水线"。

## 快速开始

> 依赖：仅 Python 3 标准库，零第三方安装。

```bash
# 一键复审（推荐入口）：一个命令跑完 static/counts/consistency/external 四层机器检查
python scripts/run_review.py <被审技能目录>

# 技能群聚合（根目录无 SKILL.md、含多个子技能时）
python scripts/run_review.py <技能群根目录> --group

# 退出码：0 = 无 FAIL，1 = 有 FAIL（可挂 CI/pre-commit 阻断）
```

一键脚本输出三份产物：
- **Markdown 复审报告**（含问题分级 hard/soft、发版门禁）
- **`review_report.json`**（机器可读，含群聚合与 fixes 字段）
- **`semantic_review_points.md`**（语义复核清单，机器初筛 → 人/AI 语义复核两段式）

## 目录结构

```
skill-review-pro/
├── SKILL.md                  # 技能复审与行为实证 SOP（五层复审法主文档）
├── scripts/
│   ├── run_review.py         # 一键复审入口（四层机器检查合并 + 退出码）
│   ├── static_check.py       # L1/L2/L5 静态检查（frontmatter/引用/反模式/安全红线）
│   ├── counts_check.py       # 数字口径必查（计数声明 vs 实际）
│   ├── consistency_check.py  # 跨文件一致性 + 克隆检测（文本相似度 + 脚本哈希）
│   ├── external_check.py     # L2.5 外部权威值溯源（来源 + 版本锁定）
│   └── gen_report.py         # 报告生成（单技能 / 群聚合 JSON）
├── references/
│   ├── checklist.md          # L1–L5 + 持续治理 详细检查清单
│   ├── cases.md              # 案例库归档规则（强制）
│   ├── ci-guide.md           # CI / pre-commit 接入指引
│   ├── fix-loop.md           # 修复→复测→清零 闭环工作流
│   ├── golden-source-guide.md# L4 金标准来源库（按领域权威来源）
│   └── l4-group-testset-template.md  # 技能群级 L4 测试集模板
├── LICENSE                   # MIT
└── README.md                 # 本文档
```

## CI 接入

`run_review.py` 退出码天然可被 CI 判定（0=通过 / 1=阻断）。把每次技能变更自动复审，持续防漂移。示例见 `references/ci-guide.md`。

## 本仓库怎么用

- 作为**独立工具**：clone 后用 `run_review.py` 审你的任意 SKILL.md 技能。
- 作为**规范**：把五层复审法 + 清单抄进你的技能开发流程，作为发版门禁。

## 许可与致谢

- **MIT License**，署名 KLameng <911712412@qq.com>。
- 与姊妹项目 **TACT 三轴坐标法**（AI 系统故障定位与合规映射）互补：TACT 负责出事后"归因"，本工具负责发版前"预防"，合起来是 AI 技能的"预防 + 归因"质量闭环。
- 欢迎贡献：见 [CONTRIBUTING.md](CONTRIBUTING.md)。
