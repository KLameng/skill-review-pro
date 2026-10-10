# Group-Level L4 Test-Set Template (GAP-5, added in v1.2)

> Purpose: when behaviorally verifying a "skill group" (multiple sub-skills collaborating, e.g. an ACMG grading group), a single-skill test set is not enough — regression must be built at the **group-collaboration semantics** (combinatorial logic) level. This file gives the template.

## When to use a group-level test set

- The skill is composed of multiple sub-skills collaborating through a **scheduler** (e.g. "total scheduler scopes → per-code judgment → summary grading");
- There are **cross-skill combination rules** (exclusion matrix, combined rules, point system, threshold tables); errors often appear in combination, not single codes;
- The L4 three questions judge this group as must-run (deterministic-contract output + golden source + severe consequences).

## Group-level test-set construction steps

1. **Condense group rules into a machine-readable contract**: extract combination rules into three tables —
   - exclusion matrix (which evidence codes cannot coexist);
   - combined-rule table (classic rules: evidence-level combination → classification);
   - point system (evidence strength → points → classification interval).
2. **Draw cases from the golden source**: build "evidence-code set + level → expected classification" case rows from golden sources (guideline rule tables).
3. **Cover three domains**:
   - pathogenic domain (≥2PS, 3PM, PVS1+combination…); <!-- ext-ignore: template example, not external authoritative value -->
   - benign domain (1 BA1, ≥2 BS, 1BS+1BP…); <!-- ext-ignore: template example, not external authoritative value -->
   - boundary domain (right at threshold, exclusion pairs coexisting, PM1+PP3 soft notice, PVS1 downgrade states). <!-- ext-ignore: template example, not external authoritative value -->
4. **Run both schemes**: if the skill supports two methods (classic + point), align each to the golden separately, compute hit rates separately, and flag divergent cases.

## Case-table template

```
ID | Case (evidence code + level) | Golden | Plan A | Plan B | Gap/Notes
---|------------------------|------|-------|-------|--------
T1 | ≥2PS                   | P    | P     | LP    | Plan B misses pathogenic (classic vs point divergence)
T20| 2BS                    | B    | B     | B     | benign-domain reachability
T24| BA1 alone              | B    | B     | B     | stand-alone
```

- `Golden` must come from an external authority (see `golden-source-guide.md`), never self-invented;
- record each case's "input evidence code → expected classification"; scripts re-run (e.g. ACMG's `acmg_l4_combine_check_v2.py`).

## Assertion metrics

- **recall (no-miss priority)**: proportion of true P/LP among what the skill judged P/LP; clinical types strict; miss > set threshold → hard "behavior below threshold".
- **precision / full-hit rate**: fully-correct schemes / total cases.
- **benign-domain reachability**: whether all benign cases can run (whether benign codes can be scoped/judged) — a group-level-specific reachability check.
- **undefined/gap**: any case the skill cannot judge because a code is undefined → hard.

## Relation to single-skill L4

Single-skill L4 tests "does one sub-skill judge one code correctly"; group-level L4 tests "does the combination grade correctly". Complementary: single-code correct first, then combination correct. Group-level test sets usually expose problems single-code tests cannot see — "combination-rule contradictions", "benign unreachable", "cross-file inconsistency".

## Delivery

Archive the regression script + case table + result JSON together (write into review_report.json's behavior and registry) for governance drift comparison. Scripts are reusable (change cases, not logic).
