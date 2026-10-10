#!/usr/bin/env python3
"""gen_report.py — skill-review-pro 的 review_report.json 骨架生成器（v1.2）。

用法:
    python gen_report.py <技能名> --version <v> --trigger <T> --profile <p> \
        --passed <n> --na <n> --pending <n> [--total <n>] [--out <path>]

单技能扩展参数:
    --fix '<json>'      修复项列表（GAP-7 修复→复测闭环）：
                        格式 [ {"issue":"...","severity":"hard|soft","action":"...",
                               "verify_command":"...","status":"open|fixed|verified|waived","verified":false} ]

群聚合参数（GAP-6）:
    --group <群根目录>   聚合群报告：自动统计子技能数，可配 --subskills 明细
    --subskill '<json>' 单条子技能明细：{"name":"...","passed":n,"na":n,"pending":n,"fails":n}（可重复）

生成符合 skill-review-pro §8 的机器可读 JSON 骨架；hard/soft/security/archive/behavior 留空供填写。
--total 缺省按 passed+na+pending 求和（禁止硬编码总数）。
profile 取值: document / data_asset / script / behavioral / hybrid。
"""
import argparse
import datetime
import json
import os
import sys


def parse_fix(arg):
    if not arg:
        return []
    try:
        val = json.loads(arg)
    except json.JSONDecodeError:
        print("ERROR --fix 不是合法 JSON:", arg, file=sys.stderr)
        sys.exit(2)
    if not isinstance(val, list):
        val = [val]
    return val


PATTERN_KEYS = ["载体", "计数", "克隆", "矛盾", "阈值", "安全", "凭据", "流程",
                "引用", "版本", "外部", "依赖", "缺失", "可操作", "边界", "漂移"]


def classify(issue):
    for k in PATTERN_KEYS:
        if k in issue:
            return k
    return "其他"


def collect_patterns(collect_dir):
    """P4 群级模式识别：从子技能 review_report.json 聚合 hard/soft，按类型聚类出"系统性根因"。

    读 collect_dir 下所有 *.json，提取 hard + soft 的 issue，按类型词聚类，
    返回 [{"type":..., "count":N, "skills":[...]}]（count 降序）——N 个技能共享同类问题
    即系统性根因（如"良性证据不可达""外部值无来源"），便于在群级报告突出共性问题。
    """
    type_count = {}
    skill_type = {}
    for f in sorted(os.listdir(collect_dir)):
        if not f.endswith(".json"):
            continue
        fp = os.path.join(collect_dir, f)
        try:
            with open(fp, encoding="utf-8-sig") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        skill = data.get("skill", os.path.splitext(f)[0])
        issues = [h.get("issue", "") for h in data.get("hard", [])]
        issues += [s.get("issue", "") for s in data.get("soft", [])]
        for iss in issues:
            if not iss:
                continue
            t = classify(iss)
            type_count[t] = type_count.get(t, 0) + 1
            skill_type.setdefault(t, set()).add(skill)
    return [{"type": t, "count": c, "skills": sorted(skill_type[t])}
            for t, c in sorted(type_count.items(), key=lambda x: -x[1])]


def main():
    ap = argparse.ArgumentParser(description="生成 review_report.json 骨架")
    ap.add_argument("skill")
    ap.add_argument("--version", default="")
    ap.add_argument("--trigger", default="TRIGGER_01")
    ap.add_argument("--profile", default="document",
                    choices=["document", "data_asset", "script", "behavioral", "hybrid"])
    ap.add_argument("--passed", type=int, default=0)
    ap.add_argument("--na", type=int, default=0)
    ap.add_argument("--pending", type=int, default=0)
    ap.add_argument("--total", type=int, default=None)
    ap.add_argument("--out", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--fix", default="")
    ap.add_argument("--group", default="")
    ap.add_argument("--collect", default="",
                    help="P4 群级模式识别：子技能 review_report.json 所在目录，聚合 hard/soft 按类型聚类")
    ap.add_argument("--subskill", action="append", default=[])
    args = ap.parse_args()

    total = args.total if args.total is not None else (args.passed + args.na + args.pending)

    subskills = []
    for s in args.subskill:
        try:
            o = json.loads(s)
        except json.JSONDecodeError:
            print("ERROR --subskill 不是合法 JSON:", s, file=sys.stderr)
            sys.exit(2)
        subskills.append(o)

    report = {
        "skill": args.skill,
        "version": args.version,
        "trigger": args.trigger,
        "profile": args.profile,
        "date": args.date or datetime.date.today().isoformat(),
        "checklist": {"passed": args.passed, "na": args.na, "pending": args.pending, "total": total},
        "hard": [],
        "soft": [],
        "security": [],
        "behavior": None,
        "walkthrough": [],
        "subskills": subskills if subskills else (None if not args.group else []),
        "fixes": parse_fix(args.fix),
        "patterns": collect_patterns(args.collect) if args.collect else [],
        "archive": [],
        "gate": {"hard_cleared": args.passed > 0,
                 "open_soft": 0,
                 "conclusion": "pending"}
    }

    if args.group:
        g = args.group
        n = 0
        if os.path.isdir(g):
            for d in sorted(os.listdir(g)):
                if os.path.isdir(os.path.join(g, d)) and os.path.exists(os.path.join(g, d, "SKILL.md")):
                    n += 1
        report["group_root"] = g
        report["group_size"] = n
        report["gate"]["group_size"] = n

    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print("已写入", args.out)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
