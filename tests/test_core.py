import unittest
from dataclasses import replace
from dmf_ca.core import Context, Engine, Fact
from dmf_ca.evaluate import cases, run


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.engine = Engine()
        self.ctx = Context("s1", 100, 100, tuple(Fact(k, v, "test", 0, 500, 90)
                           for k, v in (("role", "student"), ("purpose", "study"), ("phase", "open"))))

    def test_independent_policy_matrix(self):
        for ctx, status, (fields, constraints) in cases():
            with self.subTest(ctx=ctx):
                d = self.engine.project(ctx)
                self.assertEqual((d.status, set(d.fields), set(d.constraints)), (status, fields, constraints))
                if status != "adapted": self.assertFalse(d.relations)

    def test_interval_half_open(self):
        fs = tuple(replace(f, start=100, end=101, observed=100) for f in self.ctx.facts)
        self.assertEqual(self.engine.project(replace(self.ctx, facts=fs)).status, "adapted")
        self.assertEqual(self.engine.project(replace(self.ctx, at=101, facts=fs)).status, "abstain")

    def test_ttl_boundary(self):
        self.assertEqual(self.engine.project(replace(self.ctx, at=390)).status, "adapted")
        self.assertEqual(self.engine.project(replace(self.ctx, at=391)).status, "abstain")

    def test_as_of_knowledge(self):
        self.assertEqual(self.engine.project(replace(self.ctx, known_at=89)).status, "abstain")

    def test_confidence_boundary(self):
        self.assertEqual(self.engine.project(replace(self.ctx, facts=tuple(replace(f, confidence=.8) for f in self.ctx.facts))).status, "adapted")

    def test_order_independence_and_no_mutation(self):
        before = self.ctx
        a = self.engine.project(self.ctx)
        self.assertEqual(a, self.engine.project(replace(self.ctx, facts=self.ctx.facts[::-1])))
        self.assertEqual(before, self.ctx)
        self.assertEqual(a.rules, ("R1-study",))
        self.assertEqual(len(a.evidence), 3)
        self.assertTrue(a.relations)

    def test_invalid_fact(self):
        for kwargs in ({"confidence": float("nan")}, {"end": 0}, {"value": "admin"}, {"observed": 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.ctx.facts[0], **kwargs)

    def test_invalid_policy(self):
        with self.assertRaises(ValueError): Engine(ttl=-1)

    def test_reproducibility(self):
        a, b = run(), run()
        self.assertEqual(a["dataset_sha256"], b["dataset_sha256"])
        for x, y in zip(a["results"], b["results"]):
            for key in ("exact_accuracy", "excess_fields", "missing_fields_or_constraints", "abstentions"):
                self.assertEqual(x[key], y[key])


if __name__ == "__main__": unittest.main()
