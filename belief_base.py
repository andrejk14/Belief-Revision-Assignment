from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator
from logic import Formula


@dataclass(frozen=True)
class BeliefEntry:
    formula: Formula
    priority: int


class BeliefBase:
    def __init__(self) -> None:
        self._entries: list[BeliefEntry] = []

    def add(self, formula: Formula, priority: int = 1) -> None:
        for i, e in enumerate(self._entries):
            if e.formula == formula:
                self._entries[i] = BeliefEntry(formula, priority)
                return
        self._entries.append(BeliefEntry(formula, priority))

    def remove(self, formula: Formula) -> None:
        self._entries = [e for e in self._entries if e.formula != formula]

    def formulas(self) -> list[Formula]:
        return [e.formula for e in self._entries]

    def items(self) -> list[tuple[Formula, int]]:
        return [(e.formula, e.priority) for e in self._entries]

    def copy(self) -> BeliefBase:
        clone = BeliefBase()
        clone._entries = list(self._entries)
        return clone

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, formula: object) -> bool:
        return any(e.formula == formula for e in self._entries)

    def __iter__(self) -> Iterator[tuple[Formula, int]]:
        for e in self._entries:
            yield e.formula, e.priority

    def __str__(self) -> str:
        if not self._entries:
            return "BeliefBase(empty)"
        ordered = sorted(self._entries, key=lambda e: (-e.priority, str(e.formula)))
        body = "\n".join(f"  [{e.priority}] {e.formula}" for e in ordered)
        return f"BeliefBase:\n{body}"

    def __repr__(self) -> str:
        return str(self)