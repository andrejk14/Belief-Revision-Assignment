from __future__ import annotations

import random

from belief_base import BeliefBase
from logic import parse
from mastermind import N_COLORS, N_POSITIONS, play_auto
from resolution import entails
from revision import contraction, expansion, revision


def demo_belief_revision() -> None:
    print("=" * 60)
    print("Belief Revision Engine")
    print("=" * 60)

    print("\n[1] Belief base")
    base = BeliefBase()
    base.add(parse("p"), 3)
    base.add(parse("p >> q"), 2)
    base.add(parse("q >> r"), 1)
    print(base)

    print("\n[2] Entailment via resolution")
    for goal in ("q", "r", "s"):
        print(f"  entails({goal})? {entails(base.formulas(), parse(goal))}")

    print("\n[3] Expansion: B + (s >> q)")
    expanded = expansion(base, parse("s >> q"), priority=1)
    print(expanded)

    print("\n[4] Contraction: B / r")
    contracted = contraction(base, parse("r"))
    print(contracted)
    print(f"  entails(r)? {entails(contracted.formulas(), parse('r'))}")

    print("\n[5] Revision: B * ~r")
    revised = revision(base, parse("~r"), priority=2)
    print(revised)
    print(f"  entails(~r)? {entails(revised.formulas(), parse('~r'))}")
    print(f"  entails(p)?  {entails(revised.formulas(), parse('p'))}")


def demo_mastermind() -> None:
    print("\n" + "=" * 60)
    print("Mastermind (optional)")
    print("=" * 60)
    secret = random.sample(range(N_COLORS), N_POSITIONS)
    play_auto(secret)


if __name__ == "__main__":
    demo_belief_revision()
    demo_mastermind()