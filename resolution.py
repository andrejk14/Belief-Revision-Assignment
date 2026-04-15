from logic import Formula, Neg, Conj, to_clauses, is_satisfiable

CLAUSE_LIMIT = 50000


def entails(kb, query):
    # refutation: KB ∪ {¬query} unsatisfiable => KB |= query
    clauses = set()
    for f in kb:
        clauses |= to_clauses(f)
    clauses |= to_clauses(Neg(query))
    res = _resolve(clauses)
    if res is None:
        # resolution blew up, fall back to truth tables
        return _semantic_entails(kb, query)
    return res


def is_inconsistent(formulas):
    clauses = set()
    for f in formulas:
        clauses |= to_clauses(f)
    res = _resolve(clauses)
    if res is None:
        return _semantic_inconsistent(formulas)
    return res


def _resolve(clauses):
    clauses = {c for c in clauses if not _is_taut(c)}
    while True:
        new = set()
        clist = list(clauses)
        for i in range(len(clist)):
            for j in range(i + 1, len(clist)):
                resolvents = _resolve_pair(clist[i], clist[j])
                for r in resolvents:
                    if len(r) == 0:
                        return True
                    if not _is_taut(r):
                        new.add(r)
        if new <= clauses:
            return False
        clauses |= new
        # print(f"clauses: {len(clauses)}")
        if len(clauses) > CLAUSE_LIMIT:
            return None  # too many clauses, give up


def _resolve_pair(c1, c2):
    out = []
    for (name, pol) in c1:
        if (name, not pol) in c2:
            merged = (c1 - {(name, pol)}) | (c2 - {(name, not pol)})
            out.append(frozenset(merged))
    return out


def _is_taut(clause):
    pos = {n for n, p in clause if p}
    neg = {n for n, p in clause if not p}
    return bool(pos & neg)


def _semantic_entails(kb, query):
    if not kb:
        from logic import is_tautology
        return is_tautology(query)
    conj = kb[0]
    for f in kb[1:]:
        conj = Conj(conj, f)
    return not is_satisfiable(Conj(conj, Neg(query)))


def _semantic_inconsistent(formulas):
    if not formulas:
        return False
    conj = formulas[0]
    for f in formulas[1:]:
        conj = Conj(conj, f)
    return not is_satisfiable(conj)
