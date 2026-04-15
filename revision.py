from __future__ import annotations
from itertools import combinations
from logic import Formula, Neg, is_tautology
from resolution import entails
from belief_base import BeliefBase


def expansion(bb, phi, priority=1):
    result = bb.copy()
    result.add(phi, priority)
    return result


def contraction(bb, phi):
    beliefs = bb.items()
    formulas = [f for f, _ in beliefs]

    if not entails(formulas, phi):
        return bb.copy()
    if is_tautology(phi):
        return bb.copy()

    remainders = _find_remainders(beliefs, phi)
    if not remainders:
        return BeliefBase()

    # selection function: pick the remainder with highest total priority
    best = max(remainders, key=lambda r: sum(p for _, p in r))
    out = BeliefBase()
    for f, p in best:
        out.add(f, p)
    return out


def revision(bb, phi, priority=1):
    # Levi identity: B * phi = (B - ~phi) + phi
    contracted = contraction(bb, Neg(phi))
    return expansion(contracted, phi, priority)


def _find_remainders(beliefs, phi):
    # dropping k at a time: if no k-1 drop breaks entailment,
    # then any k-drop that does is automatically maximal
    n = len(beliefs)
    for k in range(1, n+1):
        found = []
        for dropped in combinations(range(n), k):
            keep = set(range(n)) - set(dropped)
            subset = [beliefs[i] for i in sorted(keep)]
            fs = [f for f, _ in subset]
            if not entails(fs, phi):
                found.append(subset)
        if found:
            return found
    return []
