# Code-breaker AI for Mastermind using belief revision.
# 6 colors, 4 positions, no duplicates.
#
# The feedback formulas (big disjunctions over matching codes) blow up
# badly if you try to convert them to CNF for resolution. So we keep
# the general BeliefBase structure and priority-based contraction, but
# check satisfiability by direct evaluation over the 360 valid codes.
# This is essentially the same Levi-identity revision, just with a
# domain-specific entailment oracle.

from __future__ import annotations
from itertools import permutations
from logic import Formula, Atom, Neg, Conj, Disj
from belief_base import BeliefBase

COLORS = ["R", "G", "B", "Y", "O", "P"]
N_POS = 4
N_COL = len(COLORS)
ALL_CODES = [list(p) for p in permutations(range(N_COL), N_POS)]


def _atom(pos, col):
    return Atom(f"C{pos}_{col}")


def _code_to_valuation(code):
    v = {}
    for i in range(N_POS):
        for j in range(N_COL):
            v[f"C{i}_{j}"] = (code[i] == j)
    return v


def _pegs(guess, secret):
    blacks = sum(g == s for g, s in zip(guess, secret))
    g_extra, s_extra = {}, {}
    for i in range(N_POS):
        if guess[i] != secret[i]:
            g_extra[guess[i]] = g_extra.get(guess[i], 0) + 1
            s_extra[secret[i]] = s_extra.get(secret[i], 0) + 1
    whites = sum(min(g_extra.get(c, 0), s_extra.get(c, 0))
                 for c in set(g_extra) | set(s_extra))
    return blacks, whites


def _build_constraints():
    """Background knowledge: exactly one color per position, each color used at most once."""
    fs = []
    for i in range(N_POS):
        # at least one color in each position
        fs.append(Disj(*[_atom(i, j) for j in range(N_COL)]))
    # at most one color per position
    for i in range(N_POS):
        for j in range(N_COL):
            for k in range(j + 1, N_COL):
                fs.append(Disj(Neg(_atom(i, j)), Neg(_atom(i, k))))
    # each color in at most one position
    for j in range(N_COL):
        for i in range(N_POS):
            for k in range(i + 1, N_POS):
                fs.append(Disj(Neg(_atom(i, j)), Neg(_atom(k, j))))
    return fs


def _encode_feedback(guess, blacks, whites):
    """Build a formula that is true exactly for codes consistent with this feedback."""
    matching = []
    for code in ALL_CODES:
        if _pegs(guess, code) == (blacks, whites):
            matching.append(Conj(*[_atom(i, code[i]) for i in range(N_POS)]))
    if not matching:
        raise ValueError("feedback is impossible")
    return matching[0] if len(matching) == 1 else Disj(*matching)


def _sem_consistent(entries):
    """Check if there's at least one valid code satisfying all formulas."""
    for code in ALL_CODES:
        v = _code_to_valuation(code)
        if all(f.eval(v) for f, _ in entries):
            return True
    return False


class MastermindBB:
    """
    Wraps a BeliefBase but uses semantic evaluation over the code space
    instead of resolution (which would choke on the feedback formulas).
    Revision still follows the Levi identity with priority-based contraction.
    """
    def __init__(self):
        self.bb = BeliefBase()
        self._cache = None

    def _invalidate(self):
        self._cache = None

    def consistent_codes(self):
        if self._cache is not None:
            return self._cache
        entries = self.bb.items()
        result = []
        for code in ALL_CODES:
            v = _code_to_valuation(code)
            if all(f.eval(v) for f, _ in entries):
                result.append(code)
        self._cache = result
        return result

    def expand(self, formula, priority):
        self.bb.add(formula, priority)
        self._invalidate()

    def revise(self, formula, priority):
        """
        Levi-style: try adding phi. If inconsistent, drop beliefs
        starting from lowest priority until it works again.
        """
        test = self.bb.items() + [(formula, priority)]
        if _sem_consistent(test):
            self.expand(formula, priority)
            return

        # contract: remove lowest-priority beliefs until consistent
        remaining = list(self.bb.items())
        for f, p in sorted(self.bb.items(), key=lambda x: x[1]):
            remaining.remove((f, p))
            if _sem_consistent(remaining + [(formula, priority)]):
                break

        self.bb = BeliefBase()
        for f, p in remaining:
            self.bb.add(f, p)
        self.expand(formula, priority)


class Solver:
    def __init__(self):
        self.bb = MastermindBB()
        for f in _build_constraints():
            self.bb.expand(f, 10)  # high priority: rules of the game
        self.turn = 0

    def guess(self):
        codes = self.bb.consistent_codes()
        if self.turn == 0:
            self.turn += 1
            return [0, 1, 2, 3]  # fixed first guess
        self.turn += 1
        if not codes:
            return [0, 1, 2, 3]  # fallback (shouldn't happen)
        if len(codes) <= 2:
            return codes[0]
        return self._minimax(codes)

    def observe(self, guess, blacks, whites):
        feedback = _encode_feedback(guess, blacks, whites)
        self.bb.revise(feedback, priority=5)

    def n_remaining(self):
        return len(self.bb.consistent_codes())

    def _minimax(self, codes):
        """Pick guess that minimizes worst-case remaining possibilities."""
        best, best_worst = codes[0], len(codes)
        # only check first 50 candidates to keep it fast
        for g in codes[:50]:
            buckets = {}
            for s in codes:
                key = _pegs(g, s)
                buckets[key] = buckets.get(key, 0) + 1
            worst = max(buckets.values())
            if worst < best_worst:
                best_worst = worst
                best = g
        return best


def code_str(code):
    return " ".join(COLORS[c] for c in code)


def play_auto(secret):
    print(f"Secret: {code_str(secret)}")
    print("-" * 40)
    solver = Solver()
    for t in range(10):
        g = solver.guess()
        b, w = _pegs(g, secret)
        rem = solver.n_remaining()
        print(f"  Turn {t+1}: {code_str(g)}  =>  {b}B {w}W   ({rem} remaining)")
        if b == N_POS:
            print(f"Solved in {t+1} turns.")
            return t + 1
        solver.observe(g, b, w)
    print("Failed to solve in 10 turns.")
    return -1


def play_interactive():
    print("=" * 40)
    print("MASTERMIND (I'm the code-breaker)")
    print("=" * 40)
    print(f"Colors: {', '.join(COLORS)}")
    print(f"{N_POS} positions, no repeats.\n")
    print("Pick a secret code, I'll try to guess it.\n")

    solver = Solver()
    for t in range(10):
        g = solver.guess()
        rem = solver.n_remaining()
        print(f"Guess {t+1}: {code_str(g)}   ({rem} possibilities)")
        b = int(input("  Black pegs? "))
        w = int(input("  White pegs? "))
        if b == N_POS:
            print(f"\nCracked it in {t+1}!")
            return
        solver.observe(g, b, w)
    print("Ran out of guesses :(")


if __name__ == "__main__":
    import sys, random
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        play_auto(random.sample(range(N_COL), N_POS))
    else:
        play_interactive()
