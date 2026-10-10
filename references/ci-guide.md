# CI Integration Guide (v1.5, P2)

> Purpose: hook skill-review-pro's one-click review into the release/commit flow so "every change is auto-reviewed", continuously preventing drift. Core entry: `scripts/run_review.py` — exit code **0 = no FAIL**, **1 = has FAIL**, natively CI-judgeable.

## Prerequisite: confirm python is available

run_review.py depends only on the standard library; the environment needs python3. Each CI platform ships or installs it.

---

## Option A: pre-commit hook (local machine / team-local)

Add to `.git/hooks/pre-commit` in the skill repo (or a centralized pre-commit framework):

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit —— one-click review of the target skill dir before commit
SKILL_DIR="${1:-.user_skills/skill-review-pro}"
python3 "$SKILL_DIR/scripts/run_review.py" "$SKILL_DIR" --out "$SKILL_DIR/reviews" || {
  echo "Review failed (has FAIL). Fix or manually adjudicate before committing.";
  echo "Artifacts: $SKILL_DIR/reviews/review_*.md + semantic_review_points.md";
  exit 1;
}
```

If using the [pre-commit](https://pre-commit.com) framework, `pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: skill-review-pro
        name: skill-review-pro one-click review
        entry: python3 .user_skills/skill-review-pro/scripts/run_review.py
        args: [.user_skills/skill-review-pro, --out, .user_skills/skill-review-pro/reviews]
        language: system
        pass_filenames: false
```

> Note: a FAIL blocks the commit. If a FAIL was manually adjudicated as false positive/acceptable, fix to clear, or register as `waived` (with reason) per §6 of this skill — never bake "bypass" into the script.

---

## Option B: GitHub Actions (open-source repo)

`.github/workflows/skill-review.yml`:

```yaml
name: skill-review-pro
on:
  pull_request:
  push:
    branches: [main]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - name: one-click review
        run: |
          python3 .user_skills/skill-review-pro/scripts/run_review.py \
            .user_skills/skill-review-pro \
            --out .user_skills/skill-review-pro/reviews
      - name: upload review reports
        uses: actions/upload-artifact@v4
        with:
          name: review-reports
          path: .user_skills/skill-review-pro/reviews/
        if: always()
```

> On FAIL, run_review.py returns exit code 1 → the workflow is marked red. Reports are downloadable as artifacts.

---

## Option C: Doubao scheduled re-review (periodic drift prevention without git)

Even without git, "auto-review once a week/month" works via Doubao's **scheduled task (doubao-cron-scheduler)**:

1. Trigger: the scheduled task runs a "one-click review" command each period;
2. Command example:
   `python3 <skill-review-pro>/scripts/run_review.py <target-skill-dir> --out <reviews-dir>`;
3. After trigger, check:
   - new FAIL → the skill or external authoritative values (guideline/threshold upgrades) drifted; trigger re-review and fix per this skill's P1 / continuous governance;
   - no FAIL → record this round as reviewed, keep ready.
4. Suggested frequency: clinical/finance/security skills **monthly** or **when an external authority upgrades**; ordinary skills per version cycle.

> With P1 external-upgrade re-review: once an external value version locked by external_check.py (cspec vX.Y / year) expires, scheduled review automatically exposes "unlocked version / expired source" and triggers re-verification.

---

## Fallback principles

- run_review.py only does **machine pre-filtering**; semantic items in `semantic_review_points.md` (external-value truth, clone discrimination, whether L4 truly ran) **must be reviewed by human/AI** before declaring ready. CI blocking a "machine-layer FAIL" does not mean the semantic layer passed.
- In CI, do not point `--out` at a shared directory outside the target itself, to avoid multi-process write conflicts; run serially.
- Failure retries are limited to transient errors (network/timeout); "has FAIL" is a real conclusion — do not auto-retry to mask it.
