# Belief Revision Engine

This project implements a small belief revision engine for propositional logic.
It includes:

- a propositional formula AST and parser
- CNF conversion and resolution-based entailment
- priority-based partial meet contraction
- expansion and revision via the Levi identity
- AGM postulate tests
- an optional Mastermind solver built on top of the revision engine

## Files

- `logic.py` contains the formula representation, parser, CNF conversion, and semantic helpers.
- `belief_base.py` implements the finite belief base and priority-tagged entries.
- `resolution.py` implements entailment by refutation with a semantic fallback.
- `revision.py` implements expansion, contraction, and revision.
- `agm_tests.py` contains tests for Success, Inclusion, Vacuity, Consistency, and Extensionality.
- `mastermind.py` contains the optional Mastermind code-breaker.
- `main.py` runs the demos, tests, and a sample Mastermind game.

## Running

```bash
python3 main.py
python3 agm_tests.py
python3 mastermind.py
python3 mastermind.py --auto
```

## Formula syntax

Operators from lowest to highest precedence:

- `<>` biconditional
- `>>` implication
- `|` disjunction
- `&` conjunction
- `~` negation

Examples:

```text
p & q
p >> q
~(a | b)
p <> q
```
