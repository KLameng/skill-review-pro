#!/usr/bin/env python3
"""counts_check.py — skill-review-pro 的数字口径核对工具。

文档型 / 数据资产型技能复审的必查项载体：核对 SKILL.md 声称计数 vs 数据文件实际条数。

用法:
    python counts_check.py <被审技能目录>

行为:
    1. 提取声明计数: 扫描 SKILL.md 与 references/*.md 中形如 "<int> 项/条/个/坐标/对/维/层/框架/条目"
       的计数声明，列出 (文件, 行号, 数字, 单位, 上下文词)。
    2. 数据文件摘要: 对 references/*.json 输出结构摘要（顶层 list 长度 / dict 键及其子长度），
       并识别常见计数键（framework_versions/forward/reverse/schema/mirrors/domain_symbol/
       examples/opts/pairs/L/M_groups/P_groups 及各框架名）。
    3. 精确断言(可选): 若被审技能存在 references/counts_manifest.json，逐项断言：
       格式 { "标签": {"number": N, "file": "references/x.json", "key": "a.b.c"} }
       用点路径解析 key，断言其长度 == number；解析不到则 FAIL。输出 PASS/FAIL 差异表。

输出: 逐项 PASS/WARN/FAIL；有 manifest 且断言失败时退出码 1。仅依赖标准库，无网络/命令执行。
"""
import json
import os
import re
import sys

CLAIM_RE = re.compile(r"(\d+)\s*(个|项|条|对|维|层|框架|坐标|条目|位)")
COUNT_KEYS = {"framework_versions", "forward", "reverse", "schema", "mirrors", "domain_symbol",
              "examples", "opts", "pairs", "L", "M_groups", "P_groups", "EU_AI_ACT",
              "AGENTIC", "NIST", "OWASP", "ATLAS"}


def iter_md(target):
    files = [os.path.join(target, "SKILL.md")]
    ref = os.path.join(target, "references")
    if os.path.isdir(ref):
        files += [os.path.join(ref, f) for f in sorted(os.listdir(ref)) if f.endswith(".md")]
    return [f for f in files if os.path.exists(f)]


def extract_claims(target):
    claims = []
    for md in iter_md(target):
        with open(md, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                for m in CLAIM_RE.finditer(line):
                    before = line[max(0, m.start() - 12):m.start()]
                    claims.append((os.path.relpath(md, target), i, int(m.group(1)), m.group(2), before.strip()))
    return claims


def summarize_json(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        return "<无法解析: %s>" % e
    if isinstance(data, list):
        return {"len": len(data)}
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if isinstance(v, list):
                out[k] = len(v)
            elif isinstance(v, dict):
                out[k] = {sk: (len(sv) if isinstance(sv, (list, dict)) else "scalar")
                          for sk, sv in list(v.items())[:6]}
            else:
                out[k] = "scalar"
        return out
    return "scalar"


def json_files(target):
    ref = os.path.join(target, "references")
    if not os.path.isdir(ref):
        return []
    return sorted(os.path.join(ref, f) for f in os.listdir(ref) if f.endswith(".json"))


def get_by_path(data, key):
    cur = data
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def run_manifest(target):
    mp = os.path.join(target, "references", "counts_manifest.json")
    if not os.path.exists(mp):
        return None
    with open(mp, encoding="utf-8-sig") as fh:
        manifest = json.load(fh)
    fails = 0
    rows = []
    for label, spec in manifest.items():
        if "number" not in spec:
            continue
        fp = os.path.join(target, spec.get("file", ""))
        if not os.path.exists(fp):
            rows.append(("FAIL", label, "文件缺失 %s" % spec.get("file")))
            fails += 1
            continue
        with open(fp, encoding="utf-8") as fh:
            data = json.load(fh)
        obj = get_by_path(data, spec["key"]) if "key" in spec else None
        actual = len(obj) if isinstance(obj, (list, dict)) else (obj if isinstance(obj, int) else None)
        exp = spec["number"]
        if actual is None:
            rows.append(("FAIL", label, "key '%s' 解析不到" % spec.get("key")))
            fails += 1
        elif actual == exp:
            rows.append(("PASS", label, "%s::%s = %d" % (spec.get("file"), spec.get("key"), actual)))
        else:
            rows.append(("FAIL", label, "声称 %d 实际 %d (%s::%s)" % (exp, actual, spec.get("file"), spec.get("key"))))
            fails += 1
    return rows, fails


def main():
    if len(sys.argv) < 2:
        print("用法: python counts_check.py <被审技能目录>")
        return 2
    target = sys.argv[1]
    if not os.path.isdir(target):
        print("FAIL 被审目录不存在:", target)
        return 1

    print("=" * 66)
    print("一、SKILL.md / references 计数声明")
    print("=" * 66)
    claims = extract_claims(target)
    if not claims:
        print("(未发现 '<数字> 项/条/个/坐标/对/维/层/框架' 形态声明)")
    for rel, ln, num, unit, ctx in claims:
        print("  [%s:%d] %d %s  …%s" % (rel, ln, num, unit, ctx))

    print()
    print("=" * 66)
    print("二、references/*.json 结构摘要（供人工比对声称计数）")
    print("=" * 66)
    for fp in json_files(target):
        print("  %s: %s" % (os.path.basename(fp), summarize_json(fp)))

    res = run_manifest(target)
    if res is None:
        print()
        print("（无 references/counts_manifest.json —— 未做精确断言，请用以上声明+摘要人工核对）")
        return 0
    rows, fails = res
    print()
    print("=" * 66)
    print("三、counts_manifest 精确断言")
    print("=" * 66)
    for status, label, msg in rows:
        print("  %s %s: %s" % (status, label, msg))
    print("-" * 40)
    print("数字口径核对完成: " + ("FAIL 有断言不一致" if fails else "PASS 全部一致"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
