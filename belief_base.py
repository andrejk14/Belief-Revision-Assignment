from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from logic import Formula


@dataclass(frozen=True)
class BeliefEntry:
    formula: Formula
    priority: int


class BeliefBase:
    """Finite belief base with integer priorities."""

    def __init__(self) -> None:
        self._entries: list[BeliefEntry] = []

    def add(self, formula: Formula, priority: int = 1) -> None:
        for index, entry in enumerate(self._entries):
            if entry.formula == formula:
                self._entries[index] = BeliefEntry(formula, priority)
                return
        self._entries.append(BeliefEntry(formula, priority))

    def remove(self, formula: Formula) -> None:
        self._entries = [entry for entry in self._entries if entry.formula != formula]

    def formulas(self) -> list[Formula]:
        return [entry.formula for entry in self._entries]

    def items(self) -> list[tuple[Formula, int]]:
        return [(entry.formula, entry.priority) for entry in self._entries]

    def copy(self) -> BeliefBase:
        clone = BeliefBase()
        clone._entries = list(self._entries)
        return clone

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, formula: object) -> bool:
        return any(entry.formula == formula for entry in self._entries)

    def __iter__(self) -> Iterator[tuple[Formula, int]]:
        for entry in self._entries:
            yield entry.formula, entry.priority

    def __str__(self) -> str:
        if not self._entries:
            return "BeliefBase(empty)"
        ordered = sorted(self._entries, key=lambda entry: (-entry.priority, str(entry.formula)))
        body = "\n".join(f"  [{entry.priority}] {entry.formula}" for entry in ordered)
        return f"BeliefBase:\n{body}"

    def __repr__(self) -> str:
        return str(self)
