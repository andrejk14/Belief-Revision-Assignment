from __future__ import annotations
from logic import Formula


class BeliefBase:
    def __init__(self):
        self._entries: list[tuple[Formula, int]] = []

    def add(self, formula: Formula, priority: int = 1):
        for f, _ in self._entries:
            if f == formula:
                return
        self._entries.append((formula, priority))

    def remove(self, formula):
        self._entries = [(f, p) for f, p in self._entries if f != formula]

    def formulas(self):
        return [f for f, _ in self._entries]

    def items(self):
        return list(self._entries)

    def copy(self) -> BeliefBase:
        bb = BeliefBase()
        bb._entries = list(self._entries)
        return bb

    def clear(self):
        self._entries.clear()

    def __len__(self):
        return len(self._entries)

    def __contains__(self, formula):
        return any(f == formula for f, _ in self._entries)

    def __iter__(self):
        return iter(self._entries)

    def __str__(self):
        if not self._entries:
            return "BeliefBase(empty)"
        rows = sorted(self._entries, key=lambda x: -x[1])
        lines = [f"  [{p}] {f}" for f, p in rows]
        return "BeliefBase:\n" + "\n".join(lines)

    def __repr__(self):
        return str(self)
