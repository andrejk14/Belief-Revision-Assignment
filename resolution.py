"""
Resolution-based logical entailment checking.
"""
from __future__ import annotations
from logic import Formula, Not, And, to_clauses, to_cnf


def entails(knowledge_base: list[Formula], query: Formula) -> bool:
    """
    Check if knowledge_base |= query using resolution.
    KB |= query iff KB ∪ {~query} is unsatisfiable.
    """
    # Collect all clauses from the KB
    clauses = set()
    for formula in knowledge_base:
        clauses |= to_clauses(formula)

    # Add negation of the query
    neg_query = Not(query)
    clauses |= to_clauses(neg_query)

    return _resolution_refutation(clauses)


def is_unsatisfiable(formulas: list[Formula]) -> bool:
    """Check if a set of formulas is unsatisfiable using resolution."""
    clauses = set()
    for f in formulas:
        clauses |= to_clauses(f)
    return _resolution_refutation(clauses)


def _resolution_refutation(clauses: set[frozenset[tuple[str, bool]]]) -> bool:
    """
    Apply resolution repeatedly.
    Returns True if the empty clause is derived (unsatisfiable).
    """
    clauses = set(clauses)
    # Remove tautological clauses (contain both p and ~p)
    clauses = {c for c in clauses if not _is_tautological_clause(c)}

    while True:
        new_clauses = set()
        clause_list = list(clauses)

        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                resolvents = _resolve(clause_list[i], clause_list[j])
                for resolvent in resolvents:
                    if len(resolvent) == 0:
                        return True  # Empty clause — unsatisfiable
                    if not _is_tautological_clause(resolvent):
                        new_clauses.add(resolvent)

        if new_clauses.issubset(clauses):
            return False  # No new clauses — satisfiable

        clauses |= new_clauses


def _resolve(c1: frozenset[tuple[str, bool]],
             c2: frozenset[tuple[str, bool]]) -> list[frozenset[tuple[str, bool]]]:
    """
    Resolve two clauses. Returns a list of resolvents.
    For each complementary literal pair, produce one resolvent.
    """
    resolvents = []
    for lit1 in c1:
        complement = (lit1[0], not lit1[1])
        if complement in c2:
            # Resolve on this literal
            new_clause = (c1 - {lit1}) | (c2 - {complement})
            resolvents.append(frozenset(new_clause))
    return resolvents


def _is_tautological_clause(clause: frozenset[tuple[str, bool]]) -> bool:
    """A clause is tautological if it contains both p and ~p."""
    atoms_pos = set()
    atoms_neg = set()
    for name, polarity in clause:
        if polarity:
            atoms_pos.add(name)
        else:
            atoms_neg.add(name)
    return bool(atoms_pos & atoms_neg)
