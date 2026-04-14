"""
Propositional logic: formula AST, recursive-descent parser,
CNF conversion, clause extraction, and a few semantic helpers.
"""
from __future__ import annotations
import re
from typing import Set, Dict


class Formula:
    def atoms(self) -> Set[str]:
        raise NotImplementedError
    def eval(self, v: Dict[str, bool]) -> bool:
        raise NotImplementedError
    def __eq__(self, other):
        return type(self) is type(other) and str(self) == str(other)
    def __hash__(self):
        return hash(str(self))
    def __repr__(self):
        return str(self)


class Atom(Formula):
    def __init__(self, name: str):
        self.name = name
    def atoms(self):
        return {self.name}
    def eval(self, v):
        return v[self.name]
    def __str__(self):
        return self.name


class Neg(Formula):
    def __init__(self, inner: Formula):
        self.inner = inner
    def atoms(self):
        return self.inner.atoms()
    def eval(self, v):
        return not self.inner.eval(v)
    def __str__(self):
        if isinstance(self.inner, Atom):
            return f"~{self.inner}"
        return f"~({self.inner})"


class Conj(Formula):
    def __init__(self, *parts: Formula):
        self.parts = list(parts)
    def atoms(self):
        s = set()
        for p in self.parts:
            s |= p.atoms()
        return s
    def eval(self, v):
        return all(p.eval(v) for p in self.parts)
    def __str__(self):
        bits = []
        for p in self.parts:
            s = str(p)
            if isinstance(p, (Disj, Impl, Bicond)):
                s = f"({s})"
            bits.append(s)
        return " & ".join(bits)


class Disj(Formula):
    def __init__(self, *parts: Formula):
        self.parts = list(parts)
    def atoms(self):
        s = set()
        for p in self.parts:
            s |= p.atoms()
        return s
    def eval(self, v):
        return any(p.eval(v) for p in self.parts)
    def __str__(self):
        bits = []
        for p in self.parts:
            s = str(p)
            if isinstance(p, (Conj, Impl, Bicond)):
                s = f"({s})"
            bits.append(s)
        return " | ".join(bits)


class Impl(Formula):
    def __init__(self, lhs: Formula, rhs: Formula):
        self.lhs, self.rhs = lhs, rhs
    def atoms(self):
        return self.lhs.atoms() | self.rhs.atoms()
    def eval(self, v):
        return (not self.lhs.eval(v)) or self.rhs.eval(v)
    def __str__(self):
        return f"{self.lhs} >> {self.rhs}"


class Bicond(Formula):
    def __init__(self, lhs: Formula, rhs: Formula):
        self.lhs, self.rhs = lhs, rhs
    def atoms(self):
        return self.lhs.atoms() | self.rhs.atoms()
    def eval(self, v):
        return self.lhs.eval(v) == self.rhs.eval(v)
    def __str__(self):
        return f"{self.lhs} <> {self.rhs}"


# parser
# precedence (low to high): <>, >>, |, &, ~

_TOK = re.compile(r"\s*(~|&|\||\(|\)|>>|<>|[a-zA-Z_]\w*)\s*")

def parse(text: str) -> Formula:
    toks = _TOK.findall(text)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None
    def eat():
        t = toks[pos[0]]; pos[0] += 1; return t
    def expect(t):
        got = eat()
        if got != t:
            raise SyntaxError(f"expected '{t}', got '{got}'")

    def bicond():
        left = impl()
        while peek() == "<>":
            eat(); left = Bicond(left, impl())
        return left

    def impl():
        left = disj()
        while peek() == ">>":
            eat(); left = Impl(left, disj())
        return left

    def disj():
        parts = [conj()]
        while peek() == "|":
            eat(); parts.append(conj())
        return parts[0] if len(parts) == 1 else Disj(*parts)

    def conj():
        parts = [unary()]
        while peek() == "&":
            eat(); parts.append(unary())
        return parts[0] if len(parts) == 1 else Conj(*parts)

    def unary():
        if peek() == "~":
            eat(); return Neg(unary())
        if peek() == "(":
            eat(); node = bicond(); expect(")"); return node
        tok = peek()
        if tok is None:
            raise SyntaxError("unexpected end of input")
        return Atom(eat())

    result = bicond()
    if peek() is not None:
        raise SyntaxError(f"trailing token: {peek()}")
    return result


# CNF conversion

def to_cnf(f: Formula) -> Formula:
    f = _elim_bicond(f)
    f = _elim_impl(f)
    f = _push_neg(f)
    f = _distribute(f)
    return _flatten(f)

def _elim_bicond(f):
    if isinstance(f, Atom): return f
    if isinstance(f, Neg): return Neg(_elim_bicond(f.inner))
    if isinstance(f, Conj): return Conj(*[_elim_bicond(p) for p in f.parts])
    if isinstance(f, Disj): return Disj(*[_elim_bicond(p) for p in f.parts])
    if isinstance(f, Impl): return Impl(_elim_bicond(f.lhs), _elim_bicond(f.rhs))
    if isinstance(f, Bicond):
        a, b = _elim_bicond(f.lhs), _elim_bicond(f.rhs)
        return Conj(Impl(a, b), Impl(b, a))
    return f

def _elim_impl(f):
    if isinstance(f, Atom): return f
    if isinstance(f, Neg): return Neg(_elim_impl(f.inner))
    if isinstance(f, Conj): return Conj(*[_elim_impl(p) for p in f.parts])
    if isinstance(f, Disj): return Disj(*[_elim_impl(p) for p in f.parts])
    if isinstance(f, Impl):
        return Disj(Neg(_elim_impl(f.lhs)), _elim_impl(f.rhs))
    return f

def _push_neg(f):
    if isinstance(f, Atom): return f
    if isinstance(f, Neg):
        inner = f.inner
        if isinstance(inner, Neg):  return _push_neg(inner.inner)
        if isinstance(inner, Conj): return Disj(*[_push_neg(Neg(p)) for p in inner.parts])
        if isinstance(inner, Disj): return Conj(*[_push_neg(Neg(p)) for p in inner.parts])
        if isinstance(inner, Atom): return f
        return Neg(_push_neg(inner))
    if isinstance(f, Conj): return Conj(*[_push_neg(p) for p in f.parts])
    if isinstance(f, Disj): return Disj(*[_push_neg(p) for p in f.parts])
    return f

def _distribute(f):
    """Push disjunctions inside conjunctions to get CNF."""
    if isinstance(f, (Atom, Neg)): return f
    if isinstance(f, Conj):
        return Conj(*[_distribute(p) for p in f.parts])
    if isinstance(f, Disj):
        parts = [_distribute(p) for p in f.parts]
        for i, p in enumerate(parts):
            if isinstance(p, Conj):
                rest = parts[:i] + parts[i+1:]
                return Conj(*[_distribute(Disj(c, *rest)) for c in p.parts])
        return Disj(*parts)
    return f

def _flatten(f):
    if isinstance(f, (Atom, Neg)): return f
    if isinstance(f, Conj):
        out = []
        for p in f.parts:
            p = _flatten(p)
            if isinstance(p, Conj): out.extend(p.parts)
            else: out.append(p)
        return out[0] if len(out) == 1 else Conj(*out)
    if isinstance(f, Disj):
        out = []
        for p in f.parts:
            p = _flatten(p)
            if isinstance(p, Disj): out.extend(p.parts)
            else: out.append(p)
        return out[0] if len(out) == 1 else Disj(*out)
    return f


# clause extraction for resolution

def to_clauses(formula: Formula):
    """Returns set of frozensets, each frozenset = {(atom, polarity), ...}"""
    cnf = to_cnf(formula)
    clauses = set()
    def collect(f):
        if isinstance(f, Conj):
            for p in f.parts:
                collect(p)
        else:
            clauses.add(_make_clause(f))
    collect(cnf)
    return clauses

def _make_clause(f):
    lits = set()
    def walk(g):
        if isinstance(g, Disj):
            for p in g.parts: walk(p)
        elif isinstance(g, Neg) and isinstance(g.inner, Atom):
            lits.add((g.inner.name, False))
        elif isinstance(g, Atom):
            lits.add((g.name, True))
        else:
            raise ValueError(f"not a literal: {g}")
    walk(f)
    return frozenset(lits)


#semantic helpers

def _all_valuations(atoms):
    atoms = sorted(atoms)
    n = len(atoms)
    for i in range(1 << n):
        yield {a: bool((i >> j) & 1) for j, a in enumerate(atoms)}

def is_tautology(f: Formula) -> bool:
    return all(f.eval(v) for v in _all_valuations(f.atoms()))

def is_satisfiable(f: Formula) -> bool:
    atoms = f.atoms()
    if not atoms:
        return f.eval({})
    return any(f.eval(v) for v in _all_valuations(atoms))

def equivalent(a: Formula, b: Formula) -> bool:
    return is_tautology(Bicond(a, b))
