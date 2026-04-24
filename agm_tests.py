from __future__ import annotations

import random
import unittest

from belief_base import BeliefBase
from logic import (
    Atom, Bicond, Conj, Disj, Formula, Impl, Neg,
    equivalent, is_tautology, parse, to_clauses, to_cnf,
)
from resolution import entails, is_inconsistent
from revision import contraction, expansion, revision


def _consistent(formulas: list[Formula]) -> bool:
    return not is_inconsistent(formulas)


def _same_theory(left: list[Formula], right: list[Formula]) -> bool:
    """Cn(left) = Cn(right), verified by mutual entailment."""
    return all(entails(right, f) for f in left) and all(entails(left, f) for f in right)


def _tt_entails(kb: list[Formula], query: Formula) -> bool:
    """Ground-truth entailment by truth tables: KB |= q iff (/\\KB) -> q is a tautology."""
    return is_tautology(Impl(Conj(*kb), query))


def _make_base(spec: list[tuple[str, int]]) -> BeliefBase:
    bb = BeliefBase()
    for s, p in spec:
        bb.add(parse(s), p)
    return bb


# Matrix of bases used by the parameterised postulate tests. Each covers a
# different structural case: chained implications, independent atoms,
# ambiguous disjunctions, a deeper chain, and conjunctions.
BASES: list[list[tuple[str, int]]] = [
    [("p", 3), ("p >> q", 2), ("q >> r", 1)],
    [("a", 2), ("b", 2)],
    [("p | q", 1), ("p | ~q", 1)],
    [("a", 3), ("b", 2), ("c", 1), ("a >> d", 2), ("b >> d", 1)],
    [("p >> q", 2), ("q >> r", 2), ("r >> s", 1)],
    [("p & q", 2), ("q >> r", 1)],
]


def _random_formula(atoms: list[str], max_depth: int, rng: random.Random) -> Formula:
    if max_depth <= 0 or rng.random() < 0.35:
        return Atom(rng.choice(atoms))
    op = rng.choice(["~", "&", "|", ">>", "<>"])
    if op == "~":
        return Neg(_random_formula(atoms, max_depth - 1, rng))
    left = _random_formula(atoms, max_depth - 1, rng)
    right = _random_formula(atoms, max_depth - 1, rng)
    return {
        "&": Conj(left, right),
        "|": Disj(left, right),
        ">>": Impl(left, right),
        "<>": Bicond(left, right),
    }[op]


# AGM revision postulates. Closure (K*1) is formulated for belief sets; we
# operate on a finite base and so do not claim it directly.

class RevisionPostulates(unittest.TestCase):
    def setUp(self) -> None:
        self.bb = BeliefBase()
        self.bb.add(parse("p"), 3)
        self.bb.add(parse("p >> q"), 2)
        self.bb.add(parse("q >> r"), 1)

    def test_success(self):
        # (K*2) B * phi entails phi.
        self.assertTrue(entails(revision(self.bb, parse("s")).formulas(), parse("s")))
        self.assertTrue(entails(revision(self.bb, parse("~r")).formulas(), parse("~r")))
        self.assertTrue(entails(revision(BeliefBase(), parse("a")).formulas(), parse("a")))

    def test_inclusion(self):
        # (K*3) B * phi is contained in Cn(B + phi).
        for phi in (parse("s"), parse("~q")):
            rev = revision(self.bb, phi).formulas()
            exp = expansion(self.bb, phi).formulas()
            for f in rev:
                self.assertTrue(entails(exp, f))

    def test_vacuity(self):
        # (K*4) If ~phi is not entailed, revision coincides with expansion.
        phi = parse("s")
        self.assertFalse(entails(self.bb.formulas(), Neg(phi)))
        self.assertTrue(_same_theory(
            revision(self.bb, phi).formulas(),
            expansion(self.bb, phi).formulas(),
        ))

    def test_consistency(self):
        # (K*5) If phi is consistent, B * phi is consistent.
        self.assertTrue(_consistent(revision(self.bb, parse("~r")).formulas()))
        self.assertTrue(_consistent(revision(self.bb, parse("~p"), priority=5).formulas()))

    def test_extensionality(self):
        # (K*6) Logically equivalent inputs yield the same revision.
        for phi, psi in [
            (parse("~~s"), parse("s")),
            (parse("~(p & q)"), parse("~p | ~q")),
            (parse("p >> q"), parse("~p | q")),
        ]:
            self.assertTrue(equivalent(phi, psi))
            self.assertTrue(_same_theory(
                revision(self.bb, phi).formulas(),
                revision(self.bb, psi).formulas(),
            ))


# Contraction postulates relevant to partial meet on a belief base.

class ContractionPostulates(unittest.TestCase):
    def setUp(self) -> None:
        self.bb = BeliefBase()
        self.bb.add(parse("p"), 3)
        self.bb.add(parse("p >> q"), 2)
        self.bb.add(parse("q >> r"), 1)

    def test_inclusion(self):
        # (K-2) B / phi is contained in Cn(B).
        for f in contraction(self.bb, parse("r")).formulas():
            self.assertTrue(entails(self.bb.formulas(), f))

    def test_vacuity(self):
        # (K-3) If B does not entail phi, contraction is identity.
        phi = parse("s")
        self.assertFalse(entails(self.bb.formulas(), phi))
        self.assertEqual(contraction(self.bb, phi).items(), self.bb.items())

    def test_success(self):
        # (K-4) If phi is not a tautology, B / phi does not entail phi.
        self.assertFalse(entails(contraction(self.bb, parse("r")).formulas(), parse("r")))
        self.assertFalse(entails(contraction(self.bb, parse("q")).formulas(), parse("q")))

    def test_extensionality(self):
        # (K-6) Logically equivalent formulas yield the same contraction.
        self.assertTrue(_same_theory(
            contraction(self.bb, parse("r")).formulas(),
            contraction(self.bb, parse("~~r")).formulas(),
        ))

    def test_tautology_is_identity(self):
        tautology = parse("p | ~p")
        self.assertTrue(is_tautology(tautology))
        self.assertEqual(contraction(self.bb, tautology).items(), self.bb.items())


# Partial meet selection: intersection semantics and priority order.

class PartialMeetBehaviour(unittest.TestCase):
    def test_intersection_is_not_maxichoice(self):
        # Four equally-preferred remainders; partial meet intersects them.
        bb = BeliefBase()
        for f in ("p", "p >> r", "q", "q >> r"):
            bb.add(parse(f), 1)
        contracted = contraction(bb, parse("r"))
        self.assertEqual(contracted.formulas(), [])

    def test_priority_breaks_ties(self):
        bb = BeliefBase()
        bb.add(parse("p"), 5)
        bb.add(parse("p >> r"), 1)
        bb.add(parse("q"), 1)
        bb.add(parse("q >> r"), 1)
        self.assertEqual([str(f) for f in contraction(bb, parse("r")).formulas()], ["p"])

    def test_priority_profile_is_lexicographic(self):
        # Profile (5, 4) beats (4, 4, 4): first element wins before length.
        bb = BeliefBase()
        bb.add(parse("p"), 5)
        bb.add(parse("p >> q"), 4)
        bb.add(parse("p >> r"), 4)
        self.assertEqual([str(f) for f in contraction(bb, parse("q | r")).formulas()], ["p"])

    def test_all_maximal_remainders_are_considered(self):
        bb = BeliefBase()
        bb.add(parse("(p >> p) | r >> q & p"), 3)
        bb.add(parse("r <> p"), 1)
        bb.add(parse("~((~p >> p) & p)"), 1)
        contracted = contraction(bb, parse("r"))
        self.assertEqual(len(contracted.formulas()), 1)
        self.assertFalse(entails(contracted.formulas(), parse("r")))


# Resolution entailment.
class ResolutionCorrectness(unittest.TestCase):
    def test_classical_inference_rules(self):
        cases = [
            ([parse("p"), parse("p >> q")], parse("q")),# modus ponens
            ([parse("p >> q"), parse("~q")], parse("~p")),# modus tollens
            ([parse("p >> q"), parse("q >> r")], parse("p >> r")),# hypothetical syllogism
            ([parse("p | q"), parse("~p")], parse("q")),# disjunctive syllogism
        ]
        for kb, q in cases:
            self.assertTrue(entails(kb, q))

    def test_inconsistency_and_nonentailment(self):
        self.assertTrue(is_inconsistent([parse("p"), parse("~p")]))
        self.assertFalse(is_inconsistent([parse("p"), parse("p >> q"), parse("q")]))
        self.assertFalse(entails([parse("p"), parse("p >> q")], parse("r")))

    def test_tautology_from_empty_kb(self):
        self.assertTrue(entails([], parse("p | ~p")))
        self.assertTrue(entails([], parse("(p >> q) | (q >> p)")))

    def test_agrees_with_truth_tables(self):
        cases: list[tuple[list[str], str, bool]] = [
            (["p & q"], "p", True),
            (["p | q", "~p"], "q", True),
            (["(p >> q) & (q >> r)"], "p >> r", True),
            (["p"], "q", False),
            (["~(p & q)"], "~p | ~q", True),
            (["p | q"], "p", False),
        ]
        for kb_strs, query_str, expected in cases:
            kb = [parse(s) for s in kb_strs]
            self.assertEqual(entails(kb, parse(query_str)), expected, kb_strs)


# CNF and parser.
class CNFAndParser(unittest.TestCase):
    def test_cnf_structure(self):
        # p <> q becomes two clauses; ~(p & q) becomes one.
        biconds = to_clauses(parse("p <> q"))
        self.assertIn(frozenset({("p", False), ("q", True)}), biconds)
        self.assertIn(frozenset({("p", True), ("q", False)}), biconds)
        self.assertEqual(
            to_clauses(parse("~(p & q)")),
            {frozenset({("p", False), ("q", False)})},
        )

    def test_cnf_preserves_meaning(self):
        for text in ["p & (q | r)", "(p | q) & (~p | r)", "~(p <> q)", "p >> q >> r"]:
            self.assertTrue(equivalent(parse(text), to_cnf(parse(text))), text)

    def test_parser_precedence_and_associativity(self):
        self.assertEqual(parse("p >> q >> r"), Impl(Atom("p"), Impl(Atom("q"), Atom("r"))))
        self.assertEqual(parse("p | q & r"), Disj(Atom("p"), Conj(Atom("q"), Atom("r"))))
        self.assertEqual(parse("~p & q"), Conj(Neg(Atom("p")), Atom("q")))

    def test_parser_rejects_malformed(self):
        for bad in ("", "&", "p &", "(p & q", "p & q)", "& p", "p && q"):
            with self.subTest(input=bad):
                with self.assertRaises(SyntaxError):
                    parse(bad)


# Parameterised postulate matrix. Each postulate is checked across the set
# of bases in BASES and a spread of phi inputs, including fresh atoms,
# atoms entailed by the base, their negations, tautology, contradiction,
# and cross-atom formulas.

class ParameterisedRevisionPostulates(unittest.TestCase):
    PHIS = ["s", "~r", "q", "p | ~p", "~p", "a & b", "~(p & q)", "p & ~p"]

    def test_success(self):
        # (K*2) B * phi entails phi, across every base and phi.
        for spec in BASES:
            for phi_s in self.PHIS:
                with self.subTest(base=spec, phi=phi_s):
                    bb = _make_base(spec)
                    phi = parse(phi_s)
                    rev = revision(bb, phi).formulas()
                    self.assertTrue(entails(rev, phi))

    def test_inclusion(self):
        # (K*3) B * phi subset of Cn(B + phi).
        for spec in BASES:
            for phi_s in self.PHIS:
                with self.subTest(base=spec, phi=phi_s):
                    bb = _make_base(spec)
                    phi = parse(phi_s)
                    rev = revision(bb, phi).formulas()
                    exp = expansion(bb, phi).formulas()
                    for f in rev:
                        self.assertTrue(entails(exp, f))

    def test_vacuity(self):
        # (K*4) If ~phi is not entailed by B, revision coincides with expansion.
        for spec in BASES:
            for phi_s in self.PHIS:
                bb = _make_base(spec)
                phi = parse(phi_s)
                if entails(bb.formulas(), Neg(phi)):
                    continue  # precondition of vacuity fails; skip
                with self.subTest(base=spec, phi=phi_s):
                    self.assertTrue(_same_theory(
                        revision(bb, phi).formulas(),
                        expansion(bb, phi).formulas(),
                    ))

    def test_consistency(self):
        # (K*5) If phi is consistent, B * phi is consistent.
        for spec in BASES:
            for phi_s in self.PHIS:
                bb = _make_base(spec)
                phi = parse(phi_s)
                if is_inconsistent([phi]):
                    continue  # precondition fails; skip
                with self.subTest(base=spec, phi=phi_s):
                    self.assertTrue(_consistent(revision(bb, phi).formulas()))

    def test_extensionality(self):
        # (K*6) Logically equivalent inputs yield the same revision.
        pairs = [
            ("s", "~~s"),
            ("~(p & q)", "~p | ~q"),
            ("p >> q", "~p | q"),
            ("p <> q", "(p & q) | (~p & ~q)"),
            ("(p | q) & (p | ~q)", "p"),
        ]
        for spec in BASES:
            for phi_s, psi_s in pairs:
                bb = _make_base(spec)
                phi, psi = parse(phi_s), parse(psi_s)
                with self.subTest(base=spec, phi=phi_s, psi=psi_s):
                    self.assertTrue(equivalent(phi, psi))
                    self.assertTrue(_same_theory(
                        revision(bb, phi).formulas(),
                        revision(bb, psi).formulas(),
                    ))


class ParameterisedContractionPostulates(unittest.TestCase):
    PHIS = ["r", "q", "p", "~p", "q | r", "p & q", "p | ~p"]

    def test_inclusion(self):
        # (K-2) B / phi subset of Cn(B).
        for spec in BASES:
            for phi_s in self.PHIS:
                with self.subTest(base=spec, phi=phi_s):
                    bb = _make_base(spec)
                    for f in contraction(bb, parse(phi_s)).formulas():
                        self.assertTrue(entails(bb.formulas(), f))

    def test_success(self):
        # (K-4) If phi is not a tautology, B / phi does not entail phi.
        for spec in BASES:
            for phi_s in self.PHIS:
                bb = _make_base(spec)
                phi = parse(phi_s)
                if is_tautology(phi):
                    continue
                with self.subTest(base=spec, phi=phi_s):
                    contracted = contraction(bb, phi).formulas()
                    self.assertFalse(entails(contracted, phi))

    def test_vacuity(self):
        # (K-3) If B does not entail phi, contraction is identity.
        for spec in BASES:
            for phi_s in self.PHIS:
                bb = _make_base(spec)
                phi = parse(phi_s)
                if entails(bb.formulas(), phi):
                    continue
                with self.subTest(base=spec, phi=phi_s):
                    self.assertEqual(contraction(bb, phi).items(), bb.items())

    def test_extensionality(self):
        # (K-6) Logically equivalent formulas yield the same contraction.
        pairs = [
            ("r", "~~r"),
            ("~(p & q)", "~p | ~q"),
            ("p >> q", "~p | q"),
            ("p <> q", "(p & q) | (~p & ~q)"),
        ]
        for spec in BASES:
            for phi_s, psi_s in pairs:
                bb = _make_base(spec)
                phi, psi = parse(phi_s), parse(psi_s)
                with self.subTest(base=spec, phi=phi_s, psi=psi_s):
                    self.assertTrue(equivalent(phi, psi))
                    self.assertTrue(_same_theory(
                        contraction(bb, phi).formulas(),
                        contraction(bb, psi).formulas(),
                    ))


# Recovery (K-5) fails on belief bases in general. We document a concrete
# counterexample rather than silently omitting the postulate.

class RecoveryFailsOnBases(unittest.TestCase):
    def test_recovery_counterexample(self):
        # B = {p & q}. Contract with p.
        # The only subset of B that does not entail p is the empty set,
        # so B / p = {}. Then Cn({} u {p}) = Cn({p}), which does NOT contain
        # p & q. Recovery (B subset of Cn((B/phi) u {phi})) therefore fails.
        bb = BeliefBase()
        bb.add(parse("p & q"), 1)
        contracted = contraction(bb, parse("p")).formulas()
        recovered = contracted + [parse("p")]
        self.assertFalse(
            entails(recovered, parse("p & q")),
            "Recovery would require p & q in Cn((B / p) u {p}), "
            "but partial meet on belief bases does not recover it.",
        )


# Boundary inputs the parameterised matrix does not exercise directly.

class EdgeCases(unittest.TestCase):
    def test_empty_base_contraction_is_empty(self):
        self.assertEqual(contraction(BeliefBase(), parse("p")).items(), [])

    def test_empty_base_expansion(self):
        expanded = expansion(BeliefBase(), parse("p"), priority=1)
        self.assertEqual([str(f) for f in expanded.formulas()], ["p"])

    def test_empty_base_revision(self):
        revised = revision(BeliefBase(), parse("p"), priority=1)
        self.assertTrue(entails(revised.formulas(), parse("p")))

    def test_contraction_of_tautology_is_identity(self):
        bb = BeliefBase()
        bb.add(parse("p"), 1)
        self.assertEqual(contraction(bb, parse("p | ~p")).items(), bb.items())

    def test_contraction_of_contradiction_on_consistent_base(self):
        # Consistent B does not entail a contradiction, so vacuity gives identity.
        bb = BeliefBase()
        bb.add(parse("p"), 1)
        self.assertEqual(contraction(bb, parse("q & ~q")).items(), bb.items())

    def test_revision_with_tautology_preserves_base(self):
        bb = BeliefBase()
        bb.add(parse("p"), 1)
        revised = revision(bb, parse("q | ~q"), priority=1)
        self.assertTrue(entails(revised.formulas(), parse("p")))
        self.assertTrue(entails(revised.formulas(), parse("q | ~q")))

    def test_revision_with_contradiction_yields_inconsistent_base(self):
        bb = BeliefBase()
        bb.add(parse("p"), 1)
        revised = revision(bb, parse("q & ~q"), priority=1)
        self.assertTrue(is_inconsistent(revised.formulas()))


# Randomised fuzz: resolution-based entailment must agree with truth tables
# on every (kb, query) pair. Seeded so failures are reproducible.

class ResolutionAgreesWithTruthTables(unittest.TestCase):
    ITERATIONS = 80

    def test_fuzz(self):
        rng = random.Random(42)
        atoms = ["p", "q", "r"]
        for i in range(self.ITERATIONS):
            kb_size = rng.randint(0, 3)
            kb = [_random_formula(atoms, max_depth=2, rng=rng) for _ in range(kb_size)]
            query = _random_formula(atoms, max_depth=2, rng=rng)
            with self.subTest(i=i, kb=[str(f) for f in kb], query=str(query)):
                self.assertEqual(
                    entails(kb, query),
                    _tt_entails(kb, query),
                    f"resolution disagrees with truth table on "
                    f"kb={[str(f) for f in kb]}, query={query}",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)