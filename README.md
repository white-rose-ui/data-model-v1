# DMF-CA v1.0 research platform

Data Modelling Framework based on Context Awareness: an executable research specification and standard-library Python prototype for context-dependent logical model projections in an academic information system.

**Status:** first research prototype, not a production authorization service or a validated scientific contribution. No physical schema migrations or student records are changed.

## Run (Python 3.11+)

From this repository root, with no third-party runtime dependencies:

```sh
python -m unittest discover -s tests -v
python -m dmf_ca
python -m dmf_ca.evaluate --seed 17 --repeats 5 --output evaluation-output/results.json
```

The demo prints an open-registration model and an expired-context abstention. Evaluation writes machine-readable metrics, environment information, and a corpus hash. Optional packaging: `python -m pip install .` (requires a build backend). Running modules directly requires no installation.

## Deliverables

- [Implementation-ready research specification](docs/DMF-CA-v1.0.md): formal semantics, architecture, data model, interfaces, contracts, risks, and milestones.
- [Reproducible evaluation protocol](docs/EVALUATION.md): hypotheses, baselines, metrics, controls, and external validation plan.
- [Repository inspection](docs/REPOSITORY-REVIEW.md).
- `dmf_ca/core.py`: immutable typed context model, adapter protocol, rules, resolver and projection engine.
- `dmf_ca/__main__.py`: runnable academic-system case study.
- `tests/test_core.py`: matrix conformance, temporal boundaries, provenance, malformed inputs, determinism.
- `results/reference.json`: observed local benchmark output; latency is machine-specific.

Logical constraints in a projection are declarations for a downstream compiler. They are not enforced against database rows by this prototype. The caller must authenticate subjects, trust context sources, and enforce row predicates before releasing data. See the specification for the exact boundary.
