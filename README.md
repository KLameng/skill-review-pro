# Skill-Review-Pro: An AI Skill Quality-Assurance Tool (Skill Review & Behavioral Verification SOP)

> **A runnable, verifiable, releasable quality pipeline for every SKILL.md skill.**
> Author: KLameng · MIT License · **English edition** (en branch)

## What it is

A **general-purpose, out-of-the-box** SOP for SKILL.md skill review / audit / pre-release check / behavioral evaluation / security scan.

When you need to know "is this skill production-ready and trustworthy?", use it: one command runs the machine-layer checks, then follow a checklist for semantic review, producing a review report with **issue severity grading** and a **release gate**.

Core method: the **Five-Layer Review Method**:

| Layer | What it checks | How to judge |
|---|---|---|
| **L1 Doc self-consistency** | Is the doc internally consistent? | no rule contradictions, consistent terms, closed loops, precise triggers |
| **L2 Logic review** | Can it be followed as written? | steps executable, code correct, input specs, exception fallbacks (automated via `static_check.py` / `counts_check.py` / `consistency_check.py`) |
| **L2.5 External-value verification** | Are referenced authoritative values correct? | every external threshold/rule/regulation bound to a source + version, lock re-review on upgrade (`external_check.py`) |
| **L3 Walkthrough** | Document walk-through | walk the full chain with real input, record a trace, find blockers |
| **L4 Behavioral verification** | Run it and measure | conditional: test set + no-skill baseline + deterministic contract + repeatability + precision/recall |
| **L5 Security red-line scan** | Is it safe? | credential leak / dynamic execution / exfiltration / persistence / destructive ops |

Plus **continuous governance**: registry accumulation + re-evaluation triggers + drift monitoring + a **fix → re-test → clear loop** (re-run after fixes, release only when clear).

## Why you need it

The "skill-as-AI-tool" form (SKILL.md skills, Claude Skills, various agent skill frameworks) is exploding, but **quality assurance is a gap**: many skills are internally consistent yet crash at runtime, or cite stale authoritative values, or hide security red lines. This tool answers "can this skill be released?" and turns quality from "gut feeling" into a traceable pipeline.

## Quick start

> Dependency: Python 3 standard library only — zero third-party installs.

```bash
# One-click review (recommended entry): run all four machine layers in one command
python scripts/run_review.py <target-skill-directory>

# Skill-group aggregation (root has no SKILL.md but contains sub-skills)
python scripts/run_review.py <skill-group-root> --group

# Exit codes: 0 = no FAIL, 1 = has FAIL (usable to gate CI / pre-commit)
```

One-click output produces three artifacts:
- **Markdown review report** (issue grading hard/soft + release gate)
- **`review_report.json`** (machine-readable, incl. group aggregation & fixes fields)
- **`semantic_review_points.md`** (semantic review checklist — two-stage: machine pre-filter → human/AI semantic review)

## Directory structure

```
skill-review-pro/
├── SKILL.md                  # Skill Review & Behavioral Verification SOP (five-layer method)
├── scripts/
│   ├── run_review.py         # One-click entry (four machine layers + exit codes)
│   ├── static_check.py       # L1/L2/L5 static checks (frontmatter / refs / anti-patterns / security)
│   ├── counts_check.py       # Numeric-consistency check (declared counts vs actual)
│   ├── consistency_check.py  # Cross-file consistency + clone detection (text similarity + script hash)
│   ├── external_check.py     # L2.5 external authoritative-value tracing (source + version)
│   └── gen_report.py         # Report generation (single / group JSON)
├── references/
│   ├── checklist.md          # Detailed L1–L5 + governance checklist
│   ├── cases.md              # Case library (mandatory archive target)
│   ├── ci-guide.md           # CI / pre-commit integration guide
│   ├── fix-loop.md           # Fix → re-test → clear closed loop
│   ├── golden-source-guide.md# L4 golden-source library (authoritative sources by domain)
│   └── l4-group-testset-template.md  # Group-level L4 test-set template
├── LICENSE                   # MIT
└── README.md                 # This file
```

## CI integration

`run_review.py`'s exit code is natively CI-judgeable (0 = pass / 1 = block). Put every skill change through automatic review to prevent drift. See `references/ci-guide.md`.

## How to use this repo

- **As a standalone tool**: clone and review any of your SKILL.md skills with `run_review.py`.
- **As a standard**: adopt the five-layer method + checklist into your skill development process as a release gate.

## License & acknowledgments

- **MIT License**, authored by KLameng <911712412@qq.com>.
- Complements the sister project **TACT Three-Axis Method** (AI system failure diagnosis & compliance mapping): TACT attributes failures post-incident; this tool prevents them pre-release — together a "prevent + attribute" quality loop for AI skills.
- Contributions welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).
