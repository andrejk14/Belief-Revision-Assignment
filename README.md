# Belief Revision Engine

AGM-based belief revision for propositional logic, with a Mastermind solver built on top.

## Requirements

Python 3.10+, no external packages needed.

## Files

- `logic.py` — Formula AST, recursive-descent parser, CNF conversion, semantic helpers
- `resolution.py` — Resolution-based entailment checker (implemented from scratch)
- `belief_base.py` — Belief base with priority-tagged formulas
- `revision.py` — Expansion, contraction (partial meet), and revision (Levi identity)
- `agm_tests.py` — Checks the five AGM postulates
- `mastermind.py` — Mastermind code-breaker using belief revision
- `main.py` — Runs demos, AGM tests, and an auto Mastermind game

## How to run

```
python3 main.py                  # everything
python3 agm_tests.py             # just the AGM tests
python3 mastermind.py             # interactive Mastermind
python3 mastermind.py --auto      # auto game with random secret
```

## Formula syntax

Connectives by precedence (low → high): `<>`, `>>`, `|`, `&`, `~`

Examples: `p & q`, `p >> q`, `~(a | b)`, `p <> q`

Atoms can be any identifier starting with a letter.
