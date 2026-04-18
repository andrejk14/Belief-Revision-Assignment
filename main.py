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

    print("\n1. Belief base")
    base = BeliefBase()
    base.add(parse("p"), 3)
    base.add(parse("p >> q"), 2)
    base.add(parse("q >> r"), 1)
    print(base)

    print("\n2. Entailment")
    print(f"Entails q? {entails(base.formulas(), parse('q'))}")
    print(f"Entails r? {entails(base.formulas(), parse('r'))}")

    print("\n3. Contraction")
    contracted = contraction(base, parse("r"))
    print("After contracting by r:")
    print(contracted)
    print(f"Entails r? {entails(contracted.formulas(), parse('r'))}")

    print("\n4. Expansion")
    weather = BeliefBase()
    weather.add(parse("sunny"), 2)
    weather.add(parse("sunny >> warm"), 1)
    print(weather)
    expanded = expansion(weather, parse("windy"), priority=1)
    print("After expanding with windy:")
    print(expanded)

    print("\n5. Revision")
    revised = revision(base, parse("~r"), priority=2)
    print("After revising by ~r:")
    print(revised)
    print(f"Entails ~r? {entails(revised.formulas(), parse('~r'))}")
    print(f"Entails r?  {entails(revised.formulas(), parse('r'))}")


def demo_mastermind() -> None:
    print("\n" + "=" * 60)
    print("Optional Mastermind")
    print("=" * 60)
    secret = random.sample(range(N_COLORS), N_POSITIONS)
    play_auto(secret)


if __name__ == "__main__":
    demo_belief_revision()
    demo_mastermind()
