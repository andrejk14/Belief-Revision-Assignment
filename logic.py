"""
Propositional logic: formula representation, parsing, and CNF conversion.
"""
from __future__ import annotations
from typing import Set, Dict
import re


# ── Formula classes ──────────────────────────────────────────────────────────

class Formula:
    """Base class for propositional logic formulas."""

    def get_atoms(self) -> Set[str]:
        raise NotImplementedError

    def evaluate(self, valuation: Dict[str, bool]) -> bool:
        raise NotImplementedError

    def __eq__(self, other):
        return isinstance(other, self.__class__) and hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        raise NotImplementedError

    def __repr__(self):
        return str(self)


class Atom(Formula):
    def __init__(self, name: str):
        self.name = name

    def get_atoms(self) -> Set[str]:
        return {self.name}

    def evaluate(self, valuation: Dict[str, bool]) -> bool:
        return valuation[self.name]

    def __hash__(self):
        return hash(("Atom", self.name))

    def __str__(self):
        return self.name


class Not(Formula):
    def __init__(self, operand: Formula):
        self.operand = operand

    def get_atoms(self) -> Set[str]:
        return self.operand.get_atoms()

    def evaluate(self, valuation: Dict[str, bool]) -> bool:
        return not self.operand.evaluate(valuation)

    def __hash__(self):
        return hash(("Not", hash(self.operand)))

    def __str__(self):
        if isinstance(self.operand, Atom):
            return f"~{self.operand}"
        return f"~({self.operand})"


class And(Formula):
    def __init__(self, *conjuncts: Formula):
        self.conjuncts = list(conjuncts)

    def get_atoms(self) -> Set[str]:
        atoms = set()
        for c in self.conjuncts:
            atoms |= c.get_atoms()
        return atoms

    def evaluate(self, valuation: Dict[str, bool]) -> bool:
        return all(c.evaluate(valuation) for c in self.conjuncts)

    def __hash__(self):
        return hash(("And", frozenset(hash(c) for c in self.conjuncts)))

    def __str__(self):
        parts = []
        for c in self.conjuncts:
            if isinstance(c, (Or, Implies, Biconditional)):
                parts.append(f"({c})")
            else:
                parts.append(str(c))
        return " & ".join(parts)


class Or(Formula):
    def __init__(self, *disjuncts: Formula):
        self.disjuncts = list(disjuncts)

    def get_atoms(self) -> Set[str]:
        atoms = set()
        for d in self.disjuncts:
            atoms |= d.get_atoms()
        return atoms

    def evaluate(self, valuation: Dict[str, bool]) -> bool:
        return any(d.evaluate(valuation) for d in self.disjuncts)

    def __hash__(self):
        return hash(("Or", frozenset(hash(d) for d in self.disjuncts)))

    def __str__(self):
        parts = []
        for d in self.disjuncts:
            if isinstance(d, (And, Implies, Biconditional)):
                parts.append(f"({d})")
            else:
                parts.append(str(d))
        return " | ".join(parts)


class Implies(Formula):
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms() | self.right.get_atoms()

    def evaluate(self, valuation: Dict[str, bool]) -> bool:
        return (not self.left.evaluate(valuation)) or self.right.evaluate(valuation)

    def __hash__(self):
        return hash(("Implies", hash(self.left), hash(self.right)))

    def __str__(self):
        return f"{self.left} >> {self.right}"


class Biconditional(Formula):
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms() | self.right.get_atoms()

    def evaluate(self, valuation: Dict[str, bool]) -> bool:
        return self.left.evaluate(valuation) == self.right.evaluate(valuation)

    def __hash__(self):
        return hash(("Biconditional", frozenset([hash(self.left), hash(self.right)])))

    def __str__(self):
        return f"{self.left} <> {self.right}"


# ── Parser ───────────────────────────────────────────────────────────────────
# Grammar (lowest to highest precedence):
#   expr       := biconditional
#   biconditional := implication ('<>' implication)*
#   implication   := disjunction ('>>' disjunction)*
#   disjunction   := conjunction ('|' conjunction)*
#   conjunction   := unary ('&' unary)*
#   unary         := '~' unary | atom | '(' expr ')'
#   atom          := [a-zA-Z_][a-zA-Z_0-9]*

class _Tokenizer:
    TOKEN_RE = re.compile(r"\s*(~|&|\||\(|\)|>>|<>|[a-zA-Z_][a-zA-Z_0-9]*)\s*")

    def __init__(self, text: str):
        self.tokens = self.TOKEN_RE.findall(text)
        self.pos = 0

    def peek(self) -> str | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, tok: str):
        got = self.consume()
        if got != tok:
            raise ValueError(f"Expected '{tok}', got '{got}'")


def parse(text: str) -> Formula:
    """Parse a propositional logic string into a Formula."""
    tokenizer = _Tokenizer(text)
    result = _parse_biconditional(tokenizer)
    if tokenizer.peek() is not None:
        raise ValueError(f"Unexpected token: {tokenizer.peek()}")
    return result


def _parse_biconditional(tok: _Tokenizer) -> Formula:
    left = _parse_implication(tok)
    while tok.peek() == "<>":
        tok.consume()
        right = _parse_implication(tok)
        left = Biconditional(left, right)
    return left


def _parse_implication(tok: _Tokenizer) -> Formula:
    left = _parse_disjunction(tok)
    while tok.peek() == ">>":
        tok.consume()
        right = _parse_disjunction(tok)
        left = Implies(left, right)
    return left


def _parse_disjunction(tok: _Tokenizer) -> Formula:
    left = _parse_conjunction(tok)
    parts = [left]
    while tok.peek() == "|":
        tok.consume()
        parts.append(_parse_conjunction(tok))
    if len(parts) == 1:
        return parts[0]
    return Or(*parts)


def _parse_conjunction(tok: _Tokenizer) -> Formula:
    left = _parse_unary(tok)
    parts = [left]
    while tok.peek() == "&":
        tok.consume()
        parts.append(_parse_unary(tok))
    if len(parts) == 1:
        return parts[0]
    return And(*parts)


def _parse_unary(tok: _Tokenizer) -> Formula:
    if tok.peek() == "~":
        tok.consume()
        return Not(_parse_unary(tok))
    if tok.peek() == "(":
        tok.consume()
        expr = _parse_biconditional(tok)
        tok.expect(")")
        return expr
    name = tok.consume()
    return Atom(name)


# ── CNF Conversion ───────────────────────────────────────────────────────────

def to_cnf(formula: Formula) -> Formula:
    """Convert a formula to Conjunctive Normal Form."""
    f = _eliminate_biconditional(formula)
    f = _eliminate_implication(f)
    f = _push_negation(f)
    f = _distribute(f)
    f = _flatten(f)
    return f


def _eliminate_biconditional(f: Formula) -> Formula:
    if isinstance(f, Atom):
        return f
    if isinstance(f, Not):
        return Not(_eliminate_biconditional(f.operand))
    if isinstance(f, And):
        return And(*[_eliminate_biconditional(c) for c in f.conjuncts])
    if isinstance(f, Or):
        return Or(*[_eliminate_biconditional(d) for d in f.disjuncts])
    if isinstance(f, Implies):
        return Implies(_eliminate_biconditional(f.left), _eliminate_biconditional(f.right))
    if isinstance(f, Biconditional):
        left = _eliminate_biconditional(f.left)
        right = _eliminate_biconditional(f.right)
        # (left >> right) & (right >> left)
        return And(Implies(left, right), Implies(right, left))
    return f


def _eliminate_implication(f: Formula) -> Formula:
    if isinstance(f, Atom):
        return f
    if isinstance(f, Not):
        return Not(_eliminate_implication(f.operand))
    if isinstance(f, And):
        return And(*[_eliminate_implication(c) for c in f.conjuncts])
    if isinstance(f, Or):
        return Or(*[_eliminate_implication(d) for d in f.disjuncts])
    if isinstance(f, Implies):
        # p >> q  ≡  ~p | q
        return Or(Not(_eliminate_implication(f.left)), _eliminate_implication(f.right))
    return f


def _push_negation(f: Formula) -> Formula:
    """Push negations inward using De Morgan's laws and double negation."""
    if isinstance(f, Atom):
        return f
    if isinstance(f, Not):
        inner = f.operand
        if isinstance(inner, Not):
            return _push_negation(inner.operand)
        if isinstance(inner, And):
            return Or(*[_push_negation(Not(c)) for c in inner.conjuncts])
        if isinstance(inner, Or):
            return And(*[_push_negation(Not(d)) for d in inner.disjuncts])
        if isinstance(inner, Atom):
            return f
        return Not(_push_negation(inner))
    if isinstance(f, And):
        return And(*[_push_negation(c) for c in f.conjuncts])
    if isinstance(f, Or):
        return Or(*[_push_negation(d) for d in f.disjuncts])
    return f


def _distribute(f: Formula) -> Formula:
    """Distribute OR over AND to get CNF."""
    if isinstance(f, Atom) or isinstance(f, Not):
        return f
    if isinstance(f, And):
        return And(*[_distribute(c) for c in f.conjuncts])
    if isinstance(f, Or):
        disjuncts = [_distribute(d) for d in f.disjuncts]
        # Check if any disjunct is an And — distribute
        and_idx = None
        for i, d in enumerate(disjuncts):
            if isinstance(d, And):
                and_idx = i
                break
        if and_idx is None:
            return Or(*disjuncts)
        # Distribute: (A & B) | C  ≡  (A | C) & (B | C)
        and_part = disjuncts[and_idx]
        rest = disjuncts[:and_idx] + disjuncts[and_idx + 1:]
        result_conjuncts = []
        for conjunct in and_part.conjuncts:
            new_or = Or(conjunct, *rest)
            result_conjuncts.append(_distribute(new_or))
        return And(*result_conjuncts)
    return f


def _flatten(f: Formula) -> Formula:
    """Flatten nested And/Or."""
    if isinstance(f, Atom) or isinstance(f, Not):
        return f
    if isinstance(f, And):
        conjuncts = []
        for c in f.conjuncts:
            c = _flatten(c)
            if isinstance(c, And):
                conjuncts.extend(c.conjuncts)
            else:
                conjuncts.append(c)
        if len(conjuncts) == 1:
            return conjuncts[0]
        return And(*conjuncts)
    if isinstance(f, Or):
        disjuncts = []
        for d in f.disjuncts:
            d = _flatten(d)
            if isinstance(d, Or):
                disjuncts.extend(d.disjuncts)
            else:
                disjuncts.append(d)
        if len(disjuncts) == 1:
            return disjuncts[0]
        return Or(*disjuncts)
    return f


# ── Clause extraction ────────────────────────────────────────────────────────

def to_clauses(formula: Formula) -> set[frozenset[tuple[str, bool]]]:
    """
    Convert formula to CNF and extract clauses.
    Each clause is a frozenset of (atom_name, polarity) tuples.
    E.g., {("p", True), ("q", False)} represents (p | ~q).
    """
    cnf = to_cnf(formula)
    clauses = set()

    def extract_clauses(f: Formula):
        if isinstance(f, And):
            for c in f.conjuncts:
                extract_clauses(c)
        else:
            clauses.add(_clause_from_disjunction(f))

    extract_clauses(cnf)
    return clauses


def _clause_from_disjunction(f: Formula) -> frozenset[tuple[str, bool]]:
    """Extract literals from a disjunction (or single literal)."""
    literals = set()

    def extract_literals(g: Formula):
        if isinstance(g, Or):
            for d in g.disjuncts:
                extract_literals(d)
        elif isinstance(g, Not) and isinstance(g.operand, Atom):
            literals.add((g.operand.name, False))
        elif isinstance(g, Atom):
            literals.add((g.name, True))
        else:
            raise ValueError(f"Expected literal or disjunction in CNF, got: {g}")

    extract_literals(f)
    return frozenset(literals)


# ── Helpers ──────────────────────────────────────────────────────────────────

def is_tautology(formula: Formula) -> bool:
    """Check if a formula is a tautology by evaluating all valuations."""
    atoms = sorted(formula.get_atoms())
    for i in range(2 ** len(atoms)):
        valuation = {}
        for j, atom in enumerate(atoms):
            valuation[atom] = bool((i >> j) & 1)
        if not formula.evaluate(valuation):
            return False
    return True


def is_satisfiable(formula: Formula) -> bool:
    """Check if a formula is satisfiable."""
    atoms = sorted(formula.get_atoms())
    if not atoms:
        try:
            return formula.evaluate({})
        except Exception:
            return True
    for i in range(2 ** len(atoms)):
        valuation = {}
        for j, atom in enumerate(atoms):
            valuation[atom] = bool((i >> j) & 1)
        if formula.evaluate(valuation):
            return True
    return False


def formulas_equivalent(f1: Formula, f2: Formula) -> bool:
    """Check if two formulas are logically equivalent."""
    return is_tautology(Biconditional(f1, f2))
