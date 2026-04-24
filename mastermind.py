"""Mastermind solver driven by the belief revision engine.

The solver reuses `revision.revision` unchanged but passes a custom
entailment oracle (`_feedback_entails`) instead of the resolution engine.
The oracle is semantic: it enumerates the finite domain of legal codes
(6 colours, 4 positions, no repeats = 360 codes) and checks whether every
code consistent with the background theory plus the current feedback also
satisfies the query. This is strictly faster than resolution for this
encoding (~24 atoms, tens to ~96 clauses) because model enumeration is
linear in the number of codes while resolution-refutation can be worst-case
exponential in the clause set.

The main belief revision machinery is untouched; this module exercises
that the engine accepts pluggable entailment (the `entails_fn` parameter
on `revision`).
"""
from __future__ import annotations

from itertools import permutations

from belief_base import BeliefBase
from logic import Atom, Conj, Disj, Formula, Neg
from revision import revision

COLORS = ["R", "G", "B", "Y", "O", "P"]
N_POSITIONS = 4
N_COLORS = len(COLORS)
ALL_CODES = [list(code) for code in permutations(range(N_COLORS), N_POSITIONS)]


def _atom(position: int, color: int) -> Atom:
    return Atom(f"C{position}_{color}")


def _code_to_valuation(code: list[int]) -> dict[str, bool]:
    v: dict[str, bool] = {}
    for position in range(N_POSITIONS):
        for color in range(N_COLORS):
            v[f"C{position}_{color}"] = code[position] == color
    return v


def _score(guess: list[int], secret: list[int]) -> tuple[int, int]:
    black = sum(g == s for g, s in zip(guess, secret))
    guess_counts: dict[int, int] = {}
    secret_counts: dict[int, int] = {}
    for i in range(N_POSITIONS):
        if guess[i] != secret[i]:
            guess_counts[guess[i]] = guess_counts.get(guess[i], 0) + 1
            secret_counts[secret[i]] = secret_counts.get(secret[i], 0) + 1
    white = sum(
        min(guess_counts.get(c, 0), secret_counts.get(c, 0))
        for c in set(guess_counts) | set(secret_counts)
    )
    return black, white


def _background_knowledge() -> list[Disj]:
    out: list[Disj] = []
    for position in range(N_POSITIONS):
        out.append(Disj(*(_atom(position, c) for c in range(N_COLORS))))
    for position in range(N_POSITIONS):
        for c1 in range(N_COLORS):
            for c2 in range(c1 + 1, N_COLORS):
                out.append(Disj(Neg(_atom(position, c1)), Neg(_atom(position, c2))))
    for color in range(N_COLORS):
        for p1 in range(N_POSITIONS):
            for p2 in range(p1 + 1, N_POSITIONS):
                out.append(Disj(Neg(_atom(p1, color)), Neg(_atom(p2, color))))
    return out


def _encode_feedback(guess: list[int], black: int, white: int) -> Formula:
    matching = [
        Conj(*(_atom(p, code[p]) for p in range(N_POSITIONS)))
        for code in ALL_CODES
        if _score(guess, code) == (black, white)
    ]
    if not matching:
        raise ValueError("Inconsistent feedback")
    return matching[0] if len(matching) == 1 else Disj(*matching)


def _consistent_codes(formulas: list[Formula]) -> list[list[int]]:
    return [
        code for code in ALL_CODES
        if all(f.eval(_code_to_valuation(code)) for f in formulas)
    ]


class Solver:
    BACKGROUND_PRIORITY = 10 # game rules: inviolable
    FEEDBACK_PRIORITY = 5 # feedback: trusted but in principle revisable

    def __init__(self) -> None:
        self._background = BeliefBase()
        for f in _background_knowledge():
            self._background.add(f, self.BACKGROUND_PRIORITY)
        self._feedback = BeliefBase()
        self.belief_base = self._background.copy()
        self.turn = 0
        self._cache: list[list[int]] | None = None

    def _rebuild(self) -> None:
        combined = self._background.copy()
        for f, p in self._feedback:
            combined.add(f, p)
        self.belief_base = combined
        self._cache = None

    def _candidates(self) -> list[list[int]]:
        if self._cache is None:
            self._cache = _consistent_codes(self.belief_base.formulas())
        return self._cache

    def _feedback_entails(self, formulas: list[Formula], query: Formula) -> bool:
        candidates = _consistent_codes(self._background.formulas() + formulas)
        if not candidates:
            return False
        return all(query.eval(_code_to_valuation(c)) for c in candidates)

    def guess(self) -> list[int]:
        self.turn += 1
        candidates = self._candidates()
        if not candidates:
            raise ValueError("Belief base is inconsistent")
        if self.turn == 1:
            return [0, 1, 2, 3]
        if len(candidates) <= 2:
            return candidates[0]
        return self._minimax_guess(candidates)

    def observe(self, guess: list[int], black: int, white: int) -> None:
        feedback = _encode_feedback(guess, black, white)
        self._feedback = revision(
            self._feedback,
            feedback,
            priority=self.FEEDBACK_PRIORITY,
            entails_fn=self._feedback_entails,
        )
        if not _consistent_codes(self._background.formulas() + self._feedback.formulas()):
            raise ValueError("Inconsistent feedback")
        self._rebuild()

    def remaining(self) -> int:
        return len(self._candidates())

    def _minimax_guess(self, candidates: list[list[int]]) -> list[int]:
        best = candidates[0]
        best_worst = len(candidates)
        for g in candidates:
            buckets: dict[tuple[int, int], int] = {}
            for s in candidates:
                outcome = _score(g, s)
                buckets[outcome] = buckets.get(outcome, 0) + 1
            worst = max(buckets.values())
            if worst < best_worst:
                best_worst = worst
                best = g
        return best


def code_str(code: list[int]) -> str:
    return " ".join(COLORS[c] for c in code)


def play_auto(secret: list[int]) -> int:
    print(f"Secret: {code_str(secret)}")
    print("-" * 40)
    solver = Solver()
    for turn in range(1, 11):
        g = solver.guess()
        black, white = _score(g, secret)
        if black == N_POSITIONS:
            print(f"Turn {turn}: {code_str(g)}  ->  {black}B {white}W   (1 remaining)")
            print(f"Solved in {turn} turns.")
            return turn
        solver.observe(g, black, white)
        print(f"Turn {turn}: {code_str(g)}  ->  {black}B {white}W   ({solver.remaining()} remaining)")
    print("Failed to solve in 10 turns.")
    return -1


def play_interactive() -> None:
    print("=" * 40)
    print("MASTERMIND")
    print("=" * 40)
    print(f"Colors: {', '.join(COLORS)}")
    print(f"{N_POSITIONS} positions, no repeated colors.")
    solver = Solver()
    for turn in range(1, 11):
        g = solver.guess()
        print(f"Guess {turn}: {code_str(g)}   ({solver.remaining()} possibilities)")
        black = int(input("  Black pegs: "))
        white = int(input("  White pegs: "))
        if black == N_POSITIONS:
            print(f"Solved in {turn} turns.")
            return
        solver.observe(g, black, white)
    print("Ran out of guesses.")


if __name__ == "__main__":
    import random
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        play_auto(random.sample(range(N_COLORS), N_POSITIONS))
    else:
        play_interactive()