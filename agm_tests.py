from __future__ import annotations

import unittest
from itertools import product

from belief_base import BeliefBase
from logic import Bicond, Conj, Formula, Neg, is_satisfiable, is_tautology, parse
from resolution import entails
from revision import contraction, expansion, revision


def _beliefs_are_consistent(formulas: list[Formula]) -> bool:
    if not formulas:
        return True
    return is_satisfiable(Conj(*formulas))


def _same_models(left: list[Formula], right: list[Formula]) -> bool:
    atoms = sorted({atom for formula in left + right for atom in formula.atoms()})

    for values in product((False, True), repeat=len(atoms)):
        valuation = dict(zip(atoms, values))
        left_holds = all(formula.eval(valuation) for formula in left)
        right_holds = all(formula.eval(valuation) for formula in right)
        if left_holds != right_holds:
            return False

    return True


class RevisionPostulateTests(unittest.TestCase):
    def test_success(self):
        bb = BeliefBase()
        bb.add(parse("p"), 2)
        bb.add(parse("q"), 1)

        self.assertTrue(entails(revision(bb, parse("r")).formulas(), parse("r")))
        self.assertTrue(entails(revision(bb, parse("~p")).formulas(), parse("~p")))
        self.assertTrue(entails(revision(bb, parse("p & r")).formulas(), parse("p & r")))
        self.assertTrue(entails(revision(BeliefBase(), parse("a")).formulas(), parse("a")))

    def test_inclusion(self):
        bb = BeliefBase()
        bb.add(parse("p"), 2)
        bb.add(parse("q"), 1)

        phi = parse("r")
        revised = revision(bb, phi)
        expanded = expansion(bb, phi)
        for formula in revised.formulas():
            self.assertTrue(entails(expanded.formulas(), formula))

        bb2 = BeliefBase()
        bb2.add(parse("p"), 2)
        bb2.add(parse("p >> q"), 1)
        revised2 = revision(bb2, parse("~q"))
        expanded2 = expansion(bb2, parse("~q"))
        for formula in revised2.formulas():
            self.assertTrue(entails(expanded2.formulas(), formula))

    def test_vacuity(self):
        bb = BeliefBase()
        bb.add(parse("p"), 2)
        bb.add(parse("q"), 1)
        phi = parse("r")
        self.assertFalse(entails(bb.formulas(), Neg(phi)))
        self.assertTrue(_same_models(revision(bb, phi).formulas(), expansion(bb, phi).formulas()))

        bb2 = BeliefBase()
        bb2.add(parse("a"), 2)
        phi2 = parse("b | c")
        self.assertFalse(entails(bb2.formulas(), Neg(phi2)))
        self.assertTrue(_same_models(revision(bb2, phi2).formulas(), expansion(bb2, phi2).formulas()))

    def test_consistency(self):
        bb = BeliefBase()
        bb.add(parse("p"), 2)
        bb.add(parse("q"), 1)
        self.assertTrue(_beliefs_are_consistent(revision(bb, parse("~p")).formulas()))

        bb2 = BeliefBase()
        bb2.add(parse("p"), 3)
        bb2.add(parse("p >> q"), 2)
        bb2.add(parse("q >> r"), 1)
        self.assertTrue(_beliefs_are_consistent(revision(bb2, parse("~r")).formulas()))

        bb3 = BeliefBase()
        bb3.add(parse("a"), 1)
        self.assertTrue(_beliefs_are_consistent(revision(bb3, parse("~a")).formulas()))

    def test_extensionality(self):
        bb = BeliefBase()
        bb.add(parse("p"), 2)
        bb.add(parse("q"), 1)

        phi = parse("~~r")
        psi = parse("r")
        self.assertTrue(is_tautology(Bicond(phi, psi)))
        self.assertTrue(_same_models(revision(bb, phi).formulas(), revision(bb, psi).formulas()))

        bb2 = BeliefBase()
        bb2.add(parse("r"), 2)
        self.assertTrue(
            _same_models(
                revision(bb2, parse("p | q")).formulas(),
                revision(bb2, parse("q | p")).formulas(),
            )
        )

    def test_contraction_uses_all_maximal_remainders(self):
        bb = BeliefBase()
        bb.add(parse("(p >> p) | r >> q & p"), 3)
        bb.add(parse("r <> p"), 1)
        bb.add(parse("~((~p >> p) & p)"), 1)

        contracted = contraction(bb, parse("r"))

        self.assertEqual(len(contracted.formulas()), 1)
        self.assertEqual(str(contracted.formulas()[0]), str(parse("(p >> p) | r >> q & p")))
        self.assertFalse(entails(contracted.formulas(), parse("r")))

    def test_partial_meet_intersection_not_maxichoice(self):
        bb = BeliefBase()
        bb.add(parse("p"), 1)
        bb.add(parse("p >> r"), 1)
        bb.add(parse("q"), 1)
        bb.add(parse("q >> r"), 1)

        contracted = contraction(bb, parse("r"))

        self.assertEqual(contracted.formulas(), [])
        self.assertFalse(entails(contracted.formulas(), parse("r")))

    def test_contraction_prefers_higher_priority_information(self):
        bb = BeliefBase()
        bb.add(parse("p"), 5)
        bb.add(parse("p >> r"), 1)
        bb.add(parse("q"), 1)
        bb.add(parse("q >> r"), 1)

        contracted = contraction(bb, parse("r"))

        self.assertEqual([str(formula) for formula in contracted.formulas()], ["p"])
        self.assertFalse(entails(contracted.formulas(), parse("r")))

    def test_contraction_by_tautology_is_identity(self):
        bb = BeliefBase()
        bb.add(parse("p"), 2)
        bb.add(parse("p >> q"), 1)

        tautology = parse("p | ~p")
        self.assertTrue(is_tautology(tautology))
        self.assertEqual(contraction(bb, tautology).items(), bb.items())


class ParserTests(unittest.TestCase):
    def test_rejects_operator_tokens_as_atoms(self):
        for token in (">>", "<>", "&", "|", ")"):
            with self.subTest(token=token):
                with self.assertRaises(SyntaxError):
                    parse(token)
    
    
    def test_rejects_empty_formula(self):
        with self.assertRaises(SyntaxError):
            parse("")


    def test_rejects_trailing_operator(self):
        with self.assertRaises(SyntaxError):
            parse("p &")


if __name__ == "__main__":
    unittest.main(verbosity=2)
