# Case Library

Review archival target. **Archive rule (mandatory)**: at the end of each review, all `hard` issues must be archived and typical `soft` ones too; entries come from the `archive` array of the review report, appended entry-by-entry — no manual additions or omissions. Note the profile and the corresponding check item.

| # | Title | Level | Check item | Profile |
|------|------|------|-----------|------|
| C-01 | Code snippet uses a tuple as a dict; executor copying it hits AttributeError | hard · code error | D2 | script |
| C-02 | Validation checklist hardcodes card count; next version's card-count change causes false report | soft · hardcoded version | D5 | script |
| C-03 | Step 5 builds a tuple, step 8 accesses `.P` attribute — contradictory | hard · rule contradiction | D7 | script |
| C-04 | Option name not in the enum; query has no KeyError fallback | hard · broken flow | D4 | script |
| C-05 | Doc-type skill lacks a "entry not found" exit; executor faced with an unlisted entry must improvise | soft · operability | D4 | document |
| C-06 | description trigger words too broad, hit by unrelated requests — no scope/object constraint | soft · declared boundary | L1-6 | document |
| C-07 | Review report Markdown vs JSON trigger separator inconsistency (TRIGGER 01 vs TRIGGER_01) | soft · term consistency | L1-3 | document |
| C-08 | Checklist total hardcoded across multiple spots; adding/removing entries requires cross-location sync | soft · hardcoded version | D5 | document |
| C-09 | Deterministic-contract failure: doc and code both correct, but runtime output format does not match the schema | hard · behavior below threshold | L4 | behavioral |
| C-10 | Skill reads embedded `.env` and leaks it; static scan hits the credential anti-pattern | hard · security red line | L5 | script |
| C-11 | Small test set (10 cases) yields 95% precision but skewed distribution; precision not generalizable | soft · small-sample false precision | L4 | behavioral |
| C-12 | Skill version changed but not re-evaluated; behavioral threshold decline not captured | soft · drift | governance | hybrid |
| C-13 | A data-asset skill judged "doc-type → L4 N/A" by a blanket rule, skipping the golden-sample regression it could run (calibration-set hit rate); behavioral verification missing (2026-09-30, skill-review-pro v1.1 fix triggered) | soft · profile routing | L4 | data_asset |
| C-14 | External authoritative value internally consistent but globally wrong: ACMG PTEN BA1 threshold is consistent across raw/parentheses/tables (self-consistent) yet differs 18× from ClinGen cspec v3.2 (skill 0.01 vs official 0.00056); all five layers passed without catching it — requires the L2.5 external-value verification layer to close the blind spot (2026-10-09, skill-review-pro v1.3 new trigger) | hard · external value untraceable | L2.5 | hybrid |
| C-15 | Clone detection looked only at doc similarity, missing "doc forked but execution body same-source" twins: ev-variant-literature-patient ↔ variant-literature-patient share main.py (2 scripts with identical content hash), SKILL.md one-new-one-old with similarity <85% slipped past v1.3, same execution body evolving separately = maximum drift risk — v1.4 adds a script-content-hash same-source channel (2026-10-10, skill-review-pro v1.4 trigger) | soft · drift | P2 | hybrid |
| C-16 | The review tool itself drowned in false positives: external_check reported 2 FAIL/7 WARN for skill-review-pro (no external authoritative values); every item judged a false positive — ① arrow `-> 0` caught by CMP_RE as comparator `>` ("grep old phrase -> 0 hits"); ② teaching/template examples treated as external values (doc self-referencing `<0.00001`, `0.002%`, template `≥2PS`/`1 BA1`). Conclusion: L2.5 should be N/A; but the tool flaw is exposed — a review tool's worst enemy is false positives; too many erode trust (2026-10-10, skill-review-pro v1.5 trigger) | soft · false-positive source | L2.5 | hybrid |
