from __future__ import annotations

from itertools import permutations

from belief_base import BeliefBase
from logic import Atom, Conj, Disj, Neg
from revision import revision

COLORS = ["R", "G", "B", "Y", "O", "P"]
N_POSITIONS = 4
N_COLORS = len(COLORS)
ALL_CODES = [list(code) for code in permutations(range(N_COLORS), N_POSITIONS)]


def _atom(position: int, color: int) -> Atom:
    return Atom(f"C{position}_{color}")


def _code_to_valuation(code: list[int]) -> dict[str, bool]:
    valuation: dict[str, bool] = {}
    for position in range(N_POSITIONS):
        for color in range(N_COLORS):
            valuation[f"C{position}_{color}"] = code[position] == color
    return valuation


def _score(guess: list[int], secret: list[int]) -> tuple[int, int]:
    black = sum(g == s for g, s in zip(guess, secret))
    guess_counts: dict[int, int] = {}
    secret_counts: dict[int, int] = {}

    for index in range(N_POSITIONS):
        if guess[index] != secret[index]:
            guess_counts[guess[index]] = guess_counts.get(guess[index], 0) + 1
            secret_counts[secret[index]] = secret_counts.get(secret[index], 0) + 1

    white = sum(min(guess_counts.get(color, 0), secret_counts.get(color, 0)) for color in set(guess_counts) | set(secret_counts))
    return black, white


def _background_knowledge():
    constraints = []

    for position in range(N_POSITIONS):
        constraints.append(Disj(*(_atom(position, color) for color in range(N_COLORS))))

    for position in range(N_POSITIONS):
        for left in range(N_COLORS):
            for right in range(left + 1, N_COLORS):
                constraints.append(Disj(Neg(_atom(position, left)), Neg(_atom(position, right))))

    for color in range(N_COLORS):
        for left in range(N_POSITIONS):
            for right in range(left + 1, N_POSITIONS):
                constraints.append(Disj(Neg(_atom(left, color)), Neg(_atom(right, color))))

    return constraints


def _encode_feedback(guess: list[int], black: int, white: int):
    matching_codes = []
    for code in ALL_CODES:
        if _score(guess, code) == (black, white):
            matching_codes.append(Conj(*(_atom(position, code[position]) for position in range(N_POSITIONS))))

    if not matching_codes:
        raise ValueError("Inconsistent feedback")
    if len(matching_codes) == 1:
        return matching_codes[0]
    return Disj(*matching_codes)


def _mastermind_entails(formulas, query):
    for code in ALL_CODES:
        valuation = _code_to_valuation(code)
        if all(formula.eval(valuation) for formula in formulas) and not query.eval(valuation):
            return False
    return True


def _consistent_codes(formulas):
    valid = []
    for code in ALL_CODES:
        valuation = _code_to_valuation(code)
        if all(formula.eval(valuation) for formula in formulas):
            valid.append(code)
    return valid


class Solver:
    def __init__(self) -> None:
        self.belief_base = BeliefBase()
        for formula in _background_knowledge():
            self.belief_base.add(formula, priority=10)
        self.turn = 0
        self._cache: list[list[int]] | None = None

    def _candidates(self) -> list[list[int]]:
        if self._cache is None:
            self._cache = _consistent_codes(self.belief_base.formulas())
        return self._cache

    def guess(self) -> list[int]:
        candidates = self._candidates()
        self.turn += 1

        if self.turn == 1:
            return [0, 1, 2, 3]
        if not candidates:
            return [0, 1, 2, 3]
        if len(candidates) <= 2:
            return candidates[0]
        return self._minimax_guess(candidates)

    def observe(self, guess: list[int], black: int, white: int) -> None:
        feedback = _encode_feedback(guess, black, white)
        self.belief_base = revision(
            self.belief_base,
            feedback,
            priority=5,
            entails_fn=_mastermind_entails,
        )
        self._cache = None

    def remaining(self) -> int:
        return len(self._candidates())

    def _minimax_guess(self, candidates: list[list[int]]) -> list[int]:
        best_guess = candidates[0]
        best_worst_case = len(candidates)

        for guess in candidates[:50]:
            buckets: dict[tuple[int, int], int] = {}
            for secret in candidates:
                outcome = _score(guess, secret)
                buckets[outcome] = buckets.get(outcome, 0) + 1
            worst_case = max(buckets.values())
            if worst_case < best_worst_case:
                best_worst_case = worst_case
                best_guess = guess
        return best_guess


def code_str(code: list[int]) -> str:
    return " ".join(COLORS[color] for color in code)


def play_auto(secret: list[int]) -> int:
    print(f"Secret: {code_str(secret)}")
    print("-" * 40)
    solver = Solver()

    for turn in range(1, 11):
        guess = solver.guess()
        black, white = _score(guess, secret)
        print(f"Turn {turn}: {code_str(guess)}  ->  {black}B {white}W   ({solver.remaining()} remaining)")
        if black == N_POSITIONS:
            print(f"Solved in {turn} turns.")
            return turn
        solver.observe(guess, black, white)

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
        guess = solver.guess()
        print(f"Guess {turn}: {code_str(guess)}   ({solver.remaining()} possibilities)")
        black = int(input("  Black pegs: "))
        white = int(input("  White pegs: "))
        if black == N_POSITIONS:
            print(f"Solved in {turn} turns.")
            return
        solver.observe(guess, black, white)

    print("Ran out of guesses.")


if __name__ == "__main__":
    import random
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        play_auto(random.sample(range(N_COLORS), N_POSITIONS))
    else:
        play_interactive()
