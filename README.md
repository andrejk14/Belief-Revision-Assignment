# Belief Revision Engine

Propositional logic belief revision engine implementing AGM theory, with a Mastermind game solver.

## Requirements

- Python 3.10+ (no external packages required)

## Project Structure

| File | Description |
|------|-------------|
| `logic.py` | Formula representation, parser, CNF conversion |
| `resolution.py` | Resolution-based logical entailment |
| `belief_base.py` | Belief base with priority ordering |
| `revision.py` | AGM operations: expansion, contraction, revision |
| `agm_tests.py` | AGM postulate verification tests |
| `mastermind.py` | Mastermind solver using belief revision |
| `main.py` | Demo and entry point |

## Usage

### Run full demo (belief revision examples + AGM tests + Mastermind auto-play)

```bash
python3 main.py
```

### Run AGM postulate tests only

```bash
python3 agm_tests.py
```

### Play Mastermind interactively

```bash
python3 mastermind.py
```

### Auto-play Mastermind (random secret code)

```bash
python3 mastermind.py --auto
```

## Formula Syntax

| Operator | Symbol | Example |
|----------|--------|---------|
| Negation | `~` | `~p` |
| Conjunction | `&` | `p & q` |
| Disjunction | `\|` | `p \| q` |
| Implication | `>>` | `p >> q` |
| Biconditional | `<>` | `p <> q` |

Parentheses for grouping: `(p | q) & r`
