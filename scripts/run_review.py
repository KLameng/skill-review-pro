#!/usr/bin/env python3
"""run_review.py — skill-review-pro 的一键复审入口（v1.5，P1 一键化 + 两段式）。

用法:
    python run_review.py <被审技能目录>                 # 单技能
    python run_review.py --group <技能群根目录>          # 群模式
    python run_review.py <目录> --out <输出目录>         # 指定产物目录（默认 <被审目录>/../reviews/）

作用（一个命令跑完全部机器层）:
    1. static_check    —— L2 静态检查 + L5 反模式 / P6 非交付物
    2. counts_check    —— 数字口径核对（文档/数据资产型）
    3. consistency_check —— 跨文件一致性 + P2 克隆检测（文本+脚本哈希）
    4. external_check  —— L2.5 外部权威值溯源（P0/P1）

两段式（P1）:
    机器初筛 = 上面 4 层自动跑；语义复核 = 生成 `semantic_review_points.md`，
    把"机器只能初筛、必须由人/AI 复核"的点显式列成清单（外部值真伪核验、
    克隆对区分共享/真双胞胎、L4 行为实证是否需真跑），复核者照单逐条处理即可。

产物:
    review_<skill>_<date>.md       —— 合并的 Markdown 报告（§8 模板）
    review_<skill>_<date>.json     —— 机器可读报告（并入 registry）
    semantic_review_points.md      —— 两段式语义复核清单（供人/AI 复核）

退出码: 0=无 FAIL（ready 候选）；1=有 FAIL（需处理，可挂 CI/pre-commit 阻断）。
仅依赖标准库；调用同目录的 4 个检查脚本（subprocess 列表参数，无 shell 注入）。
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKS = ["static_check", "counts_check", "consistency_check", "external_check"]

LAYER_LABEL = {
    "static_check": "L2/L5 静态检查 + 反模式 + P6 非交付物",
    "counts_check": "数字口径核对",
    "consistency_check": "跨文件一致性 + P2 克隆检测",
    "external_check": "L2.5 外部权威值溯源",
}


def run(script, target, group):
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, script + ".py")]
    # --group 仅对支持群模式的检查脚本追加；counts_check 只按目录运行（群根目录=target），
    # 追加 --group 会使其误把 "--group" 当目录名，报"被审目录不存在"（v1.5 传参 bug 修复）。
    if group and script in ("static_check", "consistency_check", "external_check"):
        cmd.append("--group")
    cmd.append(target)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return 2, "[超时] %s 运行超时" % script
    except Exception as e:  # noqa: BLE001
        return 2, "[异常] %s: %s" % (script, e)


def count_statuses(text):
    """统计输出中以 PASS/WARN/FAIL/INFO 开头的行数。"""
    c = {"PASS": 0, "WARN": 0, "FAIL": 0, "INFO": 0}
    for line in text.splitlines():
        m = re.match(r"^\s*(PASS|WARN|FAIL|INFO)\b", line)
        if m:
            c[m.group(1)] += 1
    return c


def extract_external_values(text):
    """从 external_check 输出提取待人工/权威站核验的外部值（两段式清单用）。"""
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\S+:\d+)\s+值=(\S+)\s+(\S+)(?:\s+\[版本\s*([^\]]+)\])?", line)
        if m:
            rows.append({"loc": m.group(1), "val": m.group(2),
                         "src": m.group(3), "ver": m.group(4) or ""})
    return rows


def extract_clone_pairs(text):
    """从 consistency_check 输出提取克隆对（两段式清单用）。"""
    pairs = []
    for line in text.splitlines():
        m = re.search(r"克隆对:\s*(\S+)\s*[↔].*?(\S+)\s*相似度\s*(\d+)%", line)
        if m:
            pairs.append((m.group(1), m.group(2), m.group(3)))
    return pairs


def semantic_review_points(texts, skill):
    """生成两段式的语义复核清单：机器只能初筛、必须由人/AI 复核的点。"""
    lines = ["# 语义复核清单（两段式 · 由人/AI 复核）",
             "",
             "> 机器初筛已完成（static/counts/consistency/external）。以下点机器**不能**替你做最终判定，",
             "> 必须由复核者（人 / AI）逐条处理后再发版。本清单由 run_review.py 自动生成。",
             "",
             "## 1. 外部值真伪核验（脚本只保证'可溯源'，不保证'值对'）",
             ""]
    ev = extract_external_values(texts.get("external_check", ""))
    if ev:
        for r in ev:
            ver = r["ver"]
            lines.append("- `%s` 值=%s %s%s：按来源去权威站核验取值对错与是否过期；核验结论写回报告'外部值核验'字段"
                         % (r["loc"], r["val"], r["src"], ("[版本 %s]" % ver) if ver else ""))
    else:
        lines.append("- （external_check 未报外部值，或均为示例已豁免——无待核验外部值）")
    lines += ["", "## 2. 克隆对区分（共享通用 helper vs 真双胞胎）", ""]
    pairs = extract_clone_pairs(texts.get("consistency_check", ""))
    if pairs:
        for a, b, sim in pairs:
            lines.append("- `%s ↔ %s`（文本相似度 %s%%）：判定是'共享通用脚本'还是'冗余双胞胎'；真双胞胎决定是否合并")
    else:
        lines.append("- （consistency_check 未报克隆对）")
    lines += ["", "## 3. L4 行为实证（条件式 · 是否需真跑）", "",
              "- 判画像：文档型 → L4 N/A；数据资产/行为/脚本型 → 用金标准回归 / 真跑验证（见 golden-source-guide.md）。",
              "- 若被审技能输出可契约核对且后果严重（临床/金融/安全），L4 必跑：建 ≥20 用例或单证据码回归，算精度/召回。",
              "", "## 4. 其他需人工判断的 soft", "",
              "- 通读 SKILL.md 全文做 L1/L3 走查（规则矛盾、流程闭环、触发精准度）。",
              "- 逐条核对 open soft 的 `状态/修复时限`（超 2 个版本周期未修升级为 hard 候选）。",
              ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="skill-review-pro 一键复审")
    ap.add_argument("target")
    ap.add_argument("--group", action="store_true", help="群模式")
    ap.add_argument("--out", default="", help="产物目录（默认 被审目录 的上级/reviews/）")
    args = ap.parse_args()

    if not os.path.isdir(args.target):
        print("FAIL 被审目录不存在:", args.target)
        return 1

    name = os.path.basename(args.target.rstrip("\\/"))
    today = datetime.date.today().isoformat()

    texts = {}
    counts = {}
    total_fail = 0
    print("=" * 66)
    print("一键复审: %s（%s）" % (name, "群模式" if args.group else "单技能"))
    print("=" * 66)
    for script in CHECKS:
        rc, out = run(script, args.target, args.group)
        c = count_statuses(out)
        texts[script] = out
        counts[script] = c
        total_fail += c["FAIL"]
        print("\n-- %s（%s）--" % (script, LAYER_LABEL[script]))
        print("   PASS=%d WARN=%d FAIL=%d 退出码=%d" % (c["PASS"], c["WARN"], c["FAIL"], rc))
        # 打印 FAIL 明细与 WARN 明细（截断过长）
        shown = 0
        for line in out.splitlines():
            if re.match(r"^\s*(FAIL|WARN)\b", line):
                print("   " + line.strip()[:160])
                shown += 1
                if shown >= 20:
                    print("   …（其余省略）")
                    break

    # ---- 产物目录 ----
    if args.out:
        out_dir = args.out
    else:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(args.target)), "reviews")
    os.makedirs(out_dir, exist_ok=True)

    # ---- Markdown 报告 ----
    gate = "cleared" if total_fail == 0 else "not cleared"
    md = [
        "## Skill Review Report: %s" % name,
        "",
        "**Trigger**: TRIGGER_01（一键复审）",
        "**画像**: （由执行者按 §3 判定）",
        "**L4 判定**: （由执行者按 §3 判定）",
        "**Checklist**: 机器层见下（语义层由复核清单跟踪）",
        "",
        "### 机器初筛结果",
        "",
        "| 层 | PASS | WARN | FAIL |",
        "|---|---|---|---|",
    ]
    for script in CHECKS:
        c = counts[script]
        md.append("| %s | %d | %d | %d |" % (LAYER_LABEL[script], c["PASS"], c["WARN"], c["FAIL"]))
    md += ["", "### Gate", "",
           "Hard: %d -> [%s]" % (total_fail, gate),
           "Open soft / 语义复核: 见 `semantic_review_points.md`",
           "Conclusion: %s" % ("not ready" if total_fail else "ready（语义复核通过后）"),
           "",
           "> 由 `run_review.py` 自动生成。语义复核清单见同目录 `semantic_review_points.md`。",
           ""]
    md_path = os.path.join(out_dir, "review_%s_%s.md" % (name, today))
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))

    # ---- JSON 报告 ----
    report = {
        "skill": name,
        "version": "",
        "trigger": "TRIGGER_01",
        "profile": "",
        "l4_applies": None,
        "date": today,
        "machine": {s: counts[s] for s in CHECKS},
        "hard_fail_total": total_fail,
        "gate": {"hard_cleared": total_fail == 0,
                 "semantic_review": "pending",
                 "conclusion": "ready" if total_fail == 0 else "not_ready"},
    }
    json_path = os.path.join(out_dir, "review_%s_%s.json" % (name, today))
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    # ---- 两段式语义复核清单 ----
    sp_path = os.path.join(out_dir, "semantic_review_points.md")
    with open(sp_path, "w", encoding="utf-8") as fh:
        fh.write(semantic_review_points(texts, name))

    print("\n" + "=" * 66)
    print("产物已写入: %s" % out_dir)
    print("  - %s" % os.path.basename(md_path))
    print("  - %s" % os.path.basename(json_path))
    print("  - %s" % os.path.basename(sp_path))
    print("一键复审完成: " + ("FAIL 需处理" if total_fail else "机器层全部通过（语义复核后发版）"))
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
