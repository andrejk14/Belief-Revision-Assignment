from __future__ import annotations

from collections.abc import Callable
from itertools import combinations

from belief_base import BeliefBase
from logic import Formula, Neg, is_tautology
from resolution import entails as default_entails

WeightedBelief = tuple[Formula, int]
Remainder = list[WeightedBelief]
EntailsFn = Callable[[list[Formula], Formula], bool]


def expansion(belief_base: BeliefBase, phi: Formula, priority: int = 1) -> BeliefBase:
    result = belief_base.copy()
    result.add(phi, priority)
    return result


def contraction(
    belief_base: BeliefBase,
    phi: Formula,
    entails_fn: EntailsFn | None = None,
) -> BeliefBase:
    entails_fn = entails_fn or default_entails
    belief_items = belief_base.items()
    formulas = [formula for formula, _ in belief_items]

    if is_tautology(phi):
        return belief_base.copy()
    if not entails_fn(formulas, phi):
        return belief_base.copy()

    remainders = _maximal_non_entailing_subsets(belief_items, phi, entails_fn)
    if not remainders:
        return BeliefBase()

    preferred_remainders = _preferred_remainders(remainders)
    retained_beliefs = _intersect_remainders(preferred_remainders)
    return _build_belief_base(belief_items, retained_beliefs)


def revision(
    belief_base: BeliefBase,
    phi: Formula,
    priority: int = 1,
    entails_fn: EntailsFn | None = None,
) -> BeliefBase:
    contracted = contraction(belief_base, Neg(phi), entails_fn=entails_fn)
    return expansion(contracted, phi, priority)


def _maximal_non_entailing_subsets(
    beliefs: list[WeightedBelief],
    phi: Formula,
    entails_fn: EntailsFn,
) -> list[Remainder]:
    maximal_indices: list[frozenset[int]] = []

    for size in range(len(beliefs) + 1):
        for indices in combinations(range(len(beliefs)), size):
            candidate = frozenset(indices)

            if any(candidate < other for other in maximal_indices):
                continue

            subset_formulas = [beliefs[index][0] for index in indices]
            if entails_fn(subset_formulas, phi):
                continue

            maximal_indices = [other for other in maximal_indices if not other < candidate]
            maximal_indices.append(candidate)

    maximal_indices.sort(key=lambda index_set: (-len(index_set), tuple(sorted(index_set))))
    return [[beliefs[index] for index in sorted(index_set)] for index_set in maximal_indices]


def _preferred_remainders(remainders: list[Remainder]) -> list[Remainder]:
    profiled_remainders = [(remainder, _priority_profile(remainder)) for remainder in remainders]
    best_profile = max(profile for _, profile in profiled_remainders)
    return [remainder for remainder, profile in profiled_remainders if profile == best_profile]


def _intersect_remainders(remainders: list[Remainder]) -> set[WeightedBelief]:
    shared_beliefs = set(remainders[0])
    for remainder in remainders[1:]:
        shared_beliefs.intersection_update(remainder)
    return shared_beliefs


def _build_belief_base(
    belief_items: list[WeightedBelief],
    retained_beliefs: set[WeightedBelief],
) -> BeliefBase:
    result = BeliefBase()
    for formula, priority in belief_items:
        if (formula, priority) in retained_beliefs:
            result.add(formula, priority)
    return result


def _priority_profile(remainder: Remainder) -> tuple[int, ...]:
    return tuple(sorted((priority for _, priority in remainder), reverse=True))
