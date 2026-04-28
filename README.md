# Belief Revision Assignment

Belief revision engine for the 02180 assignment. Implements a belief base with
priorities, resolution-based entailment, partial meet contraction, expansion,
and AGM revision (Levi identity). Also includes a Mastermind code-breaker
built on top of the engine.

Written in Python 3 (tested with 3.10). No external libraries.

## Files

- `belief_base.py` - belief base, formulas tagged with a priority
- `logic.py` - Formula classes, a small parser, and CNF conversion
- `resolution.py` - resolution refutation for entailment
- `revision.py` - expansion, partial meet contraction, revision
- `agm_tests.py` - tests for the AGM postulates and the rest of the engine
- `mastermind.py` - Mastermind code-breaker (the optional part)
- `main.py` - small demo that runs through each step

## How to run

Run the tests:

    python3 agm_tests.py

Run the demo (belief revision + Mastermind):

    python3 main.py

Play Mastermind:

    python3 mastermind.py            # interactive
    python3 mastermind.py --auto     # auto game with a random secret

## What the tests cover

- Revision postulates: Success, Inclusion, Vacuity, Consistency, Extensionality
- Contraction postulates: Success, Inclusion, Vacuity, Extensionality, and a
  counterexample showing that Recovery does not hold for partial meet on a
  belief base
- Partial meet: that the result is the intersection of selected remainders,
  and that priorities break ties
- Resolution on a few standard inference rules
- A couple of CNF and parser sanity checks

## Formula syntax

The parser uses these operators (low to high precedence):

1. `<>` biconditional
2. `>>` implication
3. `|`  or
4. `&`  and
5. `~`  not

Examples: `p & q`, `p >> q`, `~(a | b)`, `p <> q`.
