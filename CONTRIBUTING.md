# Contributing

Thank you for wanting to contribute to **Skill-Review-Pro**. This tool aims to give every SKILL.md skill a runnable, verifiable, releasable quality pipeline. Any change that makes that goal steadier or faster is welcome.

## What to contribute

- **New check layers / scripts**: peel "what a machine can deterministically decide" out of manual semantic review and turn it into a reusable script.
- **references rule enhancements**: additions to the checklist, CI guide, golden-source library, or test-set template.
- **Cases / examples**: pitfalls hit during review, real FAIL cases — archive them in `references/cases.md` (mandatory).
- **Docs & translation**: README, CN/EN editions, examples.
- **Bug fixes & issues**: script errors, false positives/negatives — all worth an issue.

## Development conventions

1. **Pure Python standard library**: scripts must not add third-party dependencies (argparse/json/re/subprocess/sys suffice), keeping zero-install usability.
2. **No hardcoded absolute paths**: all paths come from arguments/relative paths; cross-platform portable.
3. **Keep machine layer and semantic layer separate**: scripts only make "deterministically decidable" checks (format/count/ref/anti-pattern/external-value trace); semantic judgments (external-value truth, clone discrimination, whether L4 was truly run) go to `semantic_review_points.md` for human/AI review. **Do not** hardcode undecidable judgments into scripts.
4. **Self-review every change**: after each change run `python scripts/static_check.py .` to confirm this tool itself passes before committing.
5. **Sync version numbers**: when changing SKILL.md or script behavior, bump `version` in the SKILL.md frontmatter and state what changed in the version note.

## Submission workflow

1. Fork this repo, branch off `main`.
2. After changes, self-review (above) and add corresponding cases/docs.
3. Use clear imperative commit messages stating "what & why".
4. Open a PR, referencing any linked issue.
5. A maintainer runs `run_review.py` to re-check, then merges.

## Issue reporting

Include:
- the command triggered and the full output (exit code);
- the reviewed skill directory structure (desensitized if needed);
- expected vs actual behavior;
- whether it's a false positive/negative and the fix direction you expect.

## Code of conduct

Stay respectful and on-topic. This is a quality-engineering tool; no demeaning content targeting individuals, organizations, or platforms belongs in docs or examples.
