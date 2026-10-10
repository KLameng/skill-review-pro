---
name: skill-review-pro
version: 1.5.2
description: >-
  A skill review & behavioral verification SOP. Applies to any SKILL.md-format skill for document-quality review, logic review, behavioral verification, security red-line scanning, and pre-release checks — checking self-consistency, logical executability, trigger precision, numeric consistency, runtime correctness, and security anti-patterns, excluding skill-value or direction judgments. Supports skill-group/multi-skill aggregate scanning and cross-file consistency verification.
  Five-layer review method: L1 doc self-consistency → L2 logic review → L2.5 external authoritative-value verification → L3 walkthrough → L4 behavioral verification (conditional) → L5 security red-line scan, plus continuous governance (registry + re-evaluation). P0 external values traceable, P1 external upgrade re-review, P2 clone detection (text + script hash), P3 doc-accompanies-package, P4 group-level pattern recognition, P5 clinical lightweight L4, P6 non-deliverable check.
  Supports **one-click review** (`scripts/run_review.py` — one command runs all machine layers and generates a semantic review checklist) and a two-stage approach (machine pre-filter + human/AI semantic review), integrable into CI / pre-commit / scheduled re-review.
  Use when the user says "review this skill" "audit SKILL.md" "check skill quality" "pre-release check" "behaviorally evaluate this skill" "security review this skill" "one-click review" "run the checks".
---

# Skill Review & Behavioral Verification SOP (skill-review-pro)

> General-purpose skill review standard operating procedure: doc self-consistency → logic review → walkthrough → behavioral verification → security red line → continuous governance.
> Version: v1.5.2 (v1.5.1 fixed the run_review.py group-mode counts_check argument bug + this release strengthens group-mode counts_check to run per sub-skill, actually auditing each skill's numeric consistency)

---

## 1 Skill positioning

This skill is a **general-purpose review / audit / pre-release check / behavioral evaluation / security review** workflow for all SKILL.md-format skills.

Core methodology: the **Five-Layer Review Method**, paired with:

- **Tradeoff principle** (value × maintenance tax, deciding whether each layer runs)
- **Skill-profile routing** (document / data_asset / script / behavioral / hybrid)
- **Group/multi-skill aggregation** (v1.2: one-click aggregate scan of a skill-group root + cross-skill consistency)
- **Issue grading** (hard / soft) + **release gate**
- **soft closed loop** (lifecycle + deadline + escalation)
- **Fix → re-test closed loop** (v1.2: fixes[] record + verify_command + clear judgment, see `references/fix-loop.md`)
- **Case library** (mandatory archive)
- **Machine-readable output** (review_report.json, incl. group aggregation & fixes fields) + **continuous-governance registry**

This SOP is mandatory. Skills that fail review must not be released.

**Review input**: the reviewed skill directory (containing SKILL.md), path named by the user or located from context; SKILL.md must be read in full, never reviewed from a summary or impression. Multi-file skills read supplementary references/scripts per the §3 profile adaptation.

**Exception handling**: the reviewed directory missing, SKILL.md absent, or read failure → mark "blocked" in the report, state the reason and attempted actions; never claim passed. Until unblocked, do not enter the release gate.

---

## 2 Tradeoff principle (set the standard before working)

Whether each layer is enabled is decided with **two rulers**, avoiding "adding for the sake of adding" slowing the flow:

1. **Value = output determinism × consequence severity**
   - Is the output deterministically checkable (classification, format, result fields, schema)?
   - Is there a checkable golden / expected output?
   - Consequence severity (clinical / financial / security > document / creative)?
2. **Maintenance tax = per-review extra cost + long-term maintenance burden**

**Rules**:
- all three determinism/consequence high → that layer **must run**;
- partial → **optional**, executor decides by maintenance tax;
- pure document / creative → mark **N/A**, **must stay lightweight**, never slow every review by adding layers.
- capabilities that only benefit a few skills yet tax every review → **conditionally enabled**.

---

## 3 Skill profile & L4 applicability

Before reviewing, judge the reviewed skill's profile and allocate layer weights accordingly; **mark inapplicable items explicitly N/A with reason, never pretend passed**.

| Profile | Judgment | Check-item adaptation |
|---|---|---|
| document | only SKILL.md + pure document/creative/explanatory data, output **not contract-checkable** (no golden to verify) | L1/L2/L3 focus; **L4 N/A** (no golden); L5 static scan still applies; numeric cross-file consistency key |
| data_asset | document + data assets, **no execution script**, but output **contract-checkable** (coordinate library + calibration set/golden, crosswalk, schema, golden-sample set, mapping tables etc.) | L1/L2/L3 focus; **L4 must run** (regression on golden-sample set for hit rate/coverage, not running execution code); L5 static applicable; numeric consistency via `counts_check.py` mandatory |
| script | contains `scripts/` or embedded executable code blocks | L1–L5 all apply; L2 automated static checks, L4 behavioral verification key |
| behavioral (deterministic high-consequence) | has execution engine/script, output contract-checkable, has golden, severe consequence (clinical/financial/security/judgment) | **L4 must run**; L5 must run; L1–L3 as usual |
| hybrid | doc + script both present | all apply; script part executed per script profile |

**Profile judgment essentials**: data_asset vs document boundary = **whether output is contract-checkable** (has golden-sample set/authoritative labels). Skills with judgment output (coordinate classification, cross-map mapping, schema, compliance obligation tables) → data_asset; pure explanatory/creative doc → document. data_asset vs behavioral boundary = **whether there is an execution script/engine**.

**L4 applicability judgment** (whether behavioral verification is worth running): write the judgment into the report's "L4 judgment" line.

1. Is the output deterministically checkable?
2. Is there a checkable golden / expected output?
3. Is consequence severity high?

All three "yes" → **L4 must run**; partial → optional; pure document/creative → **N/A**.

**Profile and L4 alignment (unified criteria)**: the L4 three questions apply uniformly to **all** profiles, not cut by profile routing — data_asset/behavioral with "contract-checkable output + golden" is **L4 must-run** (for data_asset, verify via built-in golden-sample regression, hit rate/coverage; no execution script required); only pure document/creative (no golden) is **N/A**. **When the profile table and the L4 three questions conflict, the L4 three questions win.**

Execution rules:
1. Write the profile judgment into the report (note the profile under the Trigger line).
2. N/A items count into the report tally as "X passed / Y N/A / Z pending"; each N/A carries a one-line reason.
3. For document/data_asset skills, numeric-consistency check is **mandatory**: every count in SKILL.md must be checked one-to-one against actual entries, automated by `counts_check.py`.

---

## 4 The Five-Layer Review Method

Execution order: L1 → L2 → L3 → (L4 if applicable) → L5 → grading → fix → release → archive → registry.

### L1 Document self-consistency (what: is the doc written correctly)

Read SKILL.md end-to-end checking: frontmatter complete, no rule contradictions, consistent terms, closed flows, reference check, trigger precision, design quality (progressive disclosure, context efficiency). Methods and hard-failure signals in `references/checklist.md` L1.

### L2 Logic review (what + how to judge: can it be followed)

Check steps executable, code correct, input specs, exception fallbacks, version-independence, output specs, cross-references, code-block logical self-consistency. **Also run automated static checks**: run `scripts/static_check.py <target-dir>`, which auto-verifies frontmatter legality, reference-path existence (incl. `cross_skill_refs` cross-skill exemption, skipping fake links inside code blocks), anti-pattern hits; **numeric-consistency mandatory runs `scripts/counts_check.py <target-dir>`**; **cross-file consistency runs `scripts/consistency_check.py <dir|group>`** (v1.4: count declarations vs actual, cross-skill references, explicit current-version self-declaration, `references/consistency_manifest.json` term-consistency assertions, plus **dual-channel clone detection** — SKILL.md text similarity (>85%) + script content hash same-source, catching "scoping-table↔sub-skill mapping↔summarization rule" cross-file contradictions and "doc-forked-but-execution-body-same" twins). Results merge into L2 and L5 evidence. See `references/checklist.md` L2.

> **Group/multi-skill aggregation (v1.2)**: `static_check.py <skill-group-root>` auto-detects a group (root without SKILL.md but with subdirectories containing SKILL.md), one-click aggregate-scans N member skills and summarizes FAIL/WARN; `consistency_check.py --group` syncs group-level cross-file consistency. Reports use `gen_report.py --group` for group JSON (with `subskills[]`, `group_size`).

> **One-click review (v1.5, recommended entry)**: directly run `scripts/run_review.py <target-dir>` (add `--group` for groups) — one command auto-runs the four machine layers (static/counts/consistency/external), outputs a combined Markdown report + `review_report.json` + `semantic_review_points.md` (two-stage semantic review checklist), and returns an exit code by FAIL count (has FAIL=1, gating CI/pre-commit). **Machine pre-filter → human/AI semantic review** two-stage: scripts only decide what can be deterministically judged (format/count/ref/anti-pattern/external-value trace); semantic layer (external-value truth, clone discrimination, whether L4 truly ran) is listed item-by-item in `semantic_review_points.md` for the reviewer to process. CI integration: `references/ci-guide.md`.

### L2.5 External authoritative-value verification (v1.3, P0+P1: is the external value right)

> L1–L5 guarantee "internal self-consistency", not "referenced external authoritative values are correct". External values (ClinGen thresholds, ACMG rules, regulatory numbers, guideline cut-offs) can be fully internally consistent yet wholly wrong (case C-14: PTEN BA1 internally consistent but 18× off vs the official site).
> **Any skill citing external authoritative facts (thresholds/rules/regulations/guideline numbers) must run this layer.**

Run `scripts/external_check.py <target-dir>` (single) or `--group <group-root>` (group):

1. **Identify external-value declarations**: threshold/frequency-class numbers (e.g. `<0.00001`, `>0.01`, `0.002%`) with context hitting threshold keywords (AF/MAF/frequency/allele/BA1/BS1/PM2 etc.).
2. **Bind a source**: every external value must have an adjacent source marker (URL / cspec / genome.network / PMID / ClinGen / VCEP / version / year). **External value with no bound source = hard** (cannot verify correctness/expiry) — never silently pass.
3. **Lock version (P1)**: external values should carry a version (cspec vX.Y / year); no version = WARN, register "version pending verification", triggering "external authority upgrade → re-review" under continuous governance.
4. **Value correctness is verified by the executor against the authoritative site per source** (script does not go online; it only guarantees traceability); write the verification result and conclusion into the report's "external-value verification" field.

Results merge into L2 evidence. See `references/checklist.md` L2.5.

### L3 Walkthrough (document walk-through, not runtime)

Act as the executing agent and walk the full doc chain from the beginning with real input, finding blockers, points needing improvisation, deletions without trace, measurement inconsistencies. **Explicit boundary: L3 is a doc walk-through, not runtime verification; when real running is needed, use L4**. See `references/checklist.md` L3.

**L3 walk-through trace (reviewable)**: the walk must record a **trace** — each chain records "input → each step action → artifact/blocker" four columns; the "measurement consistent / blockers cleared" conclusion must cite specific entries in that trace, never just the conclusion. The trace merges into the report or archive (report adds a `walkthrough` field).

### L4 Behavioral verification (conditional: run the skill to measure it)

Run only when §3 judges L4 applicable. Steps:

1. **Build the test set**: positive/negative trigger samples, task scenarios, boundaries, historical bugs; use authoritative labels when a golden exists (never self-invent). Scale ≥20 or per available golden. **Data-asset skills reuse the skill's own golden-sample/calibration set first.** Golden sources: `references/golden-source-guide.md` (v1.2, authoritative sources by domain).
2. **No-skill baseline comparison**: run the same batch "without skill" vs "with skill", compare success rate, error types.
3. **Deterministic-contract check**: the script verifies output format, files, fields, schema, directory per contract.
4. **Repeated-run reliability**: same case run N≥3, check result stability.
5. **Precision / recall**: compute when golden exists.
6. **Cost / latency proxy**: token count, elapsed relative metrics, **explicitly noted as non-real billing**.
7. **Archive results**: write into `review_report.json`'s `behavior` field and the continuous-governance registry.

Pass threshold is set by the executor per the skill's consequence severity and stated in the report; clinical/financial/security strict. See `references/checklist.md` L4.

> **Group-level L4 (v1.2)**: for multi-sub-skill groups, additionally run **group-combination logic regression** beyond single-skill tests — condense the exclusion matrix / combined rules / point system into machine-readable contracts, draw "evidence code + level → expected classification" cases from the golden, run the three domains (pathogenic/benign/boundary) and the two schemes (classic + point). Template: `references/l4-group-testset-template.md`.

### L5 Security red-line scan (how to judge: is it safe)

Static-scan the skill directory checking: credential/key access, network-exfiltration forms, obfuscation (base64/hex/minified), dynamic execution (eval/exec/piped download), persistence (backdoor/auto-start), destructive ops (rm/overwriting key files). Reuse `scripts/static_check.py`'s anti-pattern scan results. Any red-line hit → at least soft; high-risk (credential leak, dynamic execution, persistence) → hard. See `references/checklist.md` L5.

---

## 5 Continuous governance (registry + re-evaluation + fix loop)

Besides producing a report, a review must:
1. **Write to registry**: append `review_report.json` to the skill registry index (named `reviews/<skill>.json`, accumulated entries) for trend and drift comparison.
2. **Register re-evaluation triggers**: record when the skill next needs re-review — skill change, data/guideline upgrade (e.g. ACMG version update), **external authoritative value upgrade (P1: version locked by external_check.py expires / authoritative site updates)**, dependency change, user naming, or scheduled re-review (cron).
3. **Drift monitoring**: after a skill version change, compare the new vs old review rounds, marking new hard/soft / behavioral-threshold decline.
4. **Fix → re-test closed loop (v1.2)**: for each hard/soft register into `fixes[]` (incl. `verify_command`), re-run static_check / consistency_check / group-level L4 after fixing, and only release after clear (hard=0 and L4 meets threshold and no new additions). See `references/fix-loop.md`.

---

## 6 Issue grading

### hard — must fix before release

| Type | Criterion |
|---|---|
| Broken flow | a step has no entry/no artifact/no failure exit; executor necessarily stalls |
| Code error | embedded code syntax error, data-structure contradiction; copying it errors |
| Rule contradiction | doc internally mutually exclusive, or numbers/counts inconsistent front-to-back |
| Missing carrier | references a non-existent script/file/step |
| Silent failure | exception path no error, no warning; flow reports success |
| **Behavior below threshold** (L4) | deterministic-contract failure, golden precision below set threshold |
| **Security red line** (L5) | credential leak, dynamic execution, persistence, other high-risk anti-patterns |

**Release gate**: hard cleared; and L4, if applicable, must pass the set threshold.

### soft — non-blocking, tracked

| Type | Criterion |
|---|---|
| Operability | vague steps, insufficient parameter explanation, needs improvisation |
| Version hardcoding | specific numbers/names hardcoded, should be parameterized |
| Insufficient trace | lacks logs/checklist/warnings; result not traceable |
| Anti-drift | naming convention/directory convention not hard-ruled |
| Declared boundary | function trigger conditions/applicable scope not stated |
| **Small-sample false precision** (L4) | test set too small, skew-distributed; precision not generalizable |

### soft closed-loop protocol

soft does not block this release but must be trackable, **no silent shelving**:
1. **Record**: every row in the report's soft table must carry `status` and `fix deadline` columns.
2. **State machine**: `open → fixed → verified`; or `open → waived`, waive must attach a reason.
3. **Fix deadline**: default "recheck before next release" — at the start of any TRIGGER_02/TRIGGER_03 review, first go through all open soft one-by-one to see whether fixed; **open soft not fixed beyond 2 version cycles is escalated to hard candidate**.
4. **Recheck trigger**: next release / data upgrade / framework upgrade / user naming — any triggers open-soft recheck.

---

## 7 Fix & release protocol

1. **Same-file edits strictly serial**: only one edit flow per file at a time; no parallel modification.
2. **Verify after each batch**: after each batch, verify old wording cleared (grep old threshold/name/phrase -> 0 hits); run the checklist-count self-check (all declared counts match actual checklist entries).
3. **Release**: after fixes land, publish the new version per the skill release flow.
4. **Post-release end-to-end verification**: run the full chain from the beginning with real input; verify artifacts and report item-by-item; archive review records; hard mandatory, typical soft archived into the case library.

---

## 8 Report template & machine-readable output

### Markdown report

```
## Skill Review Report: [Skill Name]

**Trigger**: TRIGGER_01 / TRIGGER_02 / TRIGGER_03
**Profile**: document / data_asset / script / behavioral / hybrid
**L4 judgment**: must-run / optional / N/A (reason)
**Checklist**: X passed / Y N/A / Z pending (total N)

### Hard Issues (N)
| # | Location | Issue | Notes |

### Soft Suggestions (N)
| # | Location | Issue | status | fix deadline | Notes |

### Walkthrough (L3 trace)
| chain | input | each step action | artifact/blocker |

### Behavioral (L4) — only when L4 applicable
test-set size / baseline vs skill success / deterministic contract / repeated runs / precision·recall / cost proxy / threshold & conclusion

### External Values (L2.5) — only when external authoritative values exist
external values with no bound source (hard) / version not locked (WARN) / per-source verification result & conclusion

### Patterns (P4) — only for group reports
systemic root causes: N skills sharing the same class of hard/soft (clustered by type, see patterns[])

### Security (L5)
hits / severity / handling

### Gate
Hard: X -> [cleared/not cleared]
L4: [passed/not passed/N/A]
Open soft: N
Fixes: N verified / M open (see fixes[])
Conclusion: [ready/not ready]
```

### Machine-readable output (review_report.json)

After a review, **must synchronously output structured JSON** (same content as the report, for registry and programmatic statistics). The skeleton can be generated by `scripts/gen_report.py` to avoid format drift. v1.2 adds `subskills[]` (group aggregation), `fixes[]` (fix→re-test loop), `group_size` (group size):

```json
{
  "skill": "[name]",
  "version": "[reviewed skill version]",
  "trigger": "TRIGGER_01 | TRIGGER_02 | TRIGGER_03",
  "profile": "document | data_asset | script | behavioral | hybrid",
  "l4_applies": true | false,
  "date": "YYYY-MM-DD",
  "checklist": { "passed": N, "na": N, "pending": N, "total": <computed from actual checklist entries, never hardcoded> },
  "walkthrough": [ { "chain": "...", "input": "...", "action": "...", "artifact/blocker": "..." } ],
  "hard": [ { "location": "...", "issue": "..." } ],
  "soft": [ { "id": "S1", "location": "...", "issue": "...", "status": "open | fixed | verified | waived", "deadline": "next_release | immediate" } ],
  "behavior": { "test_set_n": 0, "baseline_success": 0, "skill_success": 0, "deterministic_contract": "pass | fail", "repeat_n": 0, "precision": 0, "recall": 0, "cost_proxy_tokens": 0, "threshold": "...", "conclusion": "pass | fail | na" },
  "security": [ { "pattern": "...", "level": "hard | soft" } ],
  "subskills": [ { "name": "...", "passed": N, "fails": N } ],          // group aggregation (v1.2)
  "group_root": "...", "group_size": N,                                 // group aggregation (v1.2)
  "fixes": [ { "issue": "...", "severity": "hard|soft", "action": "...",
               "verify_command": "...", "status": "open|fixed|verified|waived",
               "verified": false, "evidence": "..." } ],                // fix loop (v1.2)
  "archive": [ { "title": "...", "level": "hard | soft", "check": "L4 | L5 | D4 | ...", "profile": "..." } ],
  "gate": { "hard_cleared": true, "l4_passed": true, "open_soft": 0, "conclusion": "ready | not_ready" }
}
```

**Archive convention**: JSON stored in the workspace, named `review_<skill>_<date>.json`, appended to the registry (§5).

---

## 9 Referenced resources

- `references/checklist.md`: detailed L1–L5 + continuous-governance checklist, methods, hard-failure signals.
- `references/cases.md`: case library (mandatory archive target).
- `references/golden-source-guide.md` (v1.2): L4 golden-source library (authoritative sources by domain + self-built-sample-set rules).
- `references/l4-group-testset-template.md` (v1.2): group-level L4 test-set template (exclusion matrix / combined rules / point system → case table).
- `references/fix-loop.md` (v1.2): fix → re-test → clear → archive loop.
- `references/ci-guide.md` (v1.5): CI integration guide — pre-commit hook, GitHub Actions, Doubao scheduled re-review (cron) configs.
- `scripts/static_check.py`: L2 automated static checks + L5 anti-pattern static scan (incl. `cross_skill_refs` exemption, fake-link skip in code blocks, env-key / no-shell subprocess safety exemptions; **supports group aggregation `--group`**).
- `scripts/consistency_check.py` (v1.4): cross-file consistency scan — count declarations vs actual, cross-skill references, explicit current-version self-declaration, `references/consistency_manifest.json` term-consistency assertions; **dual-channel clone detection**: SKILL.md text similarity (>85%) + script content hash same-source (catches doc-forked-but-execution-body-same twins).
- `scripts/counts_check.py`: numeric-consistency check (mandatory for document/data_asset) — extracts SKILL.md count declarations + json structural summary + optional manifest exact assertions.
- `scripts/external_check.py` (v1.5): external authoritative-value tracing (P0+P1) — identifies threshold/frequency-class external declarations, asserts source & version binding, outputs an "external-value list"; no bound source = FAIL. v1.5 removes false positives: arrow `->`/`→` excluded, example-lead-in lines exempt, line-level `<!-- ext-ignore -->` manual exemption.
- `scripts/gen_report.py`: review_report.json skeleton generation (anti-format-drift; supports `--group` group aggregation, `--fix` fix records, `--collect` group-level pattern recognition).
- `scripts/run_review.py` (v1.5): **one-click review entry** — one command runs the four machine layers (static/counts/consistency/external), generates a combined Markdown report + JSON + `semantic_review_points.md` (two-stage semantic review checklist), exit code gates CI/pre-commit.

---

## 10 Core principles

1. **Doc self-consistency != logic correctness** — L1 is a threshold, not the endpoint.
2. **Code must run** — embedded code is not decoration; executors copy it; when it truly needs running, use L4, don't rely on "looks right".
3. **Numbers must match** — the same number consistent across files; counts follow actual checklist entries.
4. **Version-specific values must be parameterized** — unless they follow external facts, then bind the version explicitly and declare re-verification conditions.
5. **Exception paths must have fallbacks** — no fallback = the executor necessarily stalls.
6. **Silence is a more dangerous bomb than errors** — no error, no warning = errors flow all the way downstream.
7. **Value × maintenance-tax tradeoff** — don't add layers for their own sake; pure document stays lightweight; high-consequence skills strict.
8. **Behavioral verification trusts only real runs** — a pretty doc does not equal correct classification/output; clinical/financial/security must look at actual results; data-asset skills verify by golden-sample regression, not "doc correct" instead of "output correct".
9. **Profile routing is not a one-size cut** — L4 applicability is judged uniformly by "contract-checkable output + golden"; the profile table is just a starting point; on conflict, the L4 three questions win.

---

## 11 Version history

| Version | Date | Change summary |
|------|------|---------|
| v1.0 | 2026-09-29 | First release: evolved from skill-review-sop-v2 — five-layer review method (added L4 behavioral verification, L5 security red line), tradeoff principle, profile routing incl. behavioral, continuous governance (registry + re-evaluation), automated static-check scripts |
| v1.1 | 2026-09-30 | Broad hardening (exposure from two usage rounds landed): ① profile routing added "data_asset" (doc + contract-checkable output + golden), fixing the "document blanket L4 N/A → behavioral verification missing" blind spot; ② L4 three questions uniformly apply to all profiles (profile table vs L4 three questions conflict → three questions win); ③ L3 walk-through trace (reviewable walkthrough); ④ added `counts_check.py` (numeric consistency: declaration extraction + json summary + optional manifest assertions) and `gen_report.py` (report skeleton); ⑤ `static_check.py` supports `cross_skill_refs` cross-skill whitelist declarations, removing false positives; ⑥ case library added C-13 data_asset-profile case |
| v1.2 | 2026-10-09 | Group/multi-skill + cross-file consistency + static de-false-positive + closed loop (landed via stress-test exposure on a 27-skill ACMG mixed large group): ① `static_check.py` group aggregation (`--group`, auto-detect root); ② `static_check.py` L5 de-false-positive — tightened credential judgment to "literal key assignment / key file / key-shaped literal", env key reads & no-shell list subprocess as safety exemption, skip fake links in code blocks; ③ added `consistency_check.py` (cross-file consistency: count declarations vs actual, cross-skill references, explicit current-version self-declaration, `consistency_manifest.json` term assertions — automating "scoping-table↔sub-skill mapping↔summarization rule" cross-file contradictions); ④ `gen_report.py` group aggregation (`--group`/`subskills[]`/`group_size`) + fix loop (`--fix`/`fixes[]`); ⑤ added `references/golden-source-guide.md` (L4 golden library), `l4-group-testset-template.md` (group-level L4 template), `fix-loop.md` (fix→re-test→clear loop); ⑥ JSON read BOM tolerance |
| v1.3 | 2026-10-09 | External-value verification + six optimizations (landed via a 36-skill ACMG large group + the PTEN 18× threshold flip exposure): **P0 external authoritative-value verification layer** — added `scripts/external_check.py`, identifies threshold/frequency-class declarations, asserts source & version binding, no source=hard (closing the "internal self-consistency ≠ external correctness" blind spot, case C-14); **P1 external upgrade re-review trigger** — external values lock versions; authoritative upgrades (e.g. ClinGen cspec update) trigger re-evaluation; **P2 clone detection** — `consistency_check.py` adds pairwise SKILL.md similarity comparison (>85% flags clone pairs); **P3 doc-accompanies-package check** — `consistency_check.py` checks whether docs referenced in the body accompany the package; **P4 group-level pattern recognition** — `gen_report.py --collect` aggregates sub-skill hard/soft clustered by type into systemic root causes (patterns[]); **P5 clinical lightweight L4** — `golden-source-guide.md` adds "single-evidence-code fragment regression" guidance (lowering clinical-skill L4 threshold); **P6 non-deliverable check** — `static_check.py` checks __pycache__/.pyc/temp files (WARN) |
| v1.4 | 2026-10-10 | P2 clone detection upgraded to "text + script hash" dual channel (landed via v1.3 re-reviewing the ACMG 36 group exposure): `consistency_check.py` clone detection no longer relies only on SKILL.md text similarity (missing "doc forked but sharing the same script" twins, e.g. ev-variant-literature-patient ↔ variant-literature-patient sharing main.py, similarity <85% slipped past v1.3); adds sha256 comparison of the two skills' executable script content — scripts with identical content hash flagged as "script same-source clone pairs". Measured 4 text-clone pairs → 12 (8 new script-same-source pairs, requiring manual discrimination of "shared general helper" vs "true twins"); case library adds C-15 |
| v1.5 | 2026-10-10 | Self-review exposure landed (a review tool must also be reviewed): **P0 de-false-positive** — `external_check.py` fixes "teaching example / arrow" false positives (① numbers after arrow `->`/`→` no longer treated as comparators; ② example lead-in lines exempt: e.g./for example/example:/examples/teaching/illustrative; ③ line-level `<!-- ext-ignore -->` manual exemption); **P0 add version** — SKILL.md frontmatter adds `version` field (self-consistency check met); **P1 one-click** — added `scripts/run_review.py`, one command runs all machine layers + generates combined report + `semantic_review_points.md` two-stage semantic review checklist, exit code gates CI; **P1 two-stage** — machine pre-filter + human/AI semantic review (external-value truth, clone discrimination, whether L4 truly ran explicitly listed); **P2 CI integration** — added `references/ci-guide.md` (pre-commit/GitHub Actions/Doubao cron configs); case library adds C-16 |
| v1.5.1 | 2026-10-10 | Fixed `run_review.py` group-mode argument bug: one-click review wrongly passed `--group` to `counts_check` (counts_check doesn't support group args), causing group reviews to falsely report "target dir not found: --group". Fixed to append `--group` only to the three group-capable scripts (`static_check`/`consistency_check`/`external_check`). Reviewed ACMG v14 skill group with the fixed enhanced version: external-value trace FAIL 18→0, machine layers all passed, semantic review all waived, conclusion ready. |
| v1.5.2 | 2026-10-10 | Group-mode counts_check enhancement: v1.5.1 fixed "counts_check wrongly accepts --group", but group mode still passed the **group root directory** directly to counts_check — a root without SKILL.md means numeric consistency never actually audits any sub-skill. This release runs counts_check **per sub-skill in group mode** (find_subs enumerates subdirectories containing SKILL.md, scanning numeric consistency per skill), truly auditing every member skill. Measured on a 3-skill temp group: counts_check no longer reports "target dir not found"; static/consistency/external group aggregation normal; one-click review exit 0. |
