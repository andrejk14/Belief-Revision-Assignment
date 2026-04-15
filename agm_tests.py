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


def _is_consistent(formulas):
    if not formulas:
        return True
    c = formulas[0]
    for f in formulas[1:]:
        c = Conj(c, f)
    return is_satisfiable(c)


def _logically_equiv(fs1, fs2):
    # check if two sets of formulas have the same logical closure
    for f in fs1:
        if not entails(fs2, f):
            return False
    for f in fs2:
        if not entails(fs1, f):
            return False
    return True


def test_success():
    print("Testing success postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)

    r = revision(bb, parse("r"))
    _check("success-1", entails(r.formulas(), parse("r")),
           "r not entailed after revising by r")

    r2 = revision(bb, parse("~p"))
    _check("success-2", entails(r2.formulas(), parse("~p")),
           "~p not entailed after revising by ~p")

    r3 = revision(bb, parse("p & r"))
    _check("success-3", entails(r3.formulas(), parse("p & r")),
           "p&r not entailed after revising by p&r")

    # empty base
    empty = BeliefBase()
    r4 = revision(empty, parse("a"))
    _check("success-empty", entails(r4.formulas(), parse("a")),
           "a not entailed after revising empty base")


# ---- (K*2) Inclusion: B*phi <= Cn(B+phi) ----

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

    # with actual conflict
    bb2 = BeliefBase()
    bb2.add(parse("p"), 2)
    bb2.add(parse("p >> q"), 1)

    rev2 = revision(bb2, parse("~q"))
    exp2 = expansion(bb2, parse("~q"))
    for f in rev2.formulas():
        _check("incl-2", entails(exp2.formulas(), f),
               f"{f} in B*phi but not entailed by B+phi")


def test_vacuity():
    print("Testing vacuity postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)
    phi = parse("r")

    assert not entails(bb.formulas(), Neg(phi)), "precondition broken"

    rev = revision(bb, phi)
    exp = expansion(bb, phi)
    _check("vacuity-1", _logically_equiv(rev.formulas(), exp.formulas()),
           "B*phi and B+phi not logically equivalent")

    # also try with a more complex phi
    bb2 = BeliefBase()
    bb2.add(parse("a"), 2)
    phi2 = parse("b | c")
    assert not entails(bb2.formulas(), Neg(phi2))

    rev2 = revision(bb2, phi2)
    exp2 = expansion(bb2, phi2)
    _check("vacuity-2", _logically_equiv(rev2.formulas(), exp2.formulas()),
           "B*phi and B+phi not equiv for b|c")


def test_consistency():
    print("Testing consistency postulate...")

    bb = BeliefBase()
    bb.add(parse("p"), 2)
    bb.add(parse("q"), 1)

    r = revision(bb, parse("~p"))
    _check("consist-1", _is_consistent(r.formulas()),
           "B*~p is inconsistent")

    # longer implication chain
    bb2 = BeliefBase()
    bb2.add(parse("p"), 3)
    bb2.add(parse("p >> q"), 2)
    bb2.add(parse("q >> r"), 1)

    r2 = revision(bb2, parse("~r"))
    _check("consist-2", _is_consistent(r2.formulas()),
           "B*~r is inconsistent")

    # single belief
    bb3 = BeliefBase()
    bb3.add(parse("a"), 1)
    r3 = revision(bb3, parse("~a"))
    _check("consist-3", _is_consistent(r3.formulas()),
           "B*~a inconsistent on single-element base")


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
    _check("ext-1", _logically_equiv(r1.formulas(), r2.formulas()),
           "B*(~~r) != B*r")

    # p|q <=> q|p
    bb2 = BeliefBase()
    bb2.add(parse("r"), 2)
    ra = revision(bb2, parse("p | q"))
    rb = revision(bb2, parse("q | p"))
    _check("ext-2", _logically_equiv(ra.formulas(), rb.formulas()),
           "B*(p|q) != B*(q|p)")


def run_all():
    global _passed, _failed
    _passed = 0
    _failed = 0

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
