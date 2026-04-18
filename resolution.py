from __future__ import annotations

from itertools import combinations

from logic import Clause, Conj, Formula, Neg, is_satisfiable, is_tautology, to_clauses

CLAUSE_LIMIT = 50_000


def entails(knowledge_base: list[Formula], query: Formula) -> bool:
    """Resolution-based entailment with a semantic fallback for large clause sets."""
    clauses: set[Clause] = set()
    for formula in knowledge_base:
        clauses |= to_clauses(formula)
    clauses |= to_clauses(Neg(query))

    result = _resolve(clauses)
    if result is None:
        return _semantic_entails(knowledge_base, query)
    return result


def is_inconsistent(formulas: list[Formula]) -> bool:
    clauses: set[Clause] = set()
    for formula in formulas:
        clauses |= to_clauses(formula)

    result = _resolve(clauses)
    if result is None:
        return _semantic_inconsistent(formulas)
    return result


def _resolve(clauses: set[Clause]) -> bool | None:
    clauses = {clause for clause in clauses if not _is_tautological_clause(clause)}
    processed_pairs: set[tuple[Clause, Clause]] = set()

    while True:
        new_clauses: set[Clause] = set()
        clause_list = sorted(clauses, key=lambda clause: (len(clause), sorted(clause)))

        for first, second in combinations(clause_list, 2):
            pair = (first, second)
            if pair in processed_pairs:
                continue
            processed_pairs.add(pair)

            for resolvent in _resolve_pair(first, second):
                if not resolvent:
                    return True
                if not _is_tautological_clause(resolvent):
                    new_clauses.add(resolvent)

        if new_clauses <= clauses:
            return False

        clauses |= new_clauses
        if len(clauses) > CLAUSE_LIMIT:
            return None


def _resolve_pair(left: Clause, right: Clause) -> set[Clause]:
    resolvents: set[Clause] = set()
    for atom, polarity in left:
        complement = (atom, not polarity)
        if complement in right:
            merged = (left - {(atom, polarity)}) | (right - {complement})
            resolvents.add(frozenset(merged))
    return resolvents


def _is_tautological_clause(clause: Clause) -> bool:
    positive = {atom for atom, polarity in clause if polarity}
    negative = {atom for atom, polarity in clause if not polarity}
    return bool(positive & negative)


def _semantic_entails(knowledge_base: list[Formula], query: Formula) -> bool:
    if not knowledge_base:
        return is_tautology(query)
    conjunction = Conj(*knowledge_base)
    return not is_satisfiable(Conj(conjunction, Neg(query)))


def _semantic_inconsistent(formulas: list[Formula]) -> bool:
    if not formulas:
        return False
    return not is_satisfiable(Conj(*formulas))
