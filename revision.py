from __future__ import annotations

from collections.abc import Callable
from itertools import combinations

from belief_base import BeliefBase
from logic import Formula, Neg
from resolution import entails as resolution_entails

WeightedBelief = tuple[Formula, int]
Remainder = list[WeightedBelief]
EntailsFn = Callable[[list[Formula], Formula], bool]


def expansion(base: BeliefBase, phi: Formula, priority: int = 1) -> BeliefBase:
    out = base.copy()
    out.add(phi, priority)
    return out


def contraction(
    base: BeliefBase,
    phi: Formula,
    entails_fn: EntailsFn | None = None,
) -> BeliefBase:
    entails_fn = entails_fn or resolution_entails
    items = base.items()
    formulas = [f for f, _ in items]

    # Tautologies cannot be contracted out; also, if phi is not entailed at all,
    # there is nothing to remove. Both are identity cases.
    if entails_fn([], phi) or not entails_fn(formulas, phi):
        return base.copy()

    remainders = _remainders(items, phi, entails_fn)
    preferred = _select(remainders)

    kept = set(preferred[0])
    for r in preferred[1:]:
        kept.intersection_update(r)
    return _rebuild(items, kept)


def revision(
    base: BeliefBase,
    phi: Formula,
    priority: int = 1,
    entails_fn: EntailsFn | None = None,
) -> BeliefBase:
    return expansion(contraction(base, Neg(phi), entails_fn=entails_fn), phi, priority)


def _remainders(
    beliefs: list[WeightedBelief],
    phi: Formula,
    entails_fn: EntailsFn,
) -> list[Remainder]:
    n = len(beliefs)
    maximal: list[frozenset[int]] = []

    for size in range(n, -1, -1):
        for idx in combinations(range(n), size):
            cand = frozenset(idx)
            if any(cand < m for m in maximal):
                continue
            subset = [beliefs[i][0] for i in idx]
            if entails_fn(subset, phi):
                continue
            maximal.append(cand)

    return [[beliefs[i] for i in sorted(s)] for s in maximal]


def _select(remainders: list[Remainder]) -> list[Remainder]:
    profiled = [(r, _profile(r)) for r in remainders]
    best = max(p for _, p in profiled)
    return [r for r, p in profiled if p == best]


def _profile(r: Remainder) -> tuple[int, ...]:
    return tuple(sorted((p for _, p in r), reverse=True))


def _rebuild(items: list[WeightedBelief], kept: set[WeightedBelief]) -> BeliefBase:
    out = BeliefBase()
    for formula, priority in items:
        if (formula, priority) in kept:
            out.add(formula, priority)
    return out