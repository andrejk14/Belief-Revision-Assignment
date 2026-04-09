"""
AGM belief revision operations: expansion, contraction, and revision.
"""
from __future__ import annotations
from itertools import combinations
from logic import Formula, Not, And, is_tautology
from resolution import entails
from belief_base import BeliefBase


def expansion(bb: BeliefBase, formula: Formula, priority: int = 1) -> BeliefBase:
    """
    Expansion: B + phi
    Simply add phi to the belief base.
    """
    result = bb.copy()
    result.add(formula, priority)
    return result


def contraction(bb: BeliefBase, formula: Formula) -> BeliefBase:
    """
    Partial meet contraction: B ÷ phi
    1. Find all remainder sets (maximal subsets of B that don't entail phi)
    2. Select the best remainder sets using priority-based selection function
    3. Return the intersection of the selected remainder sets
    """
    beliefs = bb.get_beliefs_with_priority()
    formulas = [f for f, p in beliefs]

    # If the belief base doesn't entail phi, no contraction needed
    if not entails(formulas, formula):
        return bb.copy()

    # If phi is a tautology, it can't be contracted
    if is_tautology(formula):
        return bb.copy()

    # Find remainder sets: maximal subsets that don't entail phi
    remainder_sets = _find_remainder_sets(beliefs, formula)

    if not remainder_sets:
        # No remainder sets found — return empty belief base
        return BeliefBase()

    # Selection function: pick remainder sets with highest total priority
    selected = _selection_function(remainder_sets)

    # Intersection of selected remainder sets
    result = BeliefBase()
    common = set.intersection(*[set(rs) for rs in selected])
    for f, p in common:
        result.add(f, p)

    return result


def revision(bb: BeliefBase, formula: Formula, priority: int = 1) -> BeliefBase:
    """
    Revision: B * phi (Levi identity)
    B * phi = (B ÷ ~phi) + phi
    First contract by ~phi, then expand by phi.
    """
    # Contract by the negation of the formula
    contracted = contraction(bb, Not(formula))
    # Expand by the formula
    return expansion(contracted, formula, priority)


def _find_remainder_sets(beliefs: list[tuple[Formula, int]],
                         formula: Formula) -> list[list[tuple[Formula, int]]]:
    """
    Find all remainder sets: maximal subsets of beliefs that don't entail formula.
    A subset S is a remainder set if:
    1. S doesn't entail formula
    2. For any belief b not in S, S ∪ {b} entails formula
    """
    n = len(beliefs)

    # Try subsets from largest to smallest
    remainder_sets = []

    # Start with size n-1 down to 0
    for size in range(n - 1, -1, -1):
        if remainder_sets:
            # We already found maximal subsets — stop looking at smaller ones
            break
        for combo in combinations(range(n), size):
            subset = [beliefs[i] for i in combo]
            subset_formulas = [f for f, p in subset]

            if not entails(subset_formulas, formula):
                # Check maximality: adding any missing belief should make it entail phi
                is_maximal = True
                missing_indices = set(range(n)) - set(combo)
                for idx in missing_indices:
                    extended = subset_formulas + [beliefs[idx][0]]
                    if not entails(extended, formula):
                        is_maximal = False
                        break

                if is_maximal:
                    remainder_sets.append(subset)

    return remainder_sets


def _selection_function(remainder_sets: list[list[tuple[Formula, int]]]) -> list[list[tuple[Formula, int]]]:
    """
    Selection function based on priority ordering.
    Select the remainder set(s) with the highest total priority score.
    This prefers keeping more entrenched (higher priority) beliefs.
    """
    if not remainder_sets:
        return remainder_sets

    def score(rs):
        return sum(p for _, p in rs)

    max_score = max(score(rs) for rs in remainder_sets)
    return [rs for rs in remainder_sets if score(rs) == max_score]
