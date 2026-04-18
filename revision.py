from __future__ import annotations

from itertools import combinations
from typing import Callable

from belief_base import BeliefBase
from logic import Formula, Neg, is_tautology
from resolution import entails as default_entails

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
    """Priority-guided partial meet contraction."""
    entails_fn = entails_fn or default_entails
    formulas = belief_base.formulas()

    if not entails_fn(formulas, phi):
        return belief_base.copy()
    if is_tautology(phi):
        return belief_base.copy()

    remainders = _find_remainders(belief_base.items(), phi, entails_fn)
    if not remainders:
        return BeliefBase()

    best = max(
        remainders,
        key=lambda remainder: (
            sum(priority for _, priority in remainder),
            len(remainder),
            tuple(sorted((priority, str(formula)) for formula, priority in remainder)),
        ),
    )

    result = BeliefBase()
    for formula, priority in best:
        result.add(formula, priority)
    return result


def revision(
    belief_base: BeliefBase,
    phi: Formula,
    priority: int = 1,
    entails_fn: EntailsFn | None = None,
) -> BeliefBase:
    """Levi identity: B * φ = (B ÷ ~φ) + φ."""
    contracted = contraction(belief_base, Neg(phi), entails_fn=entails_fn)
    return expansion(contracted, phi, priority)


def _find_remainders(
    beliefs: list[tuple[Formula, int]],
    phi: Formula,
    entails_fn: EntailsFn,
) -> list[list[tuple[Formula, int]]]:
    """Return all maximal subsets that do not entail phi."""
    n_beliefs = len(beliefs)
    non_entailing_indices: list[frozenset[int]] = []

    for size in range(n_beliefs + 1):
        for indices in combinations(range(n_beliefs), size):
            subset_formulas = [beliefs[index][0] for index in indices]
            if not entails_fn(subset_formulas, phi):
                non_entailing_indices.append(frozenset(indices))

    maximal_indices: list[frozenset[int]] = []
    for candidate in non_entailing_indices:
        if not any(candidate < other for other in non_entailing_indices):
            maximal_indices.append(candidate)

    maximal_indices.sort(key=lambda index_set: (-len(index_set), tuple(sorted(index_set))))

    return [
        [beliefs[index] for index in sorted(index_set)]
        for index_set in maximal_indices
    ]
