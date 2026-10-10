# Fix → Re-test → Clear Closed Loop (GAP-7, added in v1.2)

> Purpose: after a review issues hard/soft findings, whether fixes land, clear, and introduce no new problems must have a structured closed loop — not "report and done". This file defines the **fix → re-test → clear → archive** workflow.

## Closed-loop workflow

```
Review produces a hard/soft list
  → register every hard into review_report.json's fixes[] (GAP-6 schema)
  → fix (serial per file; after each batch verify old wording is cleared)
  → re-test: re-run static_check / consistency_check / counts_check / group-level L4 regression
  → clear judgment: all hard verified, L4 meets threshold, no new hard
  → archive + update registry (mark drift vs previous round)
```

## fixes[] record format (written into JSON)

Every hard/soft must be registered:

```json
{
  "issue": "scoping table lacks benign codes; benign path unreachable",
  "severity": "hard",
  "action": "add BS1/BS2/BS3/BP4/BA1 to scoping + add BA1 to mapping + promote BA1 in sub-skill",
  "verify_command": "python acmg_l4_combine_check_v2.py",
  "status": "fixed",          // open | fixed | verified | waived
  "verified": true,           // re-test passed
  "evidence": "benign gap 0; plan A 24/24=100%"
}
```

- `status` state machine: `open → fixed → verified`, or `open → waived` (waive must give a reason).
- `verify_command` is the **re-runnable re-test command** for each fix (static_check / consistency_check / regression script).
- `verified=true` must have `evidence` to support it (re-test output summary); never mark it empty.

## Mandatory re-test list (after fixes)

1. `static_check.py <dir|group>` — frontmatter/refs/L5: no new anti-patterns;
2. `consistency_check.py <dir|group>` — cross-file consistency: no new contradictions;
3. `counts_check.py` — numeric consistency (if applicable);
4. group-level L4 regression — behavioral below-threshold cleared (golden hit rate reaches threshold);
5. grep old wording cleared (old threshold / old name / old key → 0 hits).

## Clear judgment

- **hard = 0** and all `verified` (or `waived` with reason);
- **L4**: if applicable, golden hit rate ≥ set threshold;
- **no new hard** (vs the pre-fix list).

Only then release, conclusion `ready`. Otherwise return to the fix step.

## Interop with registry / continuous governance

- Append the re-tested review_report.json to `reviews/<skill>.json`;
- vs the previous round: mark which hard cleared, which soft promoted to hard candidate (open soft not fixed beyond 2 version cycles);
- if a fix itself changes rules/thresholds, register a re-evaluation trigger (guideline upgrade, data upgrade).
