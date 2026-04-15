from __future__ import annotations
from itertools import combinations
from logic import Formula, Neg, is_tautology
from resolution import entails as default_entails
from belief_base import BeliefBase


def expansion(bb, phi, priority=1):
    result = bb.copy()
    result.add(phi, priority)
    return result


def contraction(bb, phi, entails_fn=None):
    # partial meet contraction with priority-based selection
    if entails_fn is None:
        entails_fn = default_entails

    beliefs = bb.items()
    formulas = [f for f, _ in beliefs]

    if not entails_fn(formulas, phi):
        return bb.copy()
    if is_tautology(phi):
        return bb.copy()  # cant contract a tautology

    remainders = _find_remainders(beliefs, phi, entails_fn)
    if not remainders:
        return BeliefBase()

    # pick the remainder that keeps the most important beliefs
    best = max(remainders, key=lambda r: sum(p for _, p in r))
    out = BeliefBase()
    for f, p in best:
        out.add(f, p)
    return out


def revision(bb, phi, priority=1, entails_fn=None):
    # Levi identity: B * phi = (B ÷ ~phi) + phi
    contracted = contraction(bb, Neg(phi), entails_fn=entails_fn)
    return expansion(contracted, phi, priority)


def _find_remainders(beliefs, phi, entails_fn):
    # try dropping k beliefs at a time, starting from k=1
    # first k that breaks entailment gives the maximal remainders
    n = len(beliefs)
    for k in range(1, n + 1):
        found = []
        for dropped in combinations(range(n), k):
            keep = set(range(n)) - set(dropped)
            subset = [beliefs[i] for i in sorted(keep)]
            fs = [f for f, _ in subset]
            if not entails_fn(fs, phi):
                found.append(subset)
        if found:
            return found
    return []
