"""
Mastermind game solver using belief revision.

Standard Mastermind: 4 positions, 6 colors, no duplicate colors.
Colors: R(ed), G(reen), B(lue), Y(ellow), O(range), P(urple)

Propositional encoding:
  Variable C_i_j means "position i has color j" (i=0..3, j=0..5)

Background knowledge:
  - Each position has exactly one color
  - Each color is used at most once (no duplicates)

Feedback encoding:
  - Black peg: correct color in correct position
  - White peg: correct color in wrong position

The solver maintains a belief base of propositional formulas encoding the
game constraints and feedback. Belief revision is performed by:
  1. Encoding each feedback as a propositional constraint
  2. Revising the belief base with the new constraint
  3. Extracting consistent possible worlds (codes) via model evaluation

For efficiency in this finite domain (360 possible codes), entailment
is checked via direct model evaluation rather than resolution, which is
sound and complete for finite propositional domains.
"""
from __future__ import annotations
from itertools import permutations
from logic import Formula, Atom, Not, And, Or

COLORS = ["R", "G", "B", "Y", "O", "P"]
NUM_POSITIONS = 4
NUM_COLORS = len(COLORS)
ALL_CODES = [list(p) for p in permutations(range(NUM_COLORS), NUM_POSITIONS)]


def var(pos: int, color: int) -> str:
    """Variable name for position pos having color color."""
    return f"C{pos}{color}"


def var_formula(pos: int, color: int) -> Atom:
    """Atom for position pos having color color."""
    return Atom(var(pos, color))


def code_to_valuation(code: list[int]) -> dict[str, bool]:
    """Convert a code to a truth-value assignment over C_i_j variables."""
    val = {}
    for i in range(NUM_POSITIONS):
        for j in range(NUM_COLORS):
            val[var(i, j)] = (code[i] == j)
    return val


# ── Background knowledge ─────────────────────────────────────────────────────

def generate_background_knowledge() -> list[Formula]:
    """Generate the background rules of Mastermind as propositional formulas."""
    formulas = []

    # Each position has at least one color
    for i in range(NUM_POSITIONS):
        formulas.append(Or(*[var_formula(i, j) for j in range(NUM_COLORS)]))

    # Each position has at most one color
    for i in range(NUM_POSITIONS):
        for j in range(NUM_COLORS):
            for k in range(j + 1, NUM_COLORS):
                formulas.append(Or(Not(var_formula(i, j)), Not(var_formula(i, k))))

    # Each color used at most once
    for j in range(NUM_COLORS):
        for i in range(NUM_POSITIONS):
            for k in range(i + 1, NUM_POSITIONS):
                formulas.append(Or(Not(var_formula(i, j)), Not(var_formula(k, j))))

    return formulas


# ── Feedback ──────────────────────────────────────────────────────────────────

def compute_feedback(guess: list[int], secret: list[int]) -> tuple[int, int]:
    """Compute Mastermind feedback: (black_pegs, white_pegs)."""
    blacks = sum(1 for i in range(NUM_POSITIONS) if guess[i] == secret[i])
    guess_colors, secret_colors = {}, {}
    for i in range(NUM_POSITIONS):
        if guess[i] != secret[i]:
            guess_colors[guess[i]] = guess_colors.get(guess[i], 0) + 1
            secret_colors[secret[i]] = secret_colors.get(secret[i], 0) + 1
    whites = sum(min(guess_colors.get(c, 0), secret_colors.get(c, 0))
                 for c in set(guess_colors) | set(secret_colors))
    return blacks, whites


def encode_feedback(guess: list[int], blacks: int, whites: int) -> Formula:
    """
    Encode feedback as a propositional formula.
    The formula is a disjunction of all codes consistent with the feedback.
    """
    consistent = [code for code in ALL_CODES
                  if compute_feedback(guess, code) == (blacks, whites)]

    code_formulas = []
    for code in consistent:
        code_formulas.append(And(*[var_formula(i, code[i]) for i in range(NUM_POSITIONS)]))

    if len(code_formulas) == 1:
        return code_formulas[0]
    return Or(*code_formulas)


# ── Belief-revision-based solver ──────────────────────────────────────────────

class MastermindBeliefBase:
    """
    Belief base for Mastermind using propositional formulas.

    Stores formulas with priorities. Uses direct model evaluation over the
    finite set of 360 possible codes to determine consistency, which is
    equivalent to resolution-based entailment for this domain.

    Revision follows the AGM framework:
      - Expansion: add new formula
      - Contraction: remove formulas that conflict (keep higher priority)
      - Revision via Levi identity: contract by ~phi, then expand by phi
    """

    def __init__(self):
        self.formulas: list[tuple[Formula, int]] = []  # (formula, priority)
        self._consistent_codes: list[list[int]] | None = None

    def _invalidate_cache(self):
        self._consistent_codes = None

    def get_consistent_codes(self) -> list[list[int]]:
        """Find all codes satisfying all formulas in the belief base."""
        if self._consistent_codes is not None:
            return self._consistent_codes

        consistent = []
        for code in ALL_CODES:
            val = code_to_valuation(code)
            if all(f.evaluate(val) for f, _ in self.formulas):
                consistent.append(code)

        self._consistent_codes = consistent
        return consistent

    def entails(self, formula: Formula) -> bool:
        """Check if the belief base entails formula (true in all consistent models)."""
        for code in self.get_consistent_codes():
            val = code_to_valuation(code)
            if not formula.evaluate(val):
                return False
        return True

    def expand(self, formula: Formula, priority: int):
        """Expansion: simply add formula to the belief base."""
        self.formulas.append((formula, priority))
        self._invalidate_cache()

    def revise(self, formula: Formula, priority: int):
        """
        AGM revision via Levi identity: B * phi = (B ÷ ~phi) + phi

        Contract by ~phi: remove lowest-priority formulas that conflict with phi
        until adding phi is consistent. Then expand by phi.
        """
        # Check if phi is already consistent with current beliefs
        test_formulas = self.formulas + [(formula, priority)]
        if self._is_consistent(test_formulas):
            # No contraction needed — just expand
            self.expand(formula, priority)
            return

        # Contraction: remove lowest-priority formulas until consistent
        # Sort by priority ascending (remove least entrenched first)
        sorted_beliefs = sorted(self.formulas, key=lambda x: x[1])
        remaining = list(self.formulas)

        for f, p in sorted_beliefs:
            remaining.remove((f, p))
            test = remaining + [(formula, priority)]
            if self._is_consistent(test):
                break

        self.formulas = remaining
        self.expand(formula, priority)

    def _is_consistent(self, formulas: list[tuple[Formula, int]]) -> bool:
        """Check if a set of formulas is jointly satisfiable."""
        for code in ALL_CODES:
            val = code_to_valuation(code)
            if all(f.evaluate(val) for f, _ in formulas):
                return True
        return False

    def get_formulas_display(self) -> list[str]:
        """Return string representations of stored formulas (for display)."""
        return [f"[{p}] {f}" for f, p in sorted(self.formulas, key=lambda x: -x[1])]


class MastermindSolver:
    """Mastermind code-breaker using belief revision."""

    def __init__(self):
        self.bb = MastermindBeliefBase()
        self.guess_number = 0

        # Add background knowledge with high priority
        for f in generate_background_knowledge():
            self.bb.expand(f, priority=10)

    def make_guess(self) -> list[int]:
        """Generate the next guess based on current beliefs."""
        consistent = self.bb.get_consistent_codes()

        if self.guess_number == 0:
            self.guess_number += 1
            return [0, 1, 2, 3]  # Fixed opening: R G B Y

        self.guess_number += 1
        if consistent:
            # Pick the code that minimizes worst-case remaining possibilities
            if len(consistent) <= 2:
                return consistent[0]
            return self._best_guess(consistent)
        return [0, 1, 2, 3]

    def _best_guess(self, consistent: list[list[int]]) -> list[int]:
        """Pick guess using minimax strategy: minimize worst-case remaining codes."""
        best_guess = consistent[0]
        best_worst = len(consistent)

        # Only evaluate consistent codes as guesses (good enough, much faster)
        for guess in consistent[:50]:  # Limit search for speed
            # Count how many codes remain for each possible feedback
            feedback_groups: dict[tuple[int, int], int] = {}
            for secret in consistent:
                fb = compute_feedback(guess, secret)
                feedback_groups[fb] = feedback_groups.get(fb, 0) + 1

            worst = max(feedback_groups.values())
            if worst < best_worst:
                best_worst = worst
                best_guess = guess

        return best_guess

    def process_feedback(self, guess: list[int], blacks: int, whites: int):
        """Revise beliefs based on feedback."""
        feedback_formula = encode_feedback(guess, blacks, whites)
        self.bb.revise(feedback_formula, priority=5)

    def get_remaining_possibilities(self) -> int:
        """Count how many codes are still consistent."""
        return len(self.bb.get_consistent_codes())


def code_to_str(code: list[int]) -> str:
    """Convert a code to a readable string."""
    return " ".join(COLORS[c] for c in code)


def str_to_code(s: str) -> list[int]:
    """Convert a string like 'R G B Y' to a code."""
    color_map = {c: i for i, c in enumerate(COLORS)}
    return [color_map[c.strip().upper()] for c in s.split()]


def play_interactive():
    """Play Mastermind interactively. The human sets the code, AI guesses."""
    print("=" * 60)
    print("MASTERMIND - Belief Revision Code Breaker")
    print("=" * 60)
    print(f"Colors: {', '.join(f'{c}({COLORS[i]})' for i, c in enumerate(['Red', 'Green', 'Blue', 'Yellow', 'Orange', 'Purple']))}")
    print(f"Code: {NUM_POSITIONS} positions, no duplicate colors")
    print()
    print("Think of a secret code. I'll try to guess it!")
    print("After each guess, tell me:")
    print("  - Black pegs (correct color AND position)")
    print("  - White pegs (correct color, WRONG position)")
    print()

    solver = MastermindSolver()
    max_guesses = 10

    for turn in range(max_guesses):
        guess = solver.make_guess()
        remaining = solver.get_remaining_possibilities()

        print(f"Guess {turn + 1}: {code_to_str(guess)}  ({remaining} possibilities remain)")

        blacks = int(input("  Black pegs: "))
        whites = int(input("  White pegs: "))

        if blacks == NUM_POSITIONS:
            print(f"\nI cracked the code in {turn + 1} guesses!")
            return

        solver.process_feedback(guess, blacks, whites)

    print("\nI couldn't crack the code in time. Something went wrong!")


def play_auto(secret: list[int]):
    """Auto-play: solver guesses against a known secret code."""
    print(f"Secret code: {code_to_str(secret)}")
    print("-" * 40)

    solver = MastermindSolver()
    max_guesses = 10

    for turn in range(max_guesses):
        guess = solver.make_guess()
        blacks, whites = compute_feedback(guess, secret)
        remaining = solver.get_remaining_possibilities()

        print(f"Guess {turn + 1}: {code_to_str(guess)}  -> {blacks}B {whites}W  ({remaining} possibilities)")

        if blacks == NUM_POSITIONS:
            print(f"Cracked in {turn + 1} guesses!")
            return turn + 1

        solver.process_feedback(guess, blacks, whites)

    print("Failed to crack the code!")
    return -1


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        import random
        secret = random.sample(range(NUM_COLORS), NUM_POSITIONS)
        play_auto(secret)
    else:
        play_interactive()
