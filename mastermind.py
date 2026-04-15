# mastermind.py - code-breaker AI using belief revision
# uses a semantic entailment check instead of resolution because
# the feedback formulas blow up when converted to CNF
from __future__ import annotations
from itertools import permutations
from logic import Atom, Neg, Conj, Disj
from belief_base import BeliefBase
from revision import revision, expansion

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
    whites = sum(min(gc.get(c, 0), sc.get(c, 0)) for c in set(gc) | set(sc))
    return blacks, whites


def _build_constraints():
    # one-hot encoding per position + each colour at most once
    fs = []
    # every position has at least one colour
    for i in range(N_POS):
        fs.append(Disj(*[_atom(i, j) for j in range(N_COL)]))
    # at most one colour per position
    for i in range(N_POS):
        for a in range(N_COL):
            for b in range(a + 1, N_COL):
                fs.append(Disj(Neg(_atom(i, a)), Neg(_atom(i, b))))
    # each colour in at most one position
    for j in range(N_COL):
        for a in range(N_POS):
            for b in range(a + 1, N_POS):
                fs.append(Disj(Neg(_atom(a, j)), Neg(_atom(b, j))))
    return fs


def _encode_feedback(guess, blacks, whites):
    # disjunction of all codes that match the given (blacks, whites) feedback
    matching = []
    for code in ALL_CODES:
        if _pegs(guess, code) == (blacks, whites):
            matching.append(Conj(*[_atom(i, code[i]) for i in range(N_POS)]))
    if not matching:
        raise ValueError("impossible feedback")
    if len(matching) == 1:
        return matching[0]
    return Disj(*matching)


def _mastermind_entails(formulas, query):
    # entailment by checking all 360 valid codes (resolution cant handle the big disjunctions)
    if not formulas:
        # query must hold in all 360 codes
        for code in ALL_CODES:
            v = _code_to_val(code)
            if not query.eval(v):
                return False
        return True
    for code in ALL_CODES:
        v = _code_to_val(code)
        if all(f.eval(v) for f in formulas):
            if not query.eval(v):
                return False
    return True


def _consistent_codes(bb):
    entries = bb.formulas()
    result = []
    for code in ALL_CODES:
        v = _code_to_val(code)
        if all(f.eval(v) for f in entries):
            result.append(code)
    return result


class Solver:
    def __init__(self):
        self.bb = BeliefBase()
        for f in _build_constraints():
            self.bb.add(f, 10)
        self.turn = 0
        self._code_cache = None

    def _codes(self):
        if self._code_cache is None:
            self._code_cache = _consistent_codes(self.bb)
        return self._code_cache

    def guess(self):
        codes = self._codes()
        if self.turn == 0:
            self.turn += 1
            return [0, 1, 2, 3]  # RGBY, good starting guess
        self.turn += 1
        if not codes:
            return [0, 1, 2, 3]
        if len(codes) <= 2:
            return codes[0]
        return self._pick_best(codes)

    def observe(self, guess, blacks, whites):
        fb = _encode_feedback(guess, blacks, whites)
        self.bb = revision(self.bb, fb, priority=5,
                           entails_fn=_mastermind_entails)
        self._code_cache = None

    def n_remaining(self):
        return len(self._codes())

    def _pick_best(self, codes):
        # minimax over a subset of candidates (checking all is too slow)
        best = codes[0]
        best_worst = len(codes)
        for g in codes[:50]:  # TODO: could try more but gets slow
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
