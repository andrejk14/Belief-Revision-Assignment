from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator


class Formula:
    def atoms(self) -> set[str]:
        raise NotImplementedError

    def eval(self, valuation: Dict[str, bool]) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class Atom(Formula):
    name: str

    def atoms(self) -> set[str]:
        return {self.name}

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return valuation[self.name]

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Neg(Formula):
    inner: Formula

    def atoms(self) -> set[str]:
        return self.inner.atoms()

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return not self.inner.eval(valuation)

    def __str__(self) -> str:
        if isinstance(self.inner, (Atom, Neg)):
            return f"~{self.inner}"
        return f"~({self.inner})"


@dataclass(frozen=True)
class Conj(Formula):
    parts: tuple[Formula, ...]

    def __init__(self, *parts: Formula):
        object.__setattr__(self, "parts", tuple(parts))

    def atoms(self) -> set[str]:
        return set().union(*(p.atoms() for p in self.parts))

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return all(p.eval(valuation) for p in self.parts)

    def __str__(self) -> str:
        return " & ".join(_paren_if(p, (Disj, Impl, Bicond)) for p in self.parts)


@dataclass(frozen=True)
class Disj(Formula):
    parts: tuple[Formula, ...]

    def __init__(self, *parts: Formula):
        object.__setattr__(self, "parts", tuple(parts))

    def atoms(self) -> set[str]:
        return set().union(*(p.atoms() for p in self.parts))

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return any(p.eval(valuation) for p in self.parts)

    def __str__(self) -> str:
        return " | ".join(_paren_if(p, (Conj, Impl, Bicond)) for p in self.parts)


@dataclass(frozen=True)
class Impl(Formula):
    lhs: Formula
    rhs: Formula

    def atoms(self) -> set[str]:
        return self.lhs.atoms() | self.rhs.atoms()

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return (not self.lhs.eval(valuation)) or self.rhs.eval(valuation)

    def __str__(self) -> str:
        return f"{_paren_if(self.lhs, (Impl, Bicond))} >> {_paren_if(self.rhs, (Bicond,))}"


@dataclass(frozen=True)
class Bicond(Formula):
    lhs: Formula
    rhs: Formula

    def atoms(self) -> set[str]:
        return self.lhs.atoms() | self.rhs.atoms()

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return self.lhs.eval(valuation) == self.rhs.eval(valuation)

    def __str__(self) -> str:
        return f"{_paren_if(self.lhs, (Bicond,))} <> {_paren_if(self.rhs, (Bicond,))}"


def _paren_if(f: Formula, types: tuple) -> str:
    return f"({f})" if isinstance(f, types) else str(f)


# precedence (low -> high): <>, >>, |, &, ~  (>> is right-assoc)
_TOKEN_RE = re.compile(r"\s*(>>|<>|~|&|\||\(|\)|[A-Za-z_]\w*)")
_ATOM_RE = re.compile(r"^[A-Za-z_]\w*$")


class _Parser:
    def __init__(self, text: str):
        self.tokens = self._tokenize(text)
        self.pos = 0

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens: list[str] = []
        i = 0
        while i < len(text):
            m = _TOKEN_RE.match(text, i)
            if m is None:
                if text[i].isspace():
                    i += 1
                    continue
                raise SyntaxError(f"Invalid token near: {text[i:i+10]!r}")
            tokens.append(m.group(1))
            i = m.end()
        return tokens

    def parse(self) -> Formula:
        if not self.tokens:
            raise SyntaxError("Empty formula")
        f = self._biconditional()
        if self._peek() is not None:
            raise SyntaxError(f"Unexpected trailing token: {self._peek()}")
        return f

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _eat(self) -> str:
        t = self._peek()
        if t is None:
            raise SyntaxError("Unexpected end of input")
        self.pos += 1
        return t

    def _expect(self, expected: str) -> None:
        t = self._eat()
        if t != expected:
            raise SyntaxError(f"Expected '{expected}', got '{t}'")

    def _biconditional(self) -> Formula:
        left = self._implication()
        while self._peek() == "<>":
            self._eat()
            left = Bicond(left, self._implication())
        return left

    def _implication(self) -> Formula:
        left = self._disjunction()
        if self._peek() == ">>":
            self._eat()
            return Impl(left, self._implication())
        return left

    def _disjunction(self) -> Formula:
        parts = [self._conjunction()]
        while self._peek() == "|":
            self._eat()
            parts.append(self._conjunction())
        return parts[0] if len(parts) == 1 else Disj(*parts)

    def _conjunction(self) -> Formula:
        parts = [self._unary()]
        while self._peek() == "&":
            self._eat()
            parts.append(self._unary())
        return parts[0] if len(parts) == 1 else Conj(*parts)

    def _unary(self) -> Formula:
        t = self._peek()
        if t == "~":
            self._eat()
            return Neg(self._unary())
        if t == "(":
            self._eat()
            f = self._biconditional()
            self._expect(")")
            return f
        if t is None:
            raise SyntaxError("Unexpected end of input")
        if _ATOM_RE.match(t):
            return Atom(self._eat())
        raise SyntaxError(f"Expected an atom, got '{t}'")


def parse(text: str) -> Formula:
    return _Parser(text).parse()


# CNF pipeline: drop <>, drop >>, NNF, distribute |/&, flatten.
def to_cnf(formula: Formula) -> Formula:
    f = _elim_bicond(formula)
    f = _elim_impl(f)
    f = _nnf(f)
    f = _distribute(f)
    return _flatten(f)


def _elim_bicond(f: Formula) -> Formula:
    if isinstance(f, Atom):
        return f
    if isinstance(f, Neg):
        return Neg(_elim_bicond(f.inner))
    if isinstance(f, Conj):
        return Conj(*(_elim_bicond(p) for p in f.parts))
    if isinstance(f, Disj):
        return Disj(*(_elim_bicond(p) for p in f.parts))
    if isinstance(f, Impl):
        return Impl(_elim_bicond(f.lhs), _elim_bicond(f.rhs))
    if isinstance(f, Bicond):
        lhs, rhs = _elim_bicond(f.lhs), _elim_bicond(f.rhs)
        return Conj(Impl(lhs, rhs), Impl(rhs, lhs))
    raise TypeError(type(f).__name__)


def _elim_impl(f: Formula) -> Formula:
    if isinstance(f, Atom):
        return f
    if isinstance(f, Neg):
        return Neg(_elim_impl(f.inner))
    if isinstance(f, Conj):
        return Conj(*(_elim_impl(p) for p in f.parts))
    if isinstance(f, Disj):
        return Disj(*(_elim_impl(p) for p in f.parts))
    if isinstance(f, Impl):
        return Disj(Neg(_elim_impl(f.lhs)), _elim_impl(f.rhs))
    raise TypeError(type(f).__name__)


def _nnf(f: Formula) -> Formula:
    if isinstance(f, Atom):
        return f
    if isinstance(f, Neg):
        inner = f.inner
        if isinstance(inner, Atom):
            return f
        if isinstance(inner, Neg):
            return _nnf(inner.inner)
        if isinstance(inner, Conj):
            return Disj(*(_nnf(Neg(p)) for p in inner.parts))
        if isinstance(inner, Disj):
            return Conj(*(_nnf(Neg(p)) for p in inner.parts))
    if isinstance(f, Conj):
        return Conj(*(_nnf(p) for p in f.parts))
    if isinstance(f, Disj):
        return Disj(*(_nnf(p) for p in f.parts))
    raise TypeError(type(f).__name__)


def _distribute(f: Formula) -> Formula:
    if isinstance(f, (Atom, Neg)):
        return f
    if isinstance(f, Conj):
        return Conj(*(_distribute(p) for p in f.parts))
    if isinstance(f, Disj):
        parts = [_distribute(p) for p in f.parts]
        for i, p in enumerate(parts):
            if isinstance(p, Conj):
                rest = parts[:i] + parts[i + 1:]
                return Conj(*(_distribute(Disj(c, *rest)) for c in p.parts))
        return Disj(*parts)
    raise TypeError(type(f).__name__)


def _flatten(f: Formula) -> Formula:
    if isinstance(f, (Atom, Neg)):
        return f
    if isinstance(f, Conj):
        flat: list[Formula] = []
        for p in f.parts:
            fp = _flatten(p)
            flat.extend(fp.parts if isinstance(fp, Conj) else [fp])
        return flat[0] if len(flat) == 1 else Conj(*flat)
    if isinstance(f, Disj):
        flat: list[Formula] = []
        for p in f.parts:
            fp = _flatten(p)
            flat.extend(fp.parts if isinstance(fp, Disj) else [fp])
        return flat[0] if len(flat) == 1 else Disj(*flat)
    raise TypeError(type(f).__name__)


Clause = frozenset[tuple[str, bool]]


def to_clauses(formula: Formula) -> set[Clause]:
    cnf = to_cnf(formula)
    clauses: set[Clause] = set()

    def collect(node: Formula) -> None:
        if isinstance(node, Conj):
            for p in node.parts:
                collect(p)
        else:
            clauses.add(_make_clause(node))

    collect(cnf)
    return clauses


def _make_clause(formula: Formula) -> Clause:
    lits: set[tuple[str, bool]] = set()

    def walk(node: Formula) -> None:
        if isinstance(node, Disj):
            for p in node.parts:
                walk(p)
        elif isinstance(node, Neg) and isinstance(node.inner, Atom):
            lits.add((node.inner.name, False))
        elif isinstance(node, Atom):
            lits.add((node.name, True))
        else:
            raise ValueError(f"Not a literal: {node}")

    walk(formula)
    return frozenset(lits)


# Truth-table helpers. Used by the tests as a ground-truth oracle.
def _all_valuations(atoms: Iterable[str]) -> Iterator[Dict[str, bool]]:
    names = sorted(set(atoms))
    for mask in range(1 << len(names)):
        yield {name: bool((mask >> i) & 1) for i, name in enumerate(names)}


def is_tautology(formula: Formula) -> bool:
    return all(formula.eval(v) for v in _all_valuations(formula.atoms()))


def is_satisfiable(formula: Formula) -> bool:
    atoms = formula.atoms()
    if not atoms:
        return formula.eval({})
    return any(formula.eval(v) for v in _all_valuations(atoms))


def equivalent(a: Formula, b: Formula) -> bool:
    return is_tautology(Bicond(a, b))