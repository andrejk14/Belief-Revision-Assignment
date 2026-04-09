"""
Belief base with priority ordering on formulas.
"""
from __future__ import annotations
from logic import Formula


class BeliefBase:
    """
    A belief base stores propositional formulas with associated priorities.
    Higher priority = more entrenched (harder to remove during contraction).
    """

    def __init__(self):
        self._beliefs: list[tuple[Formula, int]] = []

    def add(self, formula: Formula, priority: int = 1):
        """Add a formula with a given priority."""
        # Avoid duplicates
        for f, p in self._beliefs:
            if f == formula:
                return
        self._beliefs.append((formula, priority))

    def remove(self, formula: Formula):
        """Remove a formula from the belief base."""
        self._beliefs = [(f, p) for f, p in self._beliefs if f != formula]

    def get_formulas(self) -> list[Formula]:
        """Return all formulas in the belief base."""
        return [f for f, p in self._beliefs]

    def get_beliefs_with_priority(self) -> list[tuple[Formula, int]]:
        """Return all (formula, priority) pairs."""
        return list(self._beliefs)

    def get_priority(self, formula: Formula) -> int:
        """Get the priority of a formula."""
        for f, p in self._beliefs:
            if f == formula:
                return p
        return 0

    def clear(self):
        """Remove all beliefs."""
        self._beliefs = []

    def copy(self) -> BeliefBase:
        """Return a deep copy of this belief base."""
        bb = BeliefBase()
        bb._beliefs = list(self._beliefs)
        return bb

    def __len__(self):
        return len(self._beliefs)

    def __contains__(self, formula: Formula):
        return any(f == formula for f, _ in self._beliefs)

    def __str__(self):
        if not self._beliefs:
            return "BeliefBase(empty)"
        lines = []
        for f, p in sorted(self._beliefs, key=lambda x: -x[1]):
            lines.append(f"  [{p}] {f}")
        return "BeliefBase:\n" + "\n".join(lines)

    def __repr__(self):
        return str(self)
