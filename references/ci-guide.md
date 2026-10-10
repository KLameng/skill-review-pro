# CI 接入指引（v1.5，P2）

> 目的：把 skill-review-pro 的一键复审挂到发版/提交流程里，让"每次变更都自动审"，
> 持续防漂移。核心入口是 `scripts/run_review.py`——退出码 **0=无 FAIL**、**1=有 FAIL**，天然可被 CI 判定。

## 前置：确认 python 可用

run_review.py 仅依赖标准库，需环境里有 python3。各 CI 平台自带或安装即可。

---

## 方案 A：pre-commit hook（本机/团队本地）

在技能仓库 `.git/hooks/pre-commit`（或集中 pre-commit 框架）加入：

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit —— 提交前一键复审被审技能目录
SKILL_DIR="${1:-.user_skills/skill-review-pro}"
python3 "$SKILL_DIR/scripts/run_review.py" "$SKILL_DIR" --out "$SKILL_DIR/reviews" || {
  echo "复审未通过（有 FAIL）。请先修复或人工判定后再提交。";
  echo "产物: $SKILL_DIR/reviews/review_*.md + semantic_review_points.md";
  exit 1;
}
```

若用 [pre-commit](https://pre-commit.com) 框架，`pre-commit-config.yaml`：

```yaml
repos:
  - repo: local
    hooks:
      - id: skill-review-pro
        name: skill-review-pro 一键复审
        entry: python3 .user_skills/skill-review-pro/scripts/run_review.py
        args: [.user_skills/skill-review-pro, --out, .user_skills/skill-review-pro/reviews]
        language: system
        pass_filenames: false
```

> 提示：有 FAIL 会阻断提交。若某 FAIL 已人工判定为误报/可接受，先修复到清零，或按本技能 §6
> 以 `waived`（附理由）登记，不要把"绕过"写进脚本。

---

## 方案 B：GitHub Actions（开源仓库）

`.github/workflows/skill-review.yml`：

```yaml
name: skill-review-pro
on:
  pull_request:
  push:
    branches: [main]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - name: 一键复审
        run: |
          python3 .user_skills/skill-review-pro/scripts/run_review.py \
            .user_skills/skill-review-pro \
            --out .user_skills/skill-review-pro/reviews
      - name: 上传复审报告
        uses: actions/upload-artifact@v4
        with:
          name: review-reports
          path: .user_skills/skill-review-pro/reviews/
        if: always()
```

> 有 FAIL 时 run_review.py 退出码 1 → 工作流自动标红。报告作为 artifact 可下载查看。

---

## 方案 C：豆包定时重审（无仓库时按周期防漂移）

无需 git 也能"每周/每月自动审一次"，用豆包的**定时任务（doubao-cron-scheduler）**：

1. 触发方式：定时任务每周期执行一次"一键复审"命令；
2. 命令示例：
   `python3 <skill-review-pro>/scripts/run_review.py <被审技能目录> --out <reviews目录>`;
3. 触发后核对：
   - 有新 FAIL → 说明技能或外部权威值（指南/阈值升版）漂移，按本技能 P1/持续治理触发重审与修复；
   - 无 FAIL → 记录本轮已审，维持 ready。
4. 建议频率：临床/金融/安全类技能**月审**或**外部权威升版时**；普通技能按版本周期。

> 配合 P1 外部升版重审：external_check.py 锁定的外部值版本（cspec vX.Y / 年份）一旦过期，
> 定时复审会自动暴露"未锁版本/来源过期"项，触发重新核验。

---

## 兜底原则

- run_review.py 只做**机器初筛**；`semantic_review_points.md` 里的语义项（外部值真伪、克隆对区分、
  L4 是否真跑）**必须由人/AI 复核**后再宣布 ready。CI 阻断的是"机器层 FAIL"，不代表语义层通过。
- CI 里不要对 `--out` 指向被审目录自身之外的共享目录，避免多进程写同一位置冲突；串行执行。
- 失败重试仅限瞬时错误（网络/超时）；"有 FAIL"是真实结论，不要自动重试掩盖。
