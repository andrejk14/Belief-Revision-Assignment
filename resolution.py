from __future__ import annotations
from itertools import combinations
from logic import Clause, Formula, Neg, to_clauses

def entails(kb: list[Formula], query: Formula) -> bool:
    clauses: set[Clause] = set()
    for f in kb:
        clauses |= to_clauses(f)
    clauses |= to_clauses(Neg(query))
    return _refutes(clauses)


def is_inconsistent(formulas: list[Formula]) -> bool:
    clauses: set[Clause] = set()
    for f in formulas:
        clauses |= to_clauses(f)
    return _refutes(clauses)


def _refutes(clauses: set[Clause]) -> bool:
    clauses = {c for c in clauses if not _tautological(c)}
    examined: set[tuple[Clause, Clause]] = set()

    while True:
        new: set[Clause] = set()
        ordered = sorted(clauses, key=lambda c: (len(c), sorted(c)))
        for a, b in combinations(ordered, 2):
            pair = (a, b)
            if pair in examined:
                continue
            examined.add(pair)
            for r in _resolve(a, b):
                if not r:
                    return True
                if not _tautological(r):
                    new.add(r)
        if new <= clauses:
            return False
        clauses |= new


def _resolve(a: Clause, b: Clause) -> set[Clause]:
    out: set[Clause] = set()
    for atom, polarity in a:
        complement = (atom, not polarity)
        if complement in b:
            out.add(frozenset((a - {(atom, polarity)}) | (b - {complement})))
    return out


def _tautological(clause: Clause) -> bool:
    positive = {atom for atom, p in clause if p}
    negative = {atom for atom, p in clause if not p}
    return bool(positive & negative)