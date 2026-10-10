#!/usr/bin/env python3
"""consistency_check.py — skill-review-pro 的跨文件一致性扫描（v1.4，P2 克隆检测双通道）。

目标：把"PM2 分值三处不一致""圈定表缺良性码但子技能映射有"这类**跨文件矛盾**
从"靠人工通读"变成可自动断言的防线。

用法:
    python consistency_check.py <技能目录>            # 单技能
    python consistency_check.py <技能群根目录>          # 群（自动识别）
    python consistency_check.py --group <技能群根目录>  # 显式群

检查项:
    A. 自身版本声明一致性：SKILL.md 正文提及的 v<major>.<minor> 与 frontmatter `version` 是否一致
       （防"正文写 v4.6.0、frontmatter 仍 4.5.0"）
    B. 计数声明 vs 实际（群模式）：SKILL.md 中 "<int> 个技能/子技能/组成" 声明与实际子技能数比对
       （防"声称 23 个技能"与实际不符）
    C. 跨技能引用解析（群模式）：markdown 链接指向兄弟技能目录内不存在的文件
    D. 术语/证据码清单一致性断言：若技能含 references/consistency_manifest.json，逐项断言
       格式 { "术语码": ["SKILL.md", "references/rule.md", ...] }  —— 每个术语必须在列出的每个文件出现
       （泛化"圈定表↔子技能映射↔汇总规则↔子技能 证据码一致"检查）

输出: 逐项 PASS/WARN/FAIL，退出码 1=有 FAIL。仅依赖标准库，无网络/命令执行。
"""
import difflib
import json
import os
import re
import sys


def iter_skill_md(skill_dir):
    """单个技能目录下的全部 md 文件（SKILL.md + references/*.md）。"""
    files = [os.path.join(skill_dir, "SKILL.md")]
    ref = os.path.join(skill_dir, "references")
    if os.path.isdir(ref):
        files += [os.path.join(ref, f) for f in sorted(os.listdir(ref)) if f.endswith(".md")]
    return [f for f in files if os.path.exists(f)]


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def frontmatter_version(text):
    m = re.search(r"(?m)^version:\s*[\"']?([0-9]+\.[0-9]+(?:\.[0-9]+)?)", text)
    return m.group(1) if m else None


def body_version_refs(text):
    """提取 SKILL.md 正文中的 v<major>.<minor>(.<patch>)? 版本引用。"""
    return re.findall(r"(?<![A-Za-z0-9])v?([0-9]+\.[0-9]+(?:\.[0-9]+)?)", text)


def strip_code_blocks(text):
    return re.sub(r"```.*?```", " ", text, flags=re.DOTALL)


def find_skill_subdirs(root):
    subs = []
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "SKILL.md")):
            subs.append(d)
    return subs


def check_version(skill_dir, log):
    """A. 自身版本声明一致性。返回 fails。

    只比对**显式当前版本自声明**（"本技能/当前版本/技能版本 vX.Y.Z"），
    不比对历史变更日志版本（"v1.1.0 新增"）与外部指南版本（"v4.2.0 全局"），避免误报。
    """
    md = os.path.join(skill_dir, "SKILL.md")
    text = read_text(md)
    if not text:
        return 0
    fv = frontmatter_version(text)
    if not fv:
        log.append(("WARN", "%s: SKILL.md 无 frontmatter version" % os.path.basename(skill_dir)))
        return 0
    fails = 0
    body = strip_code_blocks(text)
    start = body.find("\n---", 3)
    if start != -1:
        body = body[start + 4:]
    # 仅匹配显式当前版本自声明
    for m in re.finditer(r"(?i)(本技能|当前版本|技能版本|本技能版本|current\s*version)\s*[：:]\s*v?([0-9]+\.[0-9]+(?:\.[0-9]+)?)", body):
        ref = m.group(2)
        if ref.split(".")[:2] != fv.split(".")[:2]:
            log.append(("FAIL", "%s: 正文声明当前版本 v%s 与 frontmatter version=%s 不一致" % (
                os.path.basename(skill_dir), ref, fv)))
            fails += 1
    return fails


def check_count_claims(group_root, subs, log):
    """B. 计数声明 vs 实际子技能数（群模式）。返回 fails。

    只检查**全群总量措辞**（"共/总计/全群 N 个技能"），
    不检查子集声明（如"本评级群由 23 个技能组成"指子群），避免误报。
    """
    fails = 0
    pat = re.compile(r"(?:(共|总(?:计)?|全(?:部|群)?)\s*(\d+)\s*个\s*技能)")
    for sub in subs:
        md = os.path.join(group_root, sub, "SKILL.md")
        text = read_text(md)
        if not text:
            continue
        for m in pat.finditer(strip_code_blocks(text)):
            n = int(m.group(2))
            if n != len(subs):
                log.append(("FAIL", "%s/SKILL.md: 声称%s %d 个技能，实际子技能数 %d" % (
                    sub, m.group(1), n, len(subs))))
                fails += 1
    return fails


def check_cross_skill_refs(group_root, subs, log):
    """C. 跨技能引用解析：链接指向兄弟技能目录内不存在的文件。返回 fails。"""
    fails = 0
    link_re = re.compile(r"\]\(([^)#]+)(?:#[^)]*)?\)")
    for sub in subs:
        for md in iter_skill_md(os.path.join(group_root, sub)):
            text = strip_code_blocks(read_text(md))
            for m in link_re.finditer(text):
                link = m.group(1).strip()
                if link.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                # 解析相对当前文件
                local_target = os.path.normpath(os.path.join(os.path.dirname(md), link))
                if os.path.exists(local_target):
                    continue
                # 尝试：指向兄弟技能目录内的路径（如 ../ev-bs1-bs2/SKILL.md）
                resolved = False
                norm_link = link.replace("\\", "/").lstrip("./")
                for s2 in subs:
                    cand = os.path.join(group_root, s2, norm_link)
                    if os.path.exists(cand):
                        resolved = True
                        break
                    # 也支持 "../<skill>/xxx"
                    base = os.path.basename(os.path.normpath(link))
                    dirp = os.path.dirname(link)
                    if dirp and os.path.basename(os.path.normpath(dirp)) == s2:
                        cand2 = os.path.join(group_root, s2, base)
                        if os.path.exists(cand2):
                            resolved = True
                            break
                if not resolved:
                    log.append(("FAIL", "%s (in %s): 跨技能引用目标不存在 %s" % (
                        os.path.relpath(md, group_root), sub, link)))
                    fails += 1
    return fails


def check_manifest(skill_dir, log):
    """D. consistency_manifest.json 术语一致性断言。返回 fails。

    manifest 格式: { "术语码": ["SKILL.md", "references/rule.md", ...] }
    每个术语必须在列出的每个文件出现（跨文件一致性核心）。
    """
    mp = os.path.join(skill_dir, "references", "consistency_manifest.json")
    if not os.path.exists(mp):
        return 0
    try:
        with open(mp, encoding="utf-8-sig") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        log.append(("FAIL", "%s: consistency_manifest.json 无法解析 (%s)" % (
            os.path.basename(skill_dir), e)))
        return 1
    fails = 0
    for term, files in manifest.items():
        if not isinstance(files, list):
            continue
        for rel in files:
            fp = os.path.join(skill_dir, rel)
            if not os.path.exists(fp):
                log.append(("FAIL", "%s: 术语 '%s' 指定文件不存在 %s" % (
                    os.path.basename(skill_dir), term, rel)))
                fails += 1
                continue
            if term not in read_text(fp):
                log.append(("FAIL", "%s: 术语 '%s' 未出现在 %s（跨文件一致性缺失）" % (
                    os.path.basename(skill_dir), term, rel)))
                fails += 1
    if fails == 0:
        log.append(("PASS", "%s: consistency_manifest 全部 %d 术语一致" % (
            os.path.basename(skill_dir), len(manifest))))
    return fails


SCRIPT_EXT = (".py", ".sh", ".js", ".bash", ".ps1", ".rb", ".pl", ".ts")


def file_hashes(skill_dir):
    """返回技能目录下可执行脚本文件的 {内容 sha256} 集合（不看路径，只看内容是否同源）。

    只扫 scripts/ 目录下与脚本扩展名的文件；内容哈希相同 = 执行体同源 = 即使文档分叉也是克隆。
    """
    import hashlib
    hashes = set()
    for root, _, files in os.walk(skill_dir):
        relroot = os.path.relpath(root, skill_dir).split(os.sep)
        for f in files:
            if f.startswith(("__", ".")):
                continue
            ext = os.path.splitext(f)[1].lower()
            if not (ext in SCRIPT_EXT or "scripts" in relroot):
                continue
            fp = os.path.join(root, f)
            try:
                with open(fp, "rb") as fh:
                    hashes.add(hashlib.sha256(fh.read()).hexdigest())
            except OSError:
                continue
    return hashes


def check_clones(group_root, subs, log):
    """P2 克隆/同源检测（v1.4）：文本相似度 + 脚本内容哈希 双通道。

    ①文本通道：SKILL.md 两两相似度 >85% → 文本克隆对；
    ②脚本通道：两技能共享内容哈希一致的脚本文件 → 脚本同源克隆对
      （文档可能分叉、相似度 <85% 但执行体相同，如 ev- 与 variant- 双胞胎共用 main.py）。

    用 difflib + hashlib 标准库，无网络。clone 记为 WARN（soft）——可能是双壳或冗余克隆，
    需人工判定是否合并。
    """
    texts = {}
    hashes = {}
    for sub in subs:
        md = os.path.join(group_root, sub, "SKILL.md")
        texts[sub] = read_text(md)
        hashes[sub] = file_hashes(os.path.join(group_root, sub))
    names = sorted(texts)
    n = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            ra, rb = texts[a], texts[b]
            sim = difflib.SequenceMatcher(None, ra, rb).ratio() if (ra and rb) else 0
            shared = hashes[a] & hashes[b] if (hashes[a] and hashes[b]) else set()
            if sim > 0.85:
                extra = ("，且共享 %d 个脚本文件" % len(shared)) if shared else ""
                log.append(("WARN", "文本克隆对: %s ↔ %s 相似度 %.0f%%（疑似重复技能，确认是否双壳/需合并）%s" % (
                    a, b, sim * 100, extra)))
                n += 1
            elif shared:
                log.append(("WARN", "脚本同源克隆对: %s ↔ %s 共享 %d 个脚本文件（内容哈希一致；文档可能分叉但执行体相同，v1.4 脚本哈希检测，需合并）" % (
                    a, b, len(shared))))
                n += 1
    if n:
        log.append(("WARN", "共 %d 对疑似克隆（含脚本同源）" % n))
    return n


def check_internal_doc_refs(skill_dir, log):
    """P3 被引用文档随包性：正文引用的《xx》/「xx」文档名，包内是否随附对应文件。

    启发式：匹配《》/「」包裹的 2-40 字词，若命中明显的"文档/规范/指南/标准/表/路径"字样
    且包内文件名不包含该词 → WARN（提示可能未随包）。仅 WARN 不 FAIL（外部文档可能确无独立文件）。
    """
    doc_re = re.compile(r"[《「]([^》」]{2,40})[》」]")
    md = os.path.join(skill_dir, "SKILL.md")
    text = read_text(md)
    if not text:
        return 0
    pkg_names = set()
    for root, _, files in os.walk(skill_dir):
        for f in files:
            pkg_names.add(os.path.splitext(f)[0].lower())
            pkg_names.add(f.lower())
    doc_terms = ("文档", "规范", "指南", "标准", "手册", "路径", "制度", "说明", "流程")
    n = 0
    for m in doc_re.finditer(text):
        name = m.group(1).strip()
        if not any(t in name for t in doc_terms):
            continue
        low = name.lower()
        if any(low in p or p in low for p in pkg_names):
            continue
        log.append(("WARN", "%s: 正文引用文档《%s》未在包内找到随附文件（确认是否随包/外部文档）" % (
            os.path.basename(skill_dir), name)))
        n += 1
    return n


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    group_flag = "--group" in sys.argv
    if not args:
        print("用法: python consistency_check.py <技能目录|群根目录> [--group]")
        return 2
    target = args[0]
    if not os.path.isdir(target):
        print("FAIL 目录不存在:", target)
        return 1

    subs = find_skill_subdirs(target)
    has_own = os.path.exists(os.path.join(target, "SKILL.md"))
    is_group = group_flag or (not has_own and len(subs) > 0)

    log = []
    total_fails = 0
    total_warns = 0

    if is_group:
        print("=" * 70)
        print("跨文件一致性扫描（群）: %s（%d 个子技能）" % (target, len(subs)))
        print("=" * 70)
        total_fails += check_count_claims(target, subs, log)
        total_fails += check_cross_skill_refs(target, subs, log)
        total_warns += check_clones(target, subs, log)
        for sub in subs:
            total_fails += check_version(os.path.join(target, sub), log)
            total_fails += check_manifest(os.path.join(target, sub), log)
            total_warns += check_internal_doc_refs(os.path.join(target, sub), log)
    else:
        print("=" * 70)
        print("跨文件一致性扫描（单技能）: %s" % target)
        print("=" * 70)
        total_fails += check_version(target, log)
        total_fails += check_manifest(target, log)
        total_warns += check_internal_doc_refs(target, log)

    if not log:
        print("(无一致性检查命中，全部通过)")
    else:
        for status, msg in log:
            print("  %s %s" % (status, msg))

    print("-" * 70)
    print("跨文件一致性扫描完成: " + ("FAIL 有 %d 处不一致" % total_fails if total_fails else "PASS 全部一致")
          + ("，WARN %d 处（克隆对/文档随包，soft）" % total_warns if total_warns else ""))
    return 1 if total_fails else 0


if __name__ == "__main__":
    sys.exit(main())
