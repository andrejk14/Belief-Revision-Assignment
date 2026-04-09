"""
Belief Revision Engine — Main entry point.
Demonstrates belief revision operations and runs AGM postulate tests.
"""
from logic import parse, Not, And, Or
from belief_base import BeliefBase
from revision import expansion, contraction, revision
from resolution import entails
from agm_tests import run_all_tests
from mastermind import play_auto, play_interactive, COLORS, NUM_POSITIONS, NUM_COLORS

import random


def demo_belief_revision():
    """Demonstrate the belief revision engine with examples."""
    print("=" * 60)
    print("BELIEF REVISION ENGINE — DEMONSTRATION")
    print("=" * 60)

    # ── Example 1: Basic revision ──
    print("\n--- Example 1: Basic Belief Revision ---")
    bb = BeliefBase()
    bb.add(parse("p"), priority=3)
    bb.add(parse("p >> q"), priority=2)
    bb.add(parse("q >> r"), priority=1)
    print(f"Initial belief base:\n{bb}")
    print(f"  Entails r? {entails(bb.get_formulas(), parse('r'))}")

    # Revise with ~r (contradicts the chain p -> q -> r)
    print("\nRevising with ~r...")
    bb_revised = revision(bb, parse("~r"), priority=2)
    print(f"Revised belief base:\n{bb_revised}")
    print(f"  Entails ~r? {entails(bb_revised.get_formulas(), parse('~r'))}")
    print(f"  Entails r?  {entails(bb_revised.get_formulas(), parse('r'))}")

    # ── Example 2: Expansion ──
    print("\n--- Example 2: Expansion ---")
    bb2 = BeliefBase()
    bb2.add(parse("sunny"), priority=2)
    bb2.add(parse("sunny >> warm"), priority=1)
    print(f"Initial:\n{bb2}")

    bb2_exp = expansion(bb2, parse("windy"), priority=1)
    print(f"After expanding with 'windy':\n{bb2_exp}")

    # ── Example 3: Contraction ──
    print("\n--- Example 3: Contraction ---")
    bb3 = BeliefBase()
    bb3.add(parse("a"), priority=3)
    bb3.add(parse("b"), priority=2)
    bb3.add(parse("a >> c"), priority=1)
    print(f"Initial:\n{bb3}")
    print(f"  Entails c? {entails(bb3.get_formulas(), parse('c'))}")

    bb3_cont = contraction(bb3, parse("c"))
    print(f"After contracting by 'c':\n{bb3_cont}")
    print(f"  Entails c? {entails(bb3_cont.get_formulas(), parse('c'))}")

    # ── Example 4: Handling contradictions ──
    print("\n--- Example 4: Handling Contradictions ---")
    bb4 = BeliefBase()
    bb4.add(parse("bird"), priority=3)
    bb4.add(parse("bird >> flies"), priority=2)
    print(f"Initial:\n{bb4}")
    print(f"  Entails flies? {entails(bb4.get_formulas(), parse('flies'))}")

    # Learn this bird is a penguin and doesn't fly
    bb4_rev = revision(bb4, parse("~flies"), priority=3)
    print(f"After revising with '~flies':\n{bb4_rev}")
    print(f"  Entails flies?  {entails(bb4_rev.get_formulas(), parse('flies'))}")
    print(f"  Entails ~flies? {entails(bb4_rev.get_formulas(), parse('~flies'))}")


def demo_mastermind():
    """Run an auto-play Mastermind demo."""
    print("\n" + "=" * 60)
    print("MASTERMIND — AUTO-PLAY DEMO")
    print("=" * 60)
    secret = random.sample(range(NUM_COLORS), NUM_POSITIONS)
    play_auto(secret)


def main():
    demo_belief_revision()

    print("\n")
    run_all_tests()

    demo_mastermind()

    print("\n" + "=" * 60)
    print("To play Mastermind interactively, run:")
    print("  python3 mastermind.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
