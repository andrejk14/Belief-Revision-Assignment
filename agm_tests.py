# agm_tests.py
# Tests for the five AGM postulates: success, inclusion, vacuity,
# consistency, extensionality.
# Run: python3 agm_tests.py

from logic import parse, Neg, Conj, Bicond, is_tautology, is_satisfiable
from resolution import entails
from belief_base import BeliefBase
from revision import expansion, contraction, revision

_passed = 0
_failed = 0

def _check(tag, cond, msg=""):
    global _passed, _failed
    if cond:
        _passed += 1
    else:
        _failed += 1
        print(f"  FAIL [{tag}]: {msg}")


# (K*1) Success: phi should be in B*phi
def test_success():
    print("Testing success postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)

    r1 = revision(bb, parse("r"))
    _check("success-r", entails(r1.formulas(), parse("r")),
           "r not entailed after revising by r")

    # revise by negation of existing belief
    r2 = revision(bb, parse("~p"))
    _check("success-~p", entails(r2.formulas(), parse("~p")),
           "~p not entailed after revising by ~p")

    r3 = revision(bb, parse("p & r"))
    _check("success-p&r", entails(r3.formulas(), parse("p & r")),
           "p&r not entailed after revising by p&r")


# (K*2) Inclusion: B*phi ⊆ Cn(B+phi)
def test_inclusion():
    print("Testing inclusion postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)
    phi = parse("r")

    rev = revision(bb, phi)
    exp = expansion(bb, phi)
    for f in rev.formulas():
        _check("incl-1", entails(exp.formulas(), f),
               f"{f} in B*phi but not entailed by B+phi")

    # case with actual conflict
    bb2 = BeliefBase()
    bb2.add(parse("p"), 2)
    bb2.add(parse("p >> q"), 1)

    rev2 = revision(bb2, parse("~q"))
    exp2 = expansion(bb2, parse("~q"))
    for f in rev2.formulas():
        _check("incl-2", entails(exp2.formulas(), f),
               f"{f} in B*phi but not entailed by B+phi")


# (K*3) Vacuity: if ~phi not in B, then B*phi = B+phi
def test_vacuity():
    print("Testing vacuity postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)
    phi = parse("r")

    # ~r shouldn't be entailed, so vacuity should apply
    assert not entails(bb.formulas(), Neg(phi)), "bad test setup"

    rev = revision(bb, phi)
    exp = expansion(bb, phi)

    rev_s = set(str(f) for f in rev.formulas())
    exp_s = set(str(f) for f in exp.formulas())
    _check("vacuity", rev_s == exp_s,
           f"B*phi != B+phi  (rev={rev_s}, exp={exp_s})")


# (K*4) Consistency: B*phi is consistent (when phi is satisfiable)
def test_consistency():
    print("Testing consistency postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)

    r = revision(bb, parse("~p"))
    fs = r.formulas()
    if fs:
        conjoined = fs[0]
        for f in fs[1:]:
            conjoined = Conj(conjoined, f)
        _check("consist-1", is_satisfiable(conjoined),
               "B*~p is inconsistent")

    # longer chain
    bb2 = BeliefBase()
    bb2.add(parse("p"), 3)
    bb2.add(parse("p >> q"), 2)
    bb2.add(parse("q >> r"), 1)
    r2 = revision(bb2, parse("~r"))
    fs2 = r2.formulas()
    if fs2:
        conjoined2 = fs2[0]
        for f in fs2[1:]:
            conjoined2 = Conj(conjoined2, f)
        _check("consist-2", is_satisfiable(conjoined2),
               "B*~r is inconsistent")


# (K*5) Extensionality: if phi <=> psi is a tautology, then B*phi = B*psi
def test_extensionality():
    print("Testing extensionality postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)

    # ~~r <=> r
    phi = parse("~~r")
    psi = parse("r")
    assert is_tautology(Bicond(phi, psi))

    r1 = revision(bb, phi)
    r2 = revision(bb, psi)
    for f in r1.formulas():
        _check("ext-1a", entails(r2.formulas(), f),
               f"{f} in B*phi but not in B*psi")
    for f in r2.formulas():
        _check("ext-1b", entails(r1.formulas(), f),
               f"{f} in B*psi but not in B*phi")

    # p|q vs q|p
    bb2 = BeliefBase()
    bb2.add(parse("r"), 2)
    ra = revision(bb2, parse("p | q"))
    rb = revision(bb2, parse("q | p"))
    for f in ra.formulas():
        _check("ext-2", entails(rb.formulas(), f),
               "p|q vs q|p mismatch")


def run_all():
    global _passed, _failed
    _passed, _failed = 0, 0

    print("=" * 50)
    print("AGM postulate tests")
    print("=" * 50)

    test_success()
    test_inclusion()
    test_vacuity()
    test_consistency()
    test_extensionality()

    print("-" * 50)
    total = _passed + _failed
    print(f"{_passed}/{total} checks passed.")
    if _failed:
        print(f"{_failed} FAILED.")
    else:
        print("All checks passed.")
    print("=" * 50)
    return _failed == 0


if __name__ == "__main__":
    run_all()
