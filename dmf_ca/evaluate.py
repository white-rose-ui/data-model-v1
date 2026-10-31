"""Exhaustive synthetic conformance benchmark; no learned model or external data."""
import argparse
import hashlib
import itertools
import json
import platform
import random
import statistics
import time
from pathlib import Path
from .core import Context, Engine, Fact


def cases():
    # Independent policy table: do not derive expected outputs from engine rules.
    table = {
        ("student", "study"): ({"Student.id", "Course.id", "Course.title", "Enrollment.grade"}, {"own_enrollment"}),
        ("lecturer", "grading"): ({"Student.id", "Course.id", "Enrollment.grade"}, {"assigned_course"}),
        ("registrar", "registration"): ({"Student.id", "Course.id", "Course.capacity", "Enrollment.status"}, {"capacity_limit", "unique_student_course"}),
    }
    for role, purpose, phase, quality in itertools.product(
            ("student", "lecturer", "registrar"), ("study", "grading", "registration"),
            ("open", "closed"), ("valid", "missing", "stale", "conflict", "low", "future")):
        fs = [Fact(k, v, "fixture", 0, 2000, 90) for k, v in
              (("role", role), ("purpose", purpose), ("phase", phase))]
        if quality == "missing": fs.pop()
        if quality == "stale": fs = [Fact(f.key, f.value, f.source, 0, 2000, 0) for f in fs]
        if quality == "conflict": fs.append(Fact("phase", "closed" if phase == "open" else "open", "other", 0, 2000, 90))
        if quality == "low": fs[-1] = Fact("phase", phase, "fixture", 0, 2000, 90, 0.5)
        if quality == "future": fs[-1] = Fact("phase", phase, "fixture", 0, 2000, 500)
        at = 400 if quality == "stale" else 100
        expected = table.get((role, purpose), (set(), set()))
        if role == "registrar" and phase == "closed": expected = (set(), set())
        status = "abstain" if quality != "valid" else ("adapted" if expected[0] else "deny")
        if quality != "valid": expected = (set(), set())
        yield Context("synthetic-subject", at, at, tuple(fs)), status, expected


def run(seed=17, repeats=5):
    data = list(cases())
    random.Random(seed).shuffle(data)
    engine = Engine()
    rows = []
    for name in ("static_union", "role_only", "no_temporal", "dmf_ca"):
        latencies, correct, excess, omissions, abstentions = [], 0, 0, 0, 0
        for ctx, expected_status, (fields, constraints) in data:
            for _ in range(repeats):
                start = time.perf_counter_ns()
                if name in ("dmf_ca", "no_temporal"):
                    d = engine.project(ctx, temporal=name != "no_temporal")
                    actual, cons, status = set(d.fields), set(d.constraints), d.status
                else:
                    role = next(f.value for f in ctx.facts if f.key == "role")
                    options = {"student": {"Student.id", "Course.id", "Course.title", "Enrollment.grade"},
                               "lecturer": {"Student.id", "Course.id", "Enrollment.grade"},
                               "registrar": {"Student.id", "Course.id", "Course.capacity", "Enrollment.status"}}
                    actual = set.union(*options.values()) if name == "static_union" else options[role]
                    cons, status = set(), "adapted"
                latencies.append(time.perf_counter_ns() - start)
            correct += (actual == fields and cons == constraints and status == expected_status)
            excess += len(actual - fields)
            omissions += len(fields - actual) + len(constraints - cons)
            abstentions += status == "abstain"
        rows.append({"method": name, "cases": len(data), "exact_accuracy": correct / len(data),
                     "excess_fields": excess, "missing_fields_or_constraints": omissions,
                     "abstentions": abstentions, "median_ns": statistics.median(latencies),
                     "p95_ns": sorted(latencies)[int(0.95 * (len(latencies) - 1))]})
    corpus = json.dumps([(c.__dict__ | {"facts": [f.__dict__ for f in c.facts]}, s,
                          [sorted(e[0]), sorted(e[1])]) for c, s, e in data], sort_keys=True)
    return {"seed": seed, "repeats": repeats, "python": platform.python_version(),
            "platform": platform.platform(), "dataset_sha256": hashlib.sha256(corpus.encode()).hexdigest(),
            "results": rows}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="evaluation-output/results.json")
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--repeats", type=int, default=5)
    a = p.parse_args()
    if a.repeats < 1: p.error("repeats must be positive")
    result = run(a.seed, a.repeats)
    path = Path(a.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
