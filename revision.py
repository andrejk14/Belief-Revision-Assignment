# AGM revision via the Levi identity.
# Contraction is partial meet, using priority as the selection function.
from __future__ import annotations
from itertools import combinations
from logic import Formula, Neg, is_tautology
from resolution import entails
from belief_base import BeliefBase


def expansion(bb: BeliefBase, phi: Formula, priority: int = 1) -> BeliefBase:
    out = bb.copy()
    out.add(phi, priority)
    return out


def contraction(bb: BeliefBase, phi: Formula) -> BeliefBase:
    """
    Partial meet contraction: find all maximal subsets of bb that
    don't entail phi, then pick the one with highest total priority.
    """
    beliefs = bb.items()
    flist = [f for f, _ in beliefs]

    if not entails(flist, phi):
        return bb.copy()
    if is_tautology(phi):
        return bb.copy()  # can't contract tautologies (AGM recovery)

    remainders = _find_remainders(beliefs, phi)
    if not remainders:
        # everything entails phi no matter what -- shouldn't happen for
        # non-tautologies, but just in case
        return BeliefBase()

    # selection function: take the remainder with the best total priority
    best = max(remainders, key=lambda r: sum(p for _, p in r))
    out = BeliefBase()
    for f, p in best:
        out.add(f, p)
    return out


def revision(bb: BeliefBase, phi: Formula, priority: int = 1) -> BeliefBase:
    """Levi identity: B * phi = (B - ~phi) + phi"""
    contracted = contraction(bb, Neg(phi))
    return expansion(contracted, phi, priority)


def _find_remainders(beliefs, phi):
    """
    Compute all remainder sets: maximal subsets of beliefs that don't entail phi.

    We collect every subset that (a) does not entail phi, and (b) is maximal,
    meaning adding back any single removed belief would make it entail phi again.
    """
    n = len(beliefs)
    remainders = []

    # try removing k beliefs at a time, k = 1, 2, ..., n
    for k in range(1, n + 1):
        for dropped in combinations(range(n), k):
            drop_set = set(dropped)
            subset = [beliefs[i] for i in range(n) if i not in drop_set]
            sub_formulas = [f for f, _ in subset]

            if entails(sub_formulas, phi):
                continue

            # maximality check: adding back any ONE dropped belief must
            # restore entailment, otherwise a larger subset also works
            maximal = True
            for d in dropped:
                if not entails(sub_formulas + [beliefs[d][0]], phi):
                    maximal = False
                    break

            if maximal:
                remainders.append(subset)

    return remainders
