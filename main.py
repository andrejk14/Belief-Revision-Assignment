from __future__ import annotations

import random
import unittest

import agm_tests
from belief_base import BeliefBase
from logic import parse
from mastermind import N_COLORS, N_POSITIONS, play_auto
from resolution import entails
from revision import contraction, expansion, revision


def demo_belief_revision() -> None:
    print("=" * 60)
    print("Belief Revision Engine")
    print("=" * 60)

    print("\n1. Revision over an implication chain")
    bb = BeliefBase()
    bb.add(parse("p"), 3)
    bb.add(parse("p >> q"), 2)
    bb.add(parse("q >> r"), 1)
    print(bb)
    print(f"Entails r? {entails(bb.formulas(), parse('r'))}")

    revised = revision(bb, parse("~r"), priority=2)
    print("After revising by ~r:")
    print(revised)
    print(f"Entails ~r? {entails(revised.formulas(), parse('~r'))}")
    print(f"Entails r?  {entails(revised.formulas(), parse('r'))}")

    print("\n2. Expansion")
    bb2 = BeliefBase()
    bb2.add(parse("sunny"), 2)
    bb2.add(parse("sunny >> warm"), 1)
    print(bb2)
    expanded = expansion(bb2, parse("windy"), priority=1)
    print("After expanding with windy:")
    print(expanded)

    print("\n3. Contraction")
    bb3 = BeliefBase()
    bb3.add(parse("a"), 3)
    bb3.add(parse("b"), 2)
    bb3.add(parse("a >> c"), 1)
    print(bb3)
    print(f"Entails c? {entails(bb3.formulas(), parse('c'))}")
    contracted = contraction(bb3, parse("c"))
    print("After contracting by c:")
    print(contracted)
    print(f"Entails c? {entails(contracted.formulas(), parse('c'))}")


def demo_mastermind() -> None:
    print("\n" + "=" * 60)
    print("Mastermind")
    print("=" * 60)
    secret = random.sample(range(N_COLORS), N_POSITIONS)
    play_auto(secret)


if __name__ == "__main__":
    demo_belief_revision()
    print()
    suite = unittest.defaultTestLoader.loadTestsFromModule(agm_tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    demo_mastermind()
