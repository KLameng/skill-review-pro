#!/usr/bin/env python3
"""static_check.py — skill-review-pro 的自动化静态检查（v1.2）。

用法:
    python static_check.py <被审技能目录>              # 单技能
    python static_check.py <技能群根目录>              # 自动识别为群：根目录无 SKILL.md 但有含 SKILL.md 的子目录
    python static_check.py --group <技能群根目录>      # 显式群模式

核验:
    1. frontmatter 存在且为合法结构，name/description 非空
    2. Markdown 内相对引用路径存在（references/scripts/assets 等；跨技能引用白名单豁免）
    3. L5 反模式静态扫描（凭据/外泄/混淆/动态执行/持久化/破坏性操作）
    4. 安全豁免（v1.2）：从环境变量读取密钥（os.environ.get/getenv）判为安全；
       无 shell=True 的列表参数 subprocess 调用判为安全，不再误报。

输出: 逐项 PASS/WARN/FAIL，退出码 0=无 FAIL，1=有 FAIL。
仅依赖标准库；脚本本身不做任何网络请求或命令执行，仅做文本扫描。
"""
import os
import re
import sys


def parse_frontmatter(text):
    """简易解析 --- 围栏内的键:值 行，返回 (meta_dict, error)。"""
    if not text.startswith("---"):
        return None, "缺少 --- frontmatter 起始围栏"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "缺少 --- frontmatter 结束围栏"
    block = text[3:end].strip()
    meta = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ">")) or ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip().strip("'\"")
    return meta, None


def parse_cross_skill_refs(block):
    """解析 frontmatter 中可选声明的跨技能引用白名单（YAML list 形态）。"""
    refs = []
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("cross_skill_refs"):
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if s.startswith("- "):
                    refs.append(s[2:].strip().strip("\"' "))
                    j += 1
                elif s == "":
                    j += 1
                else:
                    break
            break
        i += 1
    return refs


# ---- L5 反模式（v1.2 收紧凭据判定：只匹配"字面量密钥赋值/密钥文件访问/密钥形态字面量"，不匹配变量名本身）----
# 凭据：① 密钥类标识符赋值给引号字面量（api_key="sk-..."）；② 访问密钥文件(.ssh/.aws/.env/keychain)；
#       ③ 裸密钥形态字面量（UUID / sk-* / ghp_*）。env 读取（os.environ.get）由 SAFE_BYPASS 豁免。
FORBIDDEN = [
    ("凭据/密钥访问",
     r"(?i)(api[_-]?key|secret|password|token|bearer)\s*=\s*[\"'][^\"']{6,}"
     r"|(\.ssh|\.aws|\.env|keychain)\b"
     r"|[\"'][0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[\"']"
     r"|sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{16,}",
     "hard"),
    ("网络外泄", r"(?i)(curl|wget|fetch|requests\.(post|put))\b.*(webhook|pastebin|https?://|upload)", "hard"),
    ("混淆", r"(base64\s*-\s*d\b|base64\.b64decode|\\x[0-9a-f]{2})", "soft"),
    ("动态执行", r"(?i)(\beval\s*\(|\bexec\s*\(|os\.system|subprocess\.(call|run|Popen)|popen)", "hard"),
    ("持久化", r"(?i)(at\s*boot|startup|autorun|rc\.local|crontab|scheduled[_-]task)", "hard"),
    ("破坏性操作", r"(?i)(rm\s+-[rf]|shutil\.rmtree|os\.remove|truncate\s+0)", "soft"),
]

# ---- v1.2 安全豁免表：命中 FORBIDDEN 但属于安全写法的行，降级为 INFO（不 FAIL） ----
# 每条: (pattern_name, safe_regex, reason)
SAFE_BYPASS = [
    # 凭据/密钥访问：从环境变量读取密钥是安全做法（硬编码才是泄露）
    ("凭据/密钥访问",
     r"(?i)(os\.environ\.get|os\.getenv|os\.environ\[|os\.environ\.getdefault)\s*\(\s*[\"']",
     "从环境变量读取密钥（安全，非硬编码）"),
    ("凭据/密钥访问",
     r"(?i)getenv\(\s*[\"'][A-Z0-9_]+[\"']",
     "从环境变量读取密钥（安全，非硬编码）"),
    # 动态执行：subprocess 列表参数 + 无 shell=True = 安全；只有 shell=True 拼接字符串才有注入风险
    ("动态执行",
     r"(?i)subprocess\.(call|run|Popen)\(\s*\[",
     "subprocess 列表参数（无 shell 拼接，安全）"),
    ("动态执行",
     r"(?i)subprocess\.(call|run|Popen)\b(?!.*shell\s*=\s*True)",
     "subprocess 未开启 shell=True（安全）"),
    # 混淆：base64 模块 import / 定义示例字符串（非 decode 执行）
    ("混淆",
     r"(?i)import\s+base64|from\s+base64",
     "base64 模块导入（非解码执行，安全）"),
]


def line_is_safe(pattern_name, line):
    """命中 FORBIDDEN[pattern_name] 的行是否属于安全写法。返回 (safe, reason)。"""
    for pname, sre, reason in SAFE_BYPASS:
        if pname == pattern_name and re.search(sre, line):
            return True, reason
    return False, None


EXEC_EXT = {".py", ".sh", ".js", ".bash", ".ps1", ".rb", ".pl"}


def is_exec_file(relpath, path):
    """仅扫描可执行代码：位于 scripts/ 下，或为代码扩展名。"""
    norm = relpath.replace("\\", "/")
    if norm.startswith("scripts/"):
        return True
    return os.path.splitext(relpath)[1].lower() in EXEC_EXT


def scan_security(path):
    """对目录内可执行代码做反模式扫描，返回 [(name, level, relpath, line_no, is_safe, reason)]。

    排除本工具自身（static_check.py）。文档/数据文件不扫描。
    """
    hits = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv", "node_modules")]
        for fname in files:
            if fname == "static_check.py":
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, path)
            if not is_exec_file(rel, path):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, 1):
                        for name, pat, level in FORBIDDEN:
                            if re.search(pat, line):
                                safe, reason = line_is_safe(name, line)
                                hits.append((name, level, rel, i, safe, reason))
            except OSError:
                continue
    return hits


JUNK_PATTERNS = [
    (r"\.pyc$", "Python 编译缓存 .pyc"),
    (r"(\.tmp|\.bak|\.old|\.swp|~$|\.DS_Store|\.log)$", "临时/备份/系统文件"),
]


def scan_junk(target):
    """P6 包内非交付文件检查：__pycache__ / .pyc / 临时文件。返回 [(relpath, 原因)]。

    这些文件会混入打包（如 __pycache__/*.pyc），属非交付物，标记 WARN（soft）。
    """
    hits = []
    for root, dirs, files in os.walk(target):
        for d in dirs:
            if d == "__pycache__":
                hits.append((os.path.relpath(os.path.join(root, d), target), "Python 缓存目录 __pycache__"))
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv", "node_modules")]
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), target)
            for pat, reason in JUNK_PATTERNS:
                if re.search(pat, rel):
                    hits.append((rel, reason))
                    break
    return hits


def strip_code_blocks(text):
    """移除围栏代码块(``` ... ```)，避免代码内正则/参数被误当作 markdown 链接。"""
    return re.sub(r"```.*?```", " ", text, flags=re.DOTALL)


def check_links(md_path, base_dir):
    """检查 Markdown 内相对引用是否存在，返回 [(link, exists)]。

    跳过围栏代码块内容（代码内 `](regex)` 等会被误判为链接），再找 `](...)` 链接。
    """
    results = []
    try:
        with open(md_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return results
    text = strip_code_blocks(text)
    for m in re.finditer(r"\]\(([^)#]+)(?:#[^)]*)?\)", text):
        link = m.group(1).strip()
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(md_path), link))
        results.append((link, os.path.exists(target)))
    return results


def collect_md_files(target):
    """返回待检查的 md 文件列表：SKILL.md + references/ 下全部 .md。"""
    mds = [os.path.join(target, "SKILL.md")]
    ref_dir = os.path.join(target, "references")
    if os.path.isdir(ref_dir):
        for f in sorted(os.listdir(ref_dir)):
            if f.endswith(".md"):
                mds.append(os.path.join(ref_dir, f))
    return mds


def check_skill(target):
    """对单个技能目录执行全部检查，返回 (fails, warns, info_log)。"""
    fails = 0
    warns = 0
    log = []
    skill_md = os.path.join(target, "SKILL.md")
    if not os.path.exists(skill_md):
        log.append(("FAIL", "缺少 SKILL.md"))
        return 1, 0, log

    with open(skill_md, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    meta, err = parse_frontmatter(text)
    if err:
        log.append(("FAIL", "frontmatter: " + err))
        fails += 1
    else:
        name_ok = bool(meta.get("name"))
        desc_ok = bool(meta.get("description"))
        log.append(("PASS" if name_ok else "FAIL", "frontmatter.name"))
        log.append(("PASS" if desc_ok else "FAIL", "frontmatter.description"))
        if not name_ok:
            fails += 1
        if not desc_ok:
            fails += 1

    cross_refs = parse_cross_skill_refs(text) if not err else []
    if cross_refs:
        log.append(("INFO", "已声明跨技能引用 %d 项" % len(cross_refs)))
    for md in collect_md_files(target):
        for link, exists in check_links(md, target):
            if not exists and link in cross_refs:
                log.append(("PASS", "跨技能引用(已声明): %s (in %s)" % (link, os.path.basename(md))))
                continue
            log.append(("PASS" if exists else "FAIL",
                        "引用存在: %s (in %s)" % (link, os.path.basename(md))))
            if not exists:
                fails += 1

    hits = scan_security(target)
    if not hits:
        log.append(("PASS", "L5 反模式扫描: 无命中"))
    else:
        for name, level, f, ln, safe, reason in hits:
            if safe:
                log.append(("INFO", "L5 安全豁免 '%s': %s:%d（%s）" % (name, f, ln, reason)))
            else:
                log.append(("WARN[%s]" % level, "L5 反模式 '%s': %s:%d" % (name, f, ln)))
                warns += 1
                if level == "hard":
                    fails += 1

    for rel, reason in scan_junk(target):
        log.append(("WARN", "非交付文件: %s（%s，建议不入包）" % (rel, reason)))
        warns += 1
    return fails, warns, log


def find_skill_subdirs(root):
    """返回 root 下含 SKILL.md 的直接子目录（群成员），按名排序。"""
    subs = []
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "SKILL.md")):
            subs.append(d)
    return subs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    group_flag = "--group" in sys.argv
    if not args:
        print("用法: python static_check.py <技能目录>  |  python static_check.py --group <技能群根目录>")
        return 2
    target = args[0]
    if not os.path.isdir(target):
        print("FAIL 被审目录不存在:", target)
        return 1

    has_own_skill = os.path.exists(os.path.join(target, "SKILL.md"))
    sub_skills = find_skill_subdirs(target)
    is_group = group_flag or (not has_own_skill and len(sub_skills) > 0)

    if is_group:
        # ---- 群聚合模式（GAP-1）----
        total_fails = 0
        total_warns = 0
        print("=" * 66)
        print("技能群静态扫描: %s（%d 个成员技能）" % (target, len(sub_skills)))
        print("=" * 66)
        for name in sub_skills:
            p = os.path.join(target, name)
            f, w, log = check_skill(p)
            total_fails += f
            total_warns += w
            print("\n-- [%s] (FAIL=%d, WARN=%d) --" % (name, f, w))
            for status, msg in log:
                print("  %s %s" % (status, msg))
        if has_own_skill:
            # 根目录自身也是技能（混合：根 SKILL.md + 子技能）
            f, w, log = check_skill(target)
            total_fails += f
            total_warns += w
            print("\n-- [%s] (根目录自身也是技能, FAIL=%d, WARN=%d) --" % (os.path.basename(target), f, w))
            for status, msg in log:
                print("  %s %s" % (status, msg))
        print("\n" + "=" * 66)
        print("群汇总: %d 个成员, FAIL=%d, WARN=%d, 安全豁免见上" % (len(sub_skills), total_fails, total_warns))
        print("静态检查完成: " + ("FAIL 需处理" if total_fails else "PASS 全部通过"))
        return 1 if total_fails else 0

    # ---- 单技能模式 ----
    f, w, log = check_skill(target)
    for status, msg in log:
        print("%s %s" % (status, msg))
    print("-" * 40)
    print("静态检查完成: " + ("FAIL 需处理" if f else "PASS 全部通过"))
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
