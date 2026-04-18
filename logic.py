from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, Sequence


class Formula:
    """Base class for propositional formulas."""

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
        if isinstance(self.inner, Atom):
            return f"~{self.inner}"
        return f"~({self.inner})"


@dataclass(frozen=True)
class Conj(Formula):
    parts: tuple[Formula, ...]

    def __init__(self, *parts: Formula):
        object.__setattr__(self, "parts", tuple(parts))

    def atoms(self) -> set[str]:
        result: set[str] = set()
        for part in self.parts:
            result |= part.atoms()
        return result

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return all(part.eval(valuation) for part in self.parts)

    def __str__(self) -> str:
        rendered: list[str] = []
        for part in self.parts:
            text = str(part)
            if isinstance(part, (Disj, Impl, Bicond)):
                text = f"({text})"
            rendered.append(text)
        return " & ".join(rendered)


@dataclass(frozen=True)
class Disj(Formula):
    parts: tuple[Formula, ...]

    def __init__(self, *parts: Formula):
        object.__setattr__(self, "parts", tuple(parts))

    def atoms(self) -> set[str]:
        result: set[str] = set()
        for part in self.parts:
            result |= part.atoms()
        return result

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return any(part.eval(valuation) for part in self.parts)

    def __str__(self) -> str:
        rendered: list[str] = []
        for part in self.parts:
            text = str(part)
            if isinstance(part, (Conj, Impl, Bicond)):
                text = f"({text})"
            rendered.append(text)
        return " | ".join(rendered)


@dataclass(frozen=True)
class Impl(Formula):
    lhs: Formula
    rhs: Formula

    def atoms(self) -> set[str]:
        return self.lhs.atoms() | self.rhs.atoms()

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return (not self.lhs.eval(valuation)) or self.rhs.eval(valuation)

    def __str__(self) -> str:
        return f"{self.lhs} >> {self.rhs}"


@dataclass(frozen=True)
class Bicond(Formula):
    lhs: Formula
    rhs: Formula

    def atoms(self) -> set[str]:
        return self.lhs.atoms() | self.rhs.atoms()

    def eval(self, valuation: Dict[str, bool]) -> bool:
        return self.lhs.eval(valuation) == self.rhs.eval(valuation)

    def __str__(self) -> str:
        return f"{self.lhs} <> {self.rhs}"


_TOKEN_RE = re.compile(r"\s*(>>|<>|~|&|\||\(|\)|[A-Za-z_]\w*)")
_ATOM_RE = re.compile(r"^[A-Za-z_]\w*$")


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.tokens = self._tokenize(text)
        self.pos = 0

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens: list[str] = []
        index = 0
        while index < len(text):
            match = _TOKEN_RE.match(text, index)
            if match is None:
                if text[index].isspace():
                    index += 1
                    continue
                raise SyntaxError(f"Invalid token near: {text[index:index + 10]!r}")
            token = match.group(1)
            tokens.append(token)
            index = match.end()
        return tokens

    def parse(self) -> Formula:
        if not self.tokens:
            raise SyntaxError("Empty formula")
        formula = self._biconditional()
        if self._peek() is not None:
            raise SyntaxError(f"Unexpected trailing token: {self._peek()}")
        return formula

    def _peek(self) -> str | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def _eat(self) -> str:
        token = self._peek()
        if token is None:
            raise SyntaxError("Unexpected end of input")
        self.pos += 1
        return token

    def _expect(self, expected: str) -> None:
        token = self._eat()
        if token != expected:
            raise SyntaxError(f"Expected '{expected}', got '{token}'")

    def _biconditional(self) -> Formula:
        left = self._implication()
        while self._peek() == "<>":
            self._eat()
            right = self._implication()
            left = Bicond(left, right)
        return left

    def _implication(self) -> Formula:
        left = self._disjunction()
        if self._peek() == ">>":
            self._eat()
            right = self._implication()
            return Impl(left, right)
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
        token = self._peek()
        if token == "~":
            self._eat()
            return Neg(self._unary())
        if token == "(":
            self._eat()
            formula = self._biconditional()
            self._expect(")")
            return formula
        if token is None:
            raise SyntaxError("Unexpected end of input")
        if _ATOM_RE.match(token):
            return Atom(self._eat())
        raise SyntaxError(f"Expected an atom, got '{token}'")


def parse(text: str) -> Formula:
    return _Parser(text).parse()


def to_cnf(formula: Formula) -> Formula:
    formula = _elim_biconditional(formula)
    formula = _elim_implication(formula)
    formula = _push_negations(formula)
    formula = _distribute_disjunction(formula)
    return _flatten(formula)


def _elim_biconditional(formula: Formula) -> Formula:
    if isinstance(formula, Atom):
        return formula
    if isinstance(formula, Neg):
        return Neg(_elim_biconditional(formula.inner))
    if isinstance(formula, Conj):
        return Conj(*(_elim_biconditional(part) for part in formula.parts))
    if isinstance(formula, Disj):
        return Disj(*(_elim_biconditional(part) for part in formula.parts))
    if isinstance(formula, Impl):
        return Impl(_elim_biconditional(formula.lhs), _elim_biconditional(formula.rhs))
    if isinstance(formula, Bicond):
        left = _elim_biconditional(formula.lhs)
        right = _elim_biconditional(formula.rhs)
        return Conj(Impl(left, right), Impl(right, left))
    raise TypeError(f"Unsupported formula type: {type(formula).__name__}")


def _elim_implication(formula: Formula) -> Formula:
    if isinstance(formula, Atom):
        return formula
    if isinstance(formula, Neg):
        return Neg(_elim_implication(formula.inner))
    if isinstance(formula, Conj):
        return Conj(*(_elim_implication(part) for part in formula.parts))
    if isinstance(formula, Disj):
        return Disj(*(_elim_implication(part) for part in formula.parts))
    if isinstance(formula, Impl):
        return Disj(Neg(_elim_implication(formula.lhs)), _elim_implication(formula.rhs))
    raise TypeError(f"Unsupported formula type: {type(formula).__name__}")


def _push_negations(formula: Formula) -> Formula:
    if isinstance(formula, Atom):
        return formula
    if isinstance(formula, Neg):
        inner = formula.inner
        if isinstance(inner, Atom):
            return formula
        if isinstance(inner, Neg):
            return _push_negations(inner.inner)
        if isinstance(inner, Conj):
            return Disj(*(_push_negations(Neg(part)) for part in inner.parts))
        if isinstance(inner, Disj):
            return Conj(*(_push_negations(Neg(part)) for part in inner.parts))
        return Neg(_push_negations(inner))
    if isinstance(formula, Conj):
        return Conj(*(_push_negations(part) for part in formula.parts))
    if isinstance(formula, Disj):
        return Disj(*(_push_negations(part) for part in formula.parts))
    raise TypeError(f"Unsupported formula type: {type(formula).__name__}")


def _distribute_disjunction(formula: Formula) -> Formula:
    if isinstance(formula, (Atom, Neg)):
        return formula
    if isinstance(formula, Conj):
        return Conj(*(_distribute_disjunction(part) for part in formula.parts))
    if isinstance(formula, Disj):
        parts = [_distribute_disjunction(part) for part in formula.parts]
        for index, part in enumerate(parts):
            if isinstance(part, Conj):
                others = parts[:index] + parts[index + 1 :]
                return Conj(*(_distribute_disjunction(Disj(conj_part, *others)) for conj_part in part.parts))
        return Disj(*parts)
    raise TypeError(f"Unsupported formula type: {type(formula).__name__}")


def _flatten(formula: Formula) -> Formula:
    if isinstance(formula, (Atom, Neg)):
        return formula
    if isinstance(formula, Conj):
        parts: list[Formula] = []
        for part in formula.parts:
            flat = _flatten(part)
            if isinstance(flat, Conj):
                parts.extend(flat.parts)
            else:
                parts.append(flat)
        return parts[0] if len(parts) == 1 else Conj(*parts)
    if isinstance(formula, Disj):
        parts: list[Formula] = []
        for part in formula.parts:
            flat = _flatten(part)
            if isinstance(flat, Disj):
                parts.extend(flat.parts)
            else:
                parts.append(flat)
        return parts[0] if len(parts) == 1 else Disj(*parts)
    raise TypeError(f"Unsupported formula type: {type(formula).__name__}")


Clause = frozenset[tuple[str, bool]]


def to_clauses(formula: Formula) -> set[Clause]:
    """Convert a formula to a set of CNF clauses."""
    cnf = to_cnf(formula)
    clauses: set[Clause] = set()

    def collect(node: Formula) -> None:
        if isinstance(node, Conj):
            for part in node.parts:
                collect(part)
        else:
            clauses.add(_make_clause(node))

    collect(cnf)
    return clauses


def _make_clause(formula: Formula) -> Clause:
    literals: set[tuple[str, bool]] = set()

    def walk(node: Formula) -> None:
        if isinstance(node, Disj):
            for part in node.parts:
                walk(part)
        elif isinstance(node, Neg) and isinstance(node.inner, Atom):
            literals.add((node.inner.name, False))
        elif isinstance(node, Atom):
            literals.add((node.name, True))
        else:
            raise ValueError(f"Expected a literal, got: {node}")

    walk(formula)
    return frozenset(literals)


def _all_valuations(atoms: Iterable[str]) -> Iterator[Dict[str, bool]]:
    names = sorted(set(atoms))
    total = len(names)
    for mask in range(1 << total):
        yield {name: bool((mask >> index) & 1) for index, name in enumerate(names)}


def is_tautology(formula: Formula) -> bool:
    return all(formula.eval(valuation) for valuation in _all_valuations(formula.atoms()))


def is_satisfiable(formula: Formula) -> bool:
    atoms = formula.atoms()
    if not atoms:
        return formula.eval({})
    return any(formula.eval(valuation) for valuation in _all_valuations(atoms))


def equivalent(left: Formula, right: Formula) -> bool:
    return is_tautology(Bicond(left, right))
