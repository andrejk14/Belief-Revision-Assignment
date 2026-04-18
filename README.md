# Belief Revision Engine

This repository contains a propositional-logic belief revision engine based on course concepts such as CNF conversion, resolution, AGM revision, and partial meet contraction.

## Files

- `belief_base.py`: belief base with priorities
- `logic.py`: formula classes, parser, CNF conversion, satisfiability and tautology helpers
- `resolution.py`: entailment by resolution refutation, with a semantic fallback for large clause sets
- `revision.py`: expansion, contraction, and revision
- `agm_tests.py`: tests for the required AGM postulates
- `mastermind.py`: optional Mastermind code-breaker
- `main.py`: demo runner

## Run

```bash
python3 agm_tests.py
python3 main.py
python3 mastermind.py
python3 mastermind.py --auto
```

## Formula syntax

Operators from lowest to highest precedence:

1. `<>`
2. `>>`
3. `|`
4. `&`
5. `~`

Examples:

```text
p & q
p >> q
~(a | b)
p <> q
```
