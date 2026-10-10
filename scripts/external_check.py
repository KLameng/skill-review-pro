#!/usr/bin/env python3
"""external_check.py — skill-review-pro 的外部权威值溯源核验（v1.5，P0+P1，含 v1.5 去误报）。

背景（P0，GAP-C-14）：
    L1–L5 只保证"内部自洽"，不保证"引用的外部权威值正确"。典型翻车：ACMG 技能 PTEN BA1
    阈值文档内部一致（raw 与括号一致、各表一致），但整值 vs ClinGen 官网差 18 倍
    （技能 0.01，cspec v3.2 为 0.00056）。这是五层全部通过也发现不了的错误。

本脚本把"外部权威值必须可溯源"变成可断言防线：
    1. 识别 SKILL.md / references/*.md 中的**外部权威值声明**——只认"阈值形态"数字：
       ①带比较符（< > ≤ ≥ =）的数字（如 <0.00001、>0.01、≥0.001）；②带百分号（% ％）的数字
       （如 0.002%、0.02%）。普通计数（"5 层""6 项""4 处"）不匹配，避免误报。
    2. 且行上下文命中**阈值专用强词**（阈值/threshold/cutoff/AF/MAF/FAF/popmax/PM2/BA1/BS1/
       minor allele/等位基因频率）——只用证据码/阈值专用词，避免"频率"等宽词把无关数字卷入。
    3. 判断该值是否**绑定来源**：同一行或紧邻 2 行内出现来源标记（URL / cspec / genome.network /
       PMID / ClinGen / VCEP / 版本号 / 年份）。
    4. 输出"外部值清单"：每个外部值 → 数值 / 是否绑定来源 / 是否带版本。未绑定来源 = FAIL
       （外部值无溯源 = 硬伤信号，因为无法判断其是否过期或错误）。
    5. P1 版本过期标记：外部值若绑定版本（vX.Y / cspec vN / 年份），记录该版本；无版本 = WARN
       （提示"外部值未锁版本，权威升版后无法自动触发重审"）。

局限（如实标注）：本脚本**不联网**，无法自动验证外部值对错——它只保证"外部值有来源、有版本、
可溯源"，把"值对不对"留给执行者按来源去权威站核对（配合 L2.5 外部值核验步骤）。

v1.5 去误报（自审外部值层暴露点落地）：
    ① 箭头排除：`->`/`→` 箭头后的数字不再被当作 `>` 比较（如"grep 旧表述 -> 0 命中"的 `-> 0`）；
    ② 示例/教学行豁免：行含示例引导词（如/例如/例：/示例/举例/教学/示意）即跳过该行外部值判定
       （文档拿阈值举例教学，不是真实外部权威值）；
    ③ 行级豁免标记：作者可在示例行内加 `<!-- ext-ignore -->` 手动豁免（如模板用例表）。
    仅对"教学示例/箭头"生效，不误杀真实外部权威值（真实声明行不含示例词）。

用法:
    python external_check.py <被审技能目录>          # 单技能
    python external_check.py --group <技能群根目录>  # 群模式（聚合输出）

输出: 逐项 PASS/WARN/FAIL，退出码 1=有 FAIL（未绑定来源的外部值）。
仅依赖标准库，无网络/命令执行。
"""
import os
import re
import sys

# 阈值形态数字：①带比较符 ②带百分号（普通计数不匹配，防误报）
# v1.5：比较符前排除 `-`/`→`，避免箭头 `->`/`→` 被误当比较符
CMP_RE = re.compile(r"(?<![-→])[<>≤≥]=?\s*\d+(?:\.\d+)?(?:e-?\d+)?")
PCT_RE = re.compile(r"\d+(?:\.\d+)?(?:e-?\d+)?\s*[%％]")
# 阈值专用强词（证据码/阈值词），避免"频率"等宽词误报普通数字
CTX_WORDS = ("阈值", "threshold", "cutoff", "cut-off", "AF", "MAF", "FAF", "popmax",
             "PM2", "BA1", "BS1", "minor allele", "等位基因频率", "过滤等位基因")
# 来源标记：URL / cspec / ClinGen / VCEP / PMID / PMC / 版本 / 年份
SRC_RE = re.compile(
    r"https?://|cspec|genome\.network|clinvar|ClinGen|VCEP|PMID|PMC\d+"
    r"|v\d+\.\d+\.?\d*|20\d{2}|官网|规范|指南|论文|文献"
)
# 版本标记（用于 P1 过期检测）
VER_RE = re.compile(r"(v\d+\.\d+\.?\d*|cspec\s*v?[\d.]+|20\d{2})")
# v1.5 示例/教学行豁免：行含任一引导词即跳过外部值判定（文档举例教学，非真实权威值）
EXAMPLE_WORDS = ("如 ", "如：", "例如", "例：", "示例", "举例", "教学", "示意")
# v1.5 行级手动豁免标记（作者在示例行内加此注释即跳过）
IGNORE_MARK = "<!-- ext-ignore -->"


def iter_md(target):
    files = [os.path.join(target, "SKILL.md")]
    ref = os.path.join(target, "references")
    if os.path.isdir(ref):
        files += [os.path.join(ref, f) for f in sorted(os.listdir(ref)) if f.endswith(".md")]
    return [f for f in files if os.path.exists(f)]


COUNT_UNIT = re.compile(r"[条个处项例人]")


def value_of(line):
    """返回该行匹配到的外部值文本列表（比较符/百分号形态）。

    豁免：整数比较符数字后紧跟计数单位（条/个/处/项/例/人）→ 规模/数量建议（如 ≥10 条、
    ≥2 个），非外部权威值，跳过。
    """
    vals = []
    for m in CMP_RE.finditer(line):
        num = m.group(0)
        after = line[m.end():].lstrip()
        if "." not in num and after and COUNT_UNIT.match(after):
            continue
        vals.append(num.strip())
    vals += [m.group(0).strip() for m in PCT_RE.finditer(line)]
    return vals


def is_ctx(line):
    return any(w in line for w in CTX_WORDS)


def is_src(line):
    return bool(SRC_RE.search(line))


def has_version(line):
    m = VER_RE.search(line)
    return m.group(1) if m else None


def scan_skill(target):
    """扫描单个技能，返回 (fail_list, warn_list, values_list)。"""
    fails, warns, values = [], [], []
    for md in iter_md(target):
        with open(md, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        for i, line in enumerate(lines):
            if IGNORE_MARK in line:          # v1.5 行级手动豁免
                continue
            if not is_ctx(line):
                continue
            if any(w in line for w in EXAMPLE_WORDS):  # v1.5 示例/教学行豁免
                continue
            vals = value_of(line)
            if not vals:
                continue
            rel = os.path.relpath(md, target)
            window = "".join(lines[max(0, i - 1):min(len(lines), i + 3)])
            if is_src(window):
                ver = has_version(window)
                for v in vals:
                    values.append((rel, i + 1, v, "有来源", ver or ""))
                    if not ver:
                        warns.append((rel, i + 1, v, "外部值未锁版本（权威升版后无法自动触发重审）"))
            else:
                for v in vals:
                    values.append((rel, i + 1, v, "无来源", ""))
                    fails.append((rel, i + 1, v, "外部值未绑定来源（无法溯源验证对错/是否过期，须补 URL/cspec/PMID/版本）"))
    return fails, warns, values


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    group_flag = "--group" in sys.argv
    if not args:
        print("用法: python external_check.py <被审技能目录>  |  python external_check.py --group <群根目录>")
        return 2
    target = args[0]
    if not os.path.isdir(target):
        print("FAIL 被审目录不存在:", target)
        return 1

    has_own = os.path.exists(os.path.join(target, "SKILL.md"))
    subs = sorted(d for d in os.listdir(target)
                  if os.path.isdir(os.path.join(target, d))
                  and os.path.exists(os.path.join(target, d, "SKILL.md")))
    is_group = group_flag or (not has_own and len(subs) > 0)

    total_fail = 0
    targets = ([os.path.join(target, s) for s in subs] if is_group else [target])

    for t in targets:
        fails, warns, values = scan_skill(t)
        tag = ("[%s] " % os.path.basename(t)) if is_group else ""
        print("=" * 66)
        print("%s外部权威值核验: %s" % (tag, os.path.basename(t)))
        print("=" * 66)
        if not values:
            print("  (未发现阈值/频率类外部值声明)")
        for rel, ln, num, src, ver in values:
            print("  %s:%d 值=%s  %s %s" % (rel, ln, num, src, ("[版本 %s]" % ver) if ver else ""))
        for rel, ln, num, msg in warns:
            print("  WARN %s:%d 值=%s: %s" % (rel, ln, num, msg))
        for rel, ln, num, msg in fails:
            print("  FAIL %s:%d 值=%s: %s" % (rel, ln, num, msg))
            total_fail += 1

    print("-" * 66)
    print("外部值核验完成: " + ("FAIL 有 %d 处外部值未绑定来源" % total_fail if total_fail
                              else "PASS 全部外部值已绑定来源"))
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
