from __future__ import annotations
from itertools import permutations
from logic import Atom, Neg, Conj, Disj
from belief_base import BeliefBase

COLORS = ["R", "G", "B", "Y", "O", "P"]
N_POS  = 4
N_COL  = len(COLORS)
ALL_CODES = [list(p) for p in permutations(range(N_COL), N_POS)]


def _atom(pos, col):
    return Atom(f"C{pos}_{col}")

def _code_to_val(code):
    v = {}
    for i in range(N_POS):
        for j in range(N_COL):
            v[f"C{i}_{j}"] = (code[i] == j)
    return v

def _pegs(guess, secret):
    blacks = sum(g == s for g, s in zip(guess, secret))
    gc, sc = {}, {}
    for i in range(N_POS):
        if guess[i] != secret[i]:
            gc[guess[i]] = gc.get(guess[i], 0) + 1
            sc[secret[i]] = sc.get(secret[i], 0) + 1
    whites = sum(min(gc.get(c,0), sc.get(c,0)) for c in set(gc)|set(sc))
    return blacks, whites


def _build_constraints():
    """One-hot per position + each color at most once."""
    fs = []
    for i in range(N_POS):
        fs.append(Disj(*[_atom(i,j) for j in range(N_COL)]))
    for i in range(N_POS):
        for a in range(N_COL):
            for b in range(a+1, N_COL):
                fs.append(Disj(Neg(_atom(i,a)), Neg(_atom(i,b))))
    for j in range(N_COL):
        for a in range(N_POS):
            for b in range(a+1, N_POS):
                fs.append(Disj(Neg(_atom(a,j)), Neg(_atom(b,j))))
    return fs


def _encode_feedback(guess, blacks, whites):
    matching = []
    for code in ALL_CODES:
        if _pegs(guess, code) == (blacks, whites):
            matching.append(Conj(*[_atom(i, code[i]) for i in range(N_POS)]))
    if not matching:
        raise ValueError("impossible feedback")
    if len(matching) == 1:
        return matching[0]
    return Disj(*matching)


def _sem_consistent(entries):
    """Check if any valid code satisfies all formulas."""
    for code in ALL_CODES:
        v = _code_to_val(code)
        if all(f.eval(v) for f, _ in entries):
            return True
    return False


class MastermindBB:
    """
    Uses direct evaluation over the 360 valid codes instead of resolution,
    because the feedback disjunctions blow up in CNF. Still follows the
    Levi identity structure: try expansion, contract if inconsistent.
    """
    def __init__(self):
        self.bb = BeliefBase()
        self._cache = None

    def _clear_cache(self):
        self._cache = None

    def consistent_codes(self):
        if self._cache is not None:
            return self._cache
        entries = self.bb.items()
        res = []
        for code in ALL_CODES:
            v = _code_to_val(code)
            if all(f.eval(v) for f, _ in entries):
                res.append(code)
        self._cache = res
        return res

    def expand(self, formula, priority):
        self.bb.add(formula, priority)
        self._clear_cache()

    def revise(self, formula, priority):
        test_entries = self.bb.items() + [(formula, priority)]
        if _sem_consistent(test_entries):
            self.expand(formula, priority)
            return

        # drop lowest priority first until consistent again
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
            self.bb.expand(f, 10)
        self.turn = 0

    def guess(self):
        codes = self.bb.consistent_codes()
        if self.turn == 0:
            self.turn += 1
            return [0,1,2,3]
        self.turn += 1
        if not codes:
            return [0,1,2,3]
        if len(codes) <= 2:
            return codes[0]
        return self._pick_best(codes)

    def observe(self, guess, blacks, whites):
        fb = _encode_feedback(guess, blacks, whites)
        self.bb.revise(fb, priority=5)

    def n_remaining(self):
        return len(self.bb.consistent_codes())

    def _pick_best(self, codes):
        best = codes[0]
        best_worst = len(codes)
        # minimax over a subset to keep it fast
        for g in codes[:50]:
            buckets = {}
            for s in codes:
                key = _pegs(g, s)
                buckets[key] = buckets.get(key, 0) + 1
            w = max(buckets.values())
            if w < best_worst:
                best_worst = w
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
    print("MASTERMIND")
    print("=" * 40)
    print(f"Colors: {', '.join(COLORS)}")
    print(f"{N_POS} positions, no repeats.")
    print("Pick a secret code.\n")

    solver = Solver()
    for t in range(10):
        g = solver.guess()
        rem = solver.n_remaining()
        print(f"Guess {t+1}: {code_str(g)}   ({rem} possibilities)")
        b = int(input("  Black pegs? "))
        w = int(input("  White pegs? "))
        if b == N_POS:
            print(f"\nGot it in {t+1}!")
            return
        solver.observe(g, b, w)
    print("Ran out of guesses.")


if __name__ == "__main__":
    import sys, random
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        play_auto(random.sample(range(N_COL), N_POS))
    else:
        play_interactive()
