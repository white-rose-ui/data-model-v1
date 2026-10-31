# Reproducible evaluation protocol

## Questions and hypotheses

RQ1: Does explicit context improve model appropriateness over static and role-only models? H1: lower excess attribute rate and higher exact model agreement on independently labelled valid contexts.

RQ2: Does temporal qualification reduce inappropriate projection under outdated context? H2: fewer stale-context releases than the no-temporal ablation, with the cost measured as abstention on recoverable contexts.

RQ3: Can independent reviewers reconstruct decisions from evidence and rules? H3: improved reconstruction correctness and time compared with outputs lacking trace. H3 is not evaluated by the synthetic runner.

## Executable M1 benchmark

Run from repository root on Python 3.11+:

```sh
python -m unittest discover -s tests -v
python -m dmf_ca
python -m dmf_ca.evaluate --seed 17 --repeats 5 --output evaluation-output/results.json
```

No external dataset, training, network or third-party runtime dependency is used. All 108 cases are generated in `dmf_ca.evaluate.cases`: roles × purposes × phases × {valid, missing phase, stale observations, conflicting phase, low-confidence phase, future-observed phase}. Query time is 100 (400 for stale); known_at equals query time. Facts normally start at 0, expire at 2000, observed at 90. Stale facts observed at 0; low confidence = 0.5; future = 500. Seed 17 shuffles the complete corpus; it does not sample cases or simulate independent populations. Repeats measure runtime, not statistical sample size.

Independent oracle is the explicit expected table in the evaluator; it shares the policy specification with the engine but does not derive expected outputs from engine rules. This avoids implementation mirroring but remains a constructed conformance test. Rule changes require separately reviewed oracle changes.

| Method | Context used | Purpose |
|---|---|---|
| static_union | none; union of all candidate fields, no contextual constraints | conventional unfiltered metadata baseline |
| role_only | first synthetic role, no quality/temporal checks, no contextual constraints | simple context baseline |
| no_temporal | same resolver/rules as DMF-CA except interval/freshness filtering | temporal ablation |
| dmf_ca | all dimensions, quality, conflict and temporal checks | proposed reference method |

These simple baselines are intentionally transparent and are not strong production access-control systems. Do not claim superiority over all conventional modelling systems. Static output is considered `adapted`; its missing contextual constraints count against agreement. For fair external comparison, add a manually engineered role/purpose policy with equal enforcement features.

Metrics: exact_accuracy = cases with exact status, field set and constraint set / all cases; excess_fields = total |actual_fields − expected_fields|; missing_fields_or_constraints = total |expected_fields − actual_fields| + |expected_constraints − actual_constraints|; abstentions = count of abstain decisions. Exact accuracy currently excludes relationship-set agreement; matrix tests check no relationships on non-adapted outputs, and relation content is separately tested for R1. Add full relationship scoring before using benchmark results as whole-model correctness claims. Latency median/p95 includes each method's work in the measured branch, including trace/hash construction for DMF-CA; compare end-to-end costs rather than attributing differences solely to inference.

Reference output in `results/reference.json` records observed values from one local run. Semantic metrics and corpus hash must repeat for the same seed/version. Timing and platform fields are expected to differ. A perfect synthetic result verifies chosen rules against fixtures; it is not evidence of real-world predictive performance, policy correctness, generalization or novelty.

## M3/M4 empirical study (planned, not completed)

1. Recruit domain experts from at least three academic units. Obtain approval for any actual institutional data; prefer de-identified metadata and policy vignettes. Publish a data dictionary and permitted redistribution terms before collecting data.
2. Freeze the policy/rule version using training units/terms. Split by institution or term rather than individual near-duplicate requests. Keep one unit/term held out. Do not tune thresholds using the held-out labels.
3. Two independent experts label required entities, fields, relationships, constraints, expected deny/abstain, and uncertainty for each scenario while blinded to engine output. Report agreement per element type (including Cohen's kappa for categorical status), disagreements and adjudication rules. Preserve original labels.
4. Include role/purpose changes, semester transitions, multi-source disagreement, delayed observations, missingness and confidence perturbations. Pair all methods on identical inputs. Include equal-feature manual policy and no-quality/conflict ablations in addition to M1 methods.
5. Measure field/relation precision and recall, exact constraint-set agreement, inappropriate release rate on invalid contexts, coverage on valid contexts, and trace completeness (all emitted elements linked to a rule and eligible facts). Report denominators and per-unit/per-status strata; do not hide low coverage behind precision.
6. Bootstrap paired differences at the independent unit/episode level with 10,000 resamples and fixed seed 17; report 95% intervals, effect sizes and full distributions. If testing multiple primary hypotheses, predeclare correction and primary metric. Determine sample size from pilot effect/variance and a power analysis; do not treat the 108 synthetic cases as a powered empirical sample.
7. For H3, use a counterbalanced reviewer study with blinded scenario assignment; measure decision reconstruction correctness, explanation errors and elapsed time. Collect consent and report reviewer expertise. No reviewer study has been run.
8. Benchmark scale at 10, 100, 1,000 and 10,000 facts per query, separating acquisition, resolution, projection, canonicalization and serialization. Run warmups then at least 30 measured batches on documented hardware; record CPU, RAM, OS, Python, commit SHA, cache policy and process isolation. Separate throughput/concurrency from single-query latency. M1 runner measures only the tiny fixed corpus.

Archive commit SHA, exact commands, raw per-case predictions, frozen corpus and split manifest, label guidelines, adjudications, dependency/environment lock, random seeds, aggregate code and negative results. The M1 runner provides aggregate JSON and a corpus hash; per-case empirical export, bootstrap analysis and scaling harness are future deliverables. Gate M2 on enforcement tests and M4 on independent labels rather than a numeric synthetic accuracy target.
