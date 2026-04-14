from logic import Formula, Neg, to_clauses

MAX_CLAUSES = 50000  # safety cap so we don't spin forever on big inputs

def entails(kb: list[Formula], query: Formula) -> bool:
    """Check KB |= query via refutation: KB ∪ {¬query} unsat?"""
    clauses = set()
    for f in kb:
        clauses |= to_clauses(f)
    clauses |= to_clauses(Neg(query))
    return _resolve(clauses)


def is_inconsistent(formulas: list[Formula]) -> bool:
    clauses = set()
    for f in formulas:
        clauses |= to_clauses(f)
    return _resolve(clauses)


def _resolve(clauses):
    clauses = {c for c in clauses if not _taut(c)}
    while True:
        new = set()
        cs = list(clauses)
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                for r in _resolve_pair(cs[i], cs[j]):
                    if len(r) == 0:
                        return True  # empty clause -> contradiction
                    if not _taut(r):
                        new.add(r)
        if new <= clauses:
            return False  # saturated
        clauses |= new
        if len(clauses) > MAX_CLAUSES:
            # can't prove it within budget, give up
            return False


def _resolve_pair(c1, c2):
    results = []
    for name, pol in c1:
        if (name, not pol) in c2:
            merged = (c1 - {(name, pol)}) | (c2 - {(name, not pol)})
            results.append(frozenset(merged))
    return results


def _taut(clause):
    """A clause with both p and ~p is trivially true."""
    pos = {n for n, p in clause if p}
    neg = {n for n, p in clause if not p}
    return bool(pos & neg)
