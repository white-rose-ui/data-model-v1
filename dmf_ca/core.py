from dataclasses import dataclass, asdict
from typing import Protocol
import hashlib
import json
import math

DOMAINS = {"role": {"student", "lecturer", "registrar"},
           "purpose": {"study", "grading", "registration"},
           "phase": {"open", "closed"}}


@dataclass(frozen=True)
class Fact:
    key: str
    value: str
    source: str
    start: int
    end: int
    observed: int
    confidence: float = 1.0

    def __post_init__(self):
        if self.key not in DOMAINS or self.value not in DOMAINS[self.key]:
            raise ValueError("unsupported context dimension or value")
        if not self.source or any(type(t) is not int for t in (self.start, self.end, self.observed)):
            raise ValueError("source and integer UTC epoch seconds required")
        if self.start >= self.end or not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("invalid interval or confidence")


@dataclass(frozen=True)
class Context:
    subject: str
    at: int
    known_at: int
    facts: tuple[Fact, ...]


class Adapter(Protocol):
    def acquire(self, subject: str, at: int, known_at: int) -> Context: ...


@dataclass(frozen=True)
class Rule:
    id: str
    conditions: tuple[tuple[str, str], ...]
    fields: tuple[str, ...]
    relations: tuple[str, ...]
    constraints: tuple[str, ...]


RULES = (
    Rule("R1-study", (("role", "student"), ("purpose", "study")),
         ("Student.id", "Course.id", "Course.title", "Enrollment.grade"),
         ("Enrollment.student->Student.id", "Enrollment.course->Course.id"), ("own_enrollment",)),
    Rule("R2-grade", (("role", "lecturer"), ("purpose", "grading")),
         ("Student.id", "Course.id", "Enrollment.grade"),
         ("Enrollment.student->Student.id", "Enrollment.course->Course.id"), ("assigned_course",)),
    Rule("R3-register", (("role", "registrar"), ("purpose", "registration"), ("phase", "open")),
         ("Student.id", "Course.id", "Course.capacity", "Enrollment.status"),
         ("Enrollment.student->Student.id", "Enrollment.course->Course.id"),
         ("capacity_limit", "unique_student_course")),
)


@dataclass(frozen=True)
class Decision:
    status: str
    fields: tuple[str, ...]
    relations: tuple[str, ...]
    constraints: tuple[str, ...]
    rules: tuple[str, ...]
    evidence: tuple[Fact, ...]
    issues: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict:
        return asdict(self)


class Engine:
    def __init__(self, ttl: int = 300, threshold: float = 0.8):
        if type(ttl) is not int or ttl < 0 or not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("invalid resolution policy")
        self.ttl, self.threshold = ttl, threshold

    def project(self, context: Context, *, temporal: bool = True) -> Decision:
        if not context.subject or type(context.at) is not int or type(context.known_at) is not int:
            raise ValueError("subject and integer query times required")
        resolved, evidence, issues = {}, [], []
        for key in sorted(DOMAINS):
            candidates = [f for f in context.facts if f.key == key
                          and f.confidence >= self.threshold and f.observed <= context.known_at
                          and (not temporal or (f.start <= context.at < f.end
                               and 0 <= context.at - f.observed <= self.ttl))]
            values = {f.value for f in candidates}
            if len(values) != 1:
                issues.append(key + (":conflict" if values else ":unknown"))
            else:
                resolved[key] = next(iter(values))
                evidence.extend(candidates)
        matched = [] if issues else [r for r in RULES if all(resolved.get(k) == v for k, v in r.conditions)]
        status = "abstain" if issues else ("adapted" if matched else "deny")
        fields = tuple(sorted({v for r in matched for v in r.fields}))
        relations = tuple(sorted({v for r in matched for v in r.relations}))
        constraints = tuple(sorted({v for r in matched for v in r.constraints}))
        evidence = tuple(sorted(set(evidence), key=lambda f: (f.key, f.value, f.source, f.start, f.end, f.observed, f.confidence)))
        payload = {"version": "1.0.0", "context": asdict(context), "ttl": self.ttl,
                   "threshold": self.threshold, "temporal": temporal}
        payload["context"]["facts"] = sorted(payload["context"]["facts"], key=lambda f: json.dumps(f, sort_keys=True))
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return Decision(status, fields, relations, constraints, tuple(r.id for r in matched), evidence, tuple(issues), digest)
