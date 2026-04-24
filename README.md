# Belief Revision Engine

Propositional-logic belief revision engine covering CNF conversion, resolution-based entailment, partial meet contraction, and AGM revision via the Levi identity. Includes an optional Mastermind code-breaker built on top of the engine.

Requires Python 3.10+ and has no third-party dependencies.

## Files

- `belief_base.py`: belief base with priority-tagged formulas
- `logic.py`: formula classes, parser, CNF conversion, satisfiability and tautology helpers
- `resolution.py`: entailment by resolution refutation over CNF clause sets
- `revision.py`: expansion, partial meet contraction, and revision (Levi identity)
- `agm_tests.py`: `unittest` suite for the AGM postulates, contraction properties, resolution, and the parser
- `mastermind.py`: optional Mastermind code-breaker driven by belief revision
- `main.py`: demo runner walking through each stage of the assignment

## Run

```bash
python3 agm_tests.py             # run the full test suite
python3 main.py                  # demo of all stages + Mastermind
python3 mastermind.py            # interactive Mastermind
python3 mastermind.py --auto     # auto game with a random secret
```

## Tests

`python3 agm_tests.py` runs four groups of tests:

- **Revision postulates** (Success, Inclusion, Vacuity, Consistency, Extensionality, Closure)
- **Contraction postulates** (Success, Inclusion, Vacuity, Extensionality; plus an explicit Recovery counterexample — Recovery does not hold for belief-base partial meet in general)
- **Resolution** (modus ponens, modus tollens, disjunctive syllogism, inconsistency detection, tautology entailment)
- **Parser** (error handling for malformed formulas)

## Formula syntax

Operators from lowest to highest precedence:

1. `<>` — biconditional
2. `>>` — implication
3. `|` — disjunction
4. `&` — conjunction
5. `~` — negation

Examples:

```text
p & q
p >> q
~(a | b)
p <> q
```
