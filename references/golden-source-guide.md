# L4 Golden-Source Library (GAP-4, added in v1.2)

> Purpose: L4 behavioral verification requires "use authoritative labels, never invent them". This file gives **authoritative golden-source recommendations by domain**, so executors don't improvise or self-invent labels from domain knowledge alone (self-invention = fake verification).

## Three hard rules for choosing a golden source

1. **External authority first**: prefer judgment/classification labels published by external organizations, traceable (guidelines, standards, official databases); never use the skill's own output as its golden source (self-reference = fake verification).
2. **Version lock**: record source + version + retrieval date for the golden source (e.g. "ACMG-AMP 2015 Table 5", "Tavtigian et al 2020"), and state it in the report; after a guideline/standard upgrade, re-verify per the continuous-governance re-evaluation trigger.
3. **Scale and skew**: test set ≥20 cases or sized by golden-source volume; must cover positive/negative samples and boundaries, guarding against "small-sample false precision".

## Recommended sources by domain

| Skill domain | Recommended golden sources | Notes |
|---|---|---|
| Clinical/genetics (variant classification) | ACMG/AMP 2015 combined rules; ACMG/SVI updates; ClinGen VCEP gene-specific rules; ClinVar authoritative submissions | Build combined regression from guideline rule tables + ClinVar curated labels |
| Variant classification (point system) | Tavtigian et al 2020 point system; ACMG 2023 draft intervals | Run separately from classic rules, align each |
| Gene/phenotype naming | HGNC, OMIM, GenCC (MOI), ClinVar | Compare standardized fields |
| Security/vulnerability (L5-related skills) | OWASP Top 10, NIST, CWE, CVE | Map judgments to public vulnerability databases |
| Code/script skills | Official test suites, language spec, reproducible golden outputs | Run real inputs against expected outputs |
| Finance/compliance | Regulatory documents, industry-association rules, public disclosures | Mark "verified" vs "one-party claims" |
| General document/data-asset | Skill's own golden-sample/calibration set (e.g. coordinate-library golden, mapping crosswalk) | Data-asset skills reuse built-in golden by preference |

## Building a golden-sample set yourself (no external authority)

If a domain has no external authority, use a **dual-annotator independent labeling + dispute arbitration** calibration set (human-annotated; must note in the report "human-annotated, not external authority"), or a **counterexample set** (known-error/boundary cases verifying the skill does not miss). When the user prefers not to do kappa verification requiring human annotators, defer verification to community ratification after open-sourcing; execution focuses only on the automated parts that do not depend on human annotation (e.g. rule-combination regression, script golden).

## Golden source → regression-case mapping

Each golden entry should map to concrete test cases (input → expected output), forming a re-runnable regression set. For group-level multi-skill, use the organization in `l4-group-testset-template.md` (exclusion matrix + combined rules + point system → case table).

## Lightweight L4 for clinical skills (P5, v1.3: single-evidence-code fragment regression)

When full-grading L4 is too costly (no authoritative full-variant golden / high real-sample cost / needs human annotation), **do not skip behavioral verification** — use **single-evidence-code fragment regression**, verifying only the correctness of one evidence code's decision rule, without the full "variant → grading" loop:

- **Target**: a single decision rule in the skill (e.g. REVEL→PP3/BP4 strength, AF→BA1/BS1/PM2 tier, exclusion-pair choice).
- **Case source**: draw "evidence code → expected strength" cases from ClinVar curated variants / ClinGen VCEP rule tables / published cases, not self-invented.
- **Case form**: `input parameter → expected evidence-code strength` (e.g. `REVEL=0.84 → PP3_Moderate`; `AF=0.02% and HL-AD → satisfies PM2`).
- **Scale**: ≥10 per rule, covering boundaries (above/below threshold, interval endpoints).
- **Judgment**: the rate at which the skill rule maps each input to the expected strength = that rule's fragment precision; below the set threshold → L4 below threshold.
- **Advantages**: no dependence on a full-grading golden; single rules regress alone; low cost, auto re-runnable; multiple rules assembled approximate full L4.
- **Template**: `l4-group-testset-template.md` (exclusion matrix / combined rules / point system → case table, splittable to single-evidence-code granularity).
