# Belief Revision Engine

AGM-based belief revision for propositional logic. Includes a Mastermind solver.

## Requirements
Python 3.10+, no external packages.

## Files
- `logic.py` — formula AST, parser, CNF conversion, semantic helpers
- `resolution.py` — resolution-based entailment (with semantic fallback for large inputs)
- `belief_base.py` — belief base with priority-tagged formulas
- `revision.py` — expansion, contraction (partial meet), revision (Levi identity)
- `agm_tests.py` — tests for the five AGM postulates
- `mastermind.py` — Mastermind code-breaker using belief revision
- `main.py` — runs demos, AGM tests, and a Mastermind game

## Running
```
python3 main.py                  # everything
python3 agm_tests.py             # AGM tests only
python3 mastermind.py             # interactive Mastermind
python3 mastermind.py --auto      # auto game with random secret
```

## Formula syntax
Connectives (low to high precedence): `<>`, `>>`, `|`, `&`, `~`

Examples: `p & q`, `p >> q`, `~(a | b)`, `p <> q`
