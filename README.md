# Belief Revision Engine

This repository contains a propositional-logic belief revision engine built around AGM-style revision.
It is implemented from scratch using course concepts (parser, CNF, resolution, contraction/expansion/revision).

## Requirement Coverage

The assignment asks for four stages. The implementation follows them directly:

1. **Belief base design**: `belief_base.py` implements a finite belief base with priorities.
2. **Logical entailment**: `resolution.py` implements entailment by resolution refutation over CNF clauses (`logic.py`).
3. **Contraction**: `revision.py` implements **priority-guided partial meet contraction**.
4. **Expansion**: `revision.py` adds formulas with priorities; `revision()` uses Levi identity.

AGM postulates requested in the assignment are tested in `agm_tests.py`:

- Success
- Inclusion
- Vacuity
- Consistency
- Extensionality

Optional part:

- `mastermind.py` integrates the revision engine into a Mastermind code-breaker.

## Project Structure

- `logic.py`: formula AST, parser, CNF conversion, satisfiability/tautology/equivalence helpers.
- `belief_base.py`: belief entries and priority-aware base operations.
- `resolution.py`: clause extraction and resolution-based entailment.
- `revision.py`: expansion, contraction, revision.
- `agm_tests.py`: unit tests for required postulates and parser edge cases.
- `mastermind.py`: optional game integration.
- `main.py`: demo runner (belief revision demo + AGM tests + Mastermind auto game).

## Run Instructions

No external Python dependencies are required.

```bash
python3 agm_tests.py
python3 main.py
python3 mastermind.py
python3 mastermind.py --auto
```

## Formula Syntax

Operator precedence (low to high):

1. `<>` biconditional
2. `>>` implication
3. `|` disjunction
4. `&` conjunction
5. `~` negation

Examples:

```text
p & q
p >> q
~(a | b)
p <> q
```
