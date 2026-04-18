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
    """Priority-guided partial meet contraction.

    We compute all maximal remainders that do not entail ``phi``, keep the
    highest-ranked ones according to formula priorities, and return their
    intersection.
    """
    entails_fn = entails_fn or default_entails
    belief_items = belief_base.items()
    formulas = [formula for formula, _ in belief_items]

    if not entails_fn(formulas, phi):
        return belief_base.copy()
    if is_tautology(phi):
        return belief_base.copy()

    remainders = _find_remainders(belief_items, phi, entails_fn)
    if not remainders:
        return BeliefBase()

    scored_remainders = [(remainder, _priority_score(remainder)) for remainder in remainders]
    best_score = max(score for _, score in scored_remainders)
    selected_remainders = [remainder for remainder, score in scored_remainders if score == best_score]

    common_beliefs = set(selected_remainders[0])
    for remainder in selected_remainders[1:]:
        common_beliefs &= set(remainder)

    result = BeliefBase()
    for formula, belief_priority in belief_items:
        if (formula, belief_priority) in common_beliefs:
            result.add(formula, belief_priority)
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


def _priority_score(remainder: list[tuple[Formula, int]]) -> tuple[int, tuple[int, ...], int]:
    """Lexicographic score for selecting preferred remainders.

    Higher total priority wins first; ties are broken by stronger retained
    priorities, then by subset size.
    """
    priorities = sorted((priority for _, priority in remainder), reverse=True)
    return (sum(priorities), tuple(priorities), len(remainder))
