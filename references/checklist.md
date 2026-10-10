# Detailed Checklist (L1–L5 + Continuous Governance)

This file is skill-review-pro's per-layer checklist, methods, and hard-failure signals. Execute layer by layer; N/A items attach a reason and count into the report tally.

---

## L1 Document self-consistency (6 + 2 design-quality items)

| # | Check | Method | Hard-failure signal |
|---|--------|------|----------|
| 1 | frontmatter complete | name/description present & non-empty, name matches regex | missing name or description → skill cannot be recognized/triggered |
| 2 | No rule contradiction | extract all rules/thresholds/judgment criteria, compare pairwise | mutually exclusive instructions for the same situation |
| 3 | Term consistency | one concept, one single name across the whole text | two+ names for one concept |
| 4 | Closed flow | every step has entry/artifact/downstream/failure exit | a step with no entry / no artifact / no failure exit |
| 5 | Reference check | referenced scripts/files/paths match text verbatim | references a non-existent file |
| 6 | Trigger precision | word-by-word compare description trigger phrases vs actual capability: function-trigger alignment, missed triggers, over-broad false triggers, cross-boundary | trigger phrase does not match function; core scenario missed; over-broad hit by unrelated requests; includes other skills' duties |
| 7 | Progressive disclosure | content layered across frontmatter/SKILL.md/references; long content moved to references | SKILL.md overlong, all details piled into the body |
| 8 | Context efficiency | whether length is lean and references optimal (rows/words tradeoffs acceptable) | length far beyond needed, redundant repetition |

---

## L2 Logic review (8 items + automated static checks)

| # | Check | What it checks | Hard-failure signal |
|---|--------|--------|----------|
| D1 | Steps executable | each step specific enough for the executor to follow directly | vague instructions like "adjust per actual situation" / "use your own judgment" |
| D2 | Code snippets syntactically correct | embedded Python/JS/pseudocode syntactically correct and directly runnable | attribute access to non-existent attr, undefined variable, wrong function signature |
| D3 | Input specs explicit | what input is needed, where from, format requirements | input specs missing or vague; executor improvises |
| D4 | Exception/boundary fallback | has handling guidance when input is not as expected | no exception handling at all; executor stalls on anomaly |
| D5 | Version-independence | numbers/names/paths parameterized; explicit version binding + declared re-verification when following external facts | internal counts hardcoded not following external facts, or bound without declared re-verification |
| D6 | Output specs explicit | artifact format, location, naming convention written | artifact format/path undefined |
| D7 | Cross-references consistent | internal references point correctly | reference points to a non-existent step or mismatches reality |
| D8 | Code blocks logically self-consistent | complete code blocks consistent before/after | same variable with contradictory type/meaning across blocks |

**Automated static checks**: run `scripts/static_check.py <target-dir>`. Checks:
- frontmatter exists and is valid YAML; name/description non-empty;
- relative reference paths in Markdown exist (incl. `cross_skill_refs` cross-skill whitelist exemption);
- anti-pattern hit list (see L5 anti-pattern table).

Results merge into L2 and L5 evidence. If the script lacks dependencies or errors, record it and explain; do not substitute script failure for manual inspection.

**Numeric-consistency check (doc/data-asset mandatory)**: run `scripts/counts_check.py <target-dir>` —
- extract count declarations from SKILL.md and references/*.md (`<int> items/entries/coordinates/pairs/dims/layers/frameworks`), list location & context;
- output structural summary of references/*.json (top-level length, count-key length);
- if the reviewed skill has `references/counts_manifest.json`, assert each count declared in SKILL.md vs the actual data-file entry count, producing a diff table.

Every count SKILL.md declares must correspond one-to-one to the data file's actual count; where unmatched, note the measurement basis in the report (distinguish "book value vs mechanism count" etc.).

**L2.5 External-authoritative-value verification (v1.3, mandatory for skills citing external authoritative facts)**: run `scripts/external_check.py <dir|group>` —
- extract threshold/frequency-class external value declarations from SKILL.md and references/*.md (e.g. `<0.00001`, `>0.01`, `0.002%`), context matching threshold keywords (AF/MAF/frequency/allele/BA1/BS1/PM2 etc.);
- assert each external value **binds a source** (URL/cspec/genome.network/PMID/ClinGen/VCEP/version/year); no bound source → **hard (external value untraceable)**;
- assert each external value **locks a version** (cspec vX.Y/year); no locked version → WARN (register "version pending verification", for external-upgrade re-review trigger);
- the executor verifies value correctness against the source at the authoritative site; write the result/conclusion into the report's "external-value verification" field; **never treat "internally consistent" as "externally correct"** (case C-14: PTEN BA1 internally consistent yet 18× off vs the ClinGen official site).

---

## L3 Walkthrough (4 items)

| # | Check | Method |
|---|--------|------|
| 1 | Run through end-to-end | walk start-to-finish with real input, recording each step |
| 2 | Blockers cleared | every stalling point backfilled into the doc until unambiguous |
| 3 | Consistent measurement | artifact/report format, numbers, wording consistent throughout |
| 4 | New chain verified | newly added steps/scripts passed a real-input walk |

**L3 boundary**: document walk-through, not runtime verification; when real running is needed, move to L4. L3 focuses on four problem types: points that stall, points needing improvisation, deletions without trace, measurement inconsistencies.

**L3 trace (reviewable)**: record each chain's "input → each step action → artifact/blocker" four-column trace; the "measurement consistent / blockers cleared" conclusion must cite specific entries into the report's `walkthrough` field, not just the conclusion.

---

## L4 Behavioral verification (conditional)

Run only when §3 judges L4 applicable. Core criteria and record fields:

| Step | Content | Record field |
|---|---|---|
| 1 Test set | positive/negative trigger samples, task scenarios, boundaries, historical bugs; use authoritative labels when a golden exists (never self-invented); scale ≥20 or per golden | `test_set_n` |
| 2 Baseline comparison | run the same batch without vs with the skill, compare success rate, error types | `baseline_success` / `skill_success` |
| 3 Deterministic contract | script verifies output format/file/field/schema/directory | `deterministic_contract` |
| 4 Repeated runs | same case run N≥3 for stability | `repeat_n` |
| 5 Precision/recall | compute when golden exists | `precision` / `recall` |
| 6 Cost proxy | token count, elapsed relative metrics, noted as non-real billing | `cost_proxy_tokens` |
| 7 Archive | write into JSON behavior field and registry | `conclusion` |

**Pass threshold**: set by the executor per the skill's consequence severity and stated in the report; clinical/finance/security strict. Threshold unstated = unfinished.

**False-precision warning**: when the test set is too small or skew-distributed, precision numbers are not generalizable; record soft "small-sample false precision".

---

## L5 Security red-line scan (static)

Anti-pattern hit list (reusable via `scripts/static_check.py`):

| Anti-pattern | Example signal | Default severity |
|---|---|---|
| Credential/key access | `~/.ssh`, `~/.aws`, `.env`, keychain, token | hard |
| Network exfiltration | curl/fetch POSTing local data out, webhook, pastebin | hard |
| Obfuscation | base64 blob, hex payload, minified single line | soft→hard |
| Dynamic execution | `eval`, `exec`, piping download into shell | hard |
| Persistence | backdoor, auto-start on boot, timers | hard |
| Destructive ops | `rm`, overwriting critical files, deletion without confirmation | soft→hard |

Any red-line hit is at least soft; credential leak, dynamic execution, persistence are hard.

---

## Continuous governance

After a review:
1. Append `review_report.json` to the `reviews/<skill>.json` registry index (accumulated entries).
2. Register re-evaluation triggers: skill change, data/guideline upgrade (e.g. ACMG version update), dependency change, user naming, or scheduled re-review (cron).
3. Drift monitoring: after a skill version change, compare the new vs old rounds, marking new hard/soft/behavioral-threshold declines.
