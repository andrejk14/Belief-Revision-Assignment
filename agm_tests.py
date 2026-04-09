"""
AGM postulate verification tests for the belief revision engine.
Tests: Success, Inclusion, Vacuity, Consistency, Extensionality.
"""
from logic import Formula, Atom, Not, And, Or, Implies, Biconditional, parse, is_tautology, is_satisfiable, formulas_equivalent
from resolution import entails
from belief_base import BeliefBase
from revision import expansion, contraction, revision


def test_success():
    """
    Success postulate: phi ∈ Cn(B * phi)
    After revising by phi, the belief base should entail phi.
    """
    print("Testing SUCCESS postulate...")
    passed = True

    # Test 1: revise with a simple atom
    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)
    phi = parse("r")
    revised = revision(bb, phi)
    if not entails(revised.get_formulas(), phi):
        print("  FAIL: B * r should entail r")
        passed = False

    # Test 2: revise with negation of existing belief
    bb2 = BeliefBase()
    bb2.add(parse("p"), 2)
    phi2 = parse("~p")
    revised2 = revision(bb2, phi2)
    if not entails(revised2.get_formulas(), phi2):
        print("  FAIL: B * ~p should entail ~p")
        passed = False

    # Test 3: revise with a compound formula
    bb3 = BeliefBase()
    bb3.add(parse("p"), 2)
    bb3.add(parse("q"), 1)
    phi3 = parse("p & r")
    revised3 = revision(bb3, phi3)
    if not entails(revised3.get_formulas(), phi3):
        print("  FAIL: B * (p & r) should entail (p & r)")
        passed = False

    if passed:
        print("  PASS")
    return passed


def test_inclusion():
    """
    Inclusion postulate: B * phi ⊆ Cn(B + phi)
    The revised belief base should be a subset of the expanded one (in terms of consequences).
    Every formula entailed by B * phi should also be entailed by B + phi.
    """
    print("Testing INCLUSION postulate...")
    passed = True

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)
    phi = parse("r")

    revised = revision(bb, phi)
    expanded = expansion(bb, phi)

    # Check that every formula in the revised base is entailed by the expanded base
    for f in revised.get_formulas():
        if not entails(expanded.get_formulas(), f):
            print(f"  FAIL: {f} in B * phi but not in Cn(B + phi)")
            passed = False

    # Test with conflicting belief
    bb2 = BeliefBase()
    bb2.add(parse("p"), 2)
    bb2.add(parse("p >> q"), 1)
    phi2 = parse("~q")
    revised2 = revision(bb2, phi2)
    expanded2 = expansion(bb2, phi2)

    for f in revised2.get_formulas():
        if not entails(expanded2.get_formulas(), f):
            print(f"  FAIL: {f} in B * phi but not in Cn(B + phi)")
            passed = False

    if passed:
        print("  PASS")
    return passed


def test_vacuity():
    """
    Vacuity postulate: If ~phi ∉ Cn(B), then B * phi = B + phi
    If the negation is not entailed, revision equals expansion.
    """
    print("Testing VACUITY postulate...")
    passed = True

    # p and q in base, revise by r — ~r is not entailed
    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)
    phi = parse("r")

    # Confirm ~phi is not entailed
    if entails(bb.get_formulas(), Not(phi)):
        print("  SKIP: ~phi is entailed (test setup error)")
        return True

    revised = revision(bb, phi)
    expanded = expansion(bb, phi)

    # Both should have the same formulas
    rev_formulas = set(str(f) for f in revised.get_formulas())
    exp_formulas = set(str(f) for f in expanded.get_formulas())

    if rev_formulas != exp_formulas:
        print(f"  FAIL: B * phi != B + phi when ~phi not in Cn(B)")
        print(f"    Revised:  {rev_formulas}")
        print(f"    Expanded: {exp_formulas}")
        passed = False

    if passed:
        print("  PASS")
    return passed


def test_consistency():
    """
    Consistency postulate: If phi is consistent, then B * phi is consistent.
    """
    print("Testing CONSISTENCY postulate...")
    passed = True

    # Test 1: revise with consistent formula
    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)
    phi = parse("~p")

    if not is_satisfiable(phi):
        print("  SKIP: phi is not satisfiable")
        return True

    revised = revision(bb, phi)
    formulas = revised.get_formulas()

    # Check consistency: the conjunction of all formulas should be satisfiable
    if formulas:
        conjunction = formulas[0]
        for f in formulas[1:]:
            conjunction = And(conjunction, f)
        if not is_satisfiable(conjunction):
            print("  FAIL: B * phi is inconsistent when phi is consistent")
            passed = False

    # Test 2: another case
    bb2 = BeliefBase()
    bb2.add(parse("p"), 3)
    bb2.add(parse("p >> q"), 2)
    bb2.add(parse("q >> r"), 1)
    phi2 = parse("~r")

    revised2 = revision(bb2, phi2)
    formulas2 = revised2.get_formulas()

    if formulas2:
        conjunction2 = formulas2[0]
        for f in formulas2[1:]:
            conjunction2 = And(conjunction2, f)
        if not is_satisfiable(conjunction2):
            print("  FAIL: B * ~r is inconsistent")
            passed = False

    if passed:
        print("  PASS")
    return passed


def test_extensionality():
    """
    Extensionality postulate: If phi <=> psi is a tautology, then B * phi = B * psi
    Logically equivalent formulas should produce the same revision.
    """
    print("Testing EXTENSIONALITY postulate...")
    passed = True

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)

    # phi and psi are logically equivalent: ~~r and r
    phi = parse("~~r")
    psi = parse("r")

    # Verify they're equivalent
    if not is_tautology(Biconditional(phi, psi)):
        print("  SKIP: phi and psi are not equivalent")
        return True

    revised_phi = revision(bb, phi)
    revised_psi = revision(bb, psi)

    # The revised bases should entail the same things
    # Check: each formula in one is entailed by the other
    for f in revised_phi.get_formulas():
        if not entails(revised_psi.get_formulas(), f):
            print(f"  FAIL: {f} in B * phi but not entailed by B * psi")
            passed = False

    for f in revised_psi.get_formulas():
        if not entails(revised_phi.get_formulas(), f):
            print(f"  FAIL: {f} in B * psi but not entailed by B * phi")
            passed = False

    # Test 2: p | q  ≡  q | p
    phi2 = parse("p | q")
    psi2 = parse("q | p")

    bb2 = BeliefBase()
    bb2.add(parse("r"), 2)

    revised_phi2 = revision(bb2, phi2)
    revised_psi2 = revision(bb2, psi2)

    for f in revised_phi2.get_formulas():
        if not entails(revised_psi2.get_formulas(), f):
            print(f"  FAIL: {f} in B * (p|q) but not entailed by B * (q|p)")
            passed = False

    if passed:
        print("  PASS")
    return passed


def run_all_tests():
    """Run all AGM postulate tests."""
    print("=" * 60)
    print("AGM POSTULATE VERIFICATION")
    print("=" * 60)
    results = {
        "Success": test_success(),
        "Inclusion": test_inclusion(),
        "Vacuity": test_vacuity(),
        "Consistency": test_consistency(),
        "Extensionality": test_extensionality(),
    }
    print("=" * 60)
    print("RESULTS:")
    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    print("=" * 60)
    if all_passed:
        print("All AGM postulates verified successfully!")
    else:
        print("Some postulates failed. Check implementation.")
    return all_passed


if __name__ == "__main__":
    run_all_tests()
