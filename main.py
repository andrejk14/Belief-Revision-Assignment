from logic import parse
from belief_base import BeliefBase
from revision import expansion, contraction, revision
from resolution import entails
from agm_tests import run_all
from mastermind import play_auto, N_COL, N_POS
import random

def demos():
    print("=" * 55)
    print("BELIEF REVISION ENGINE")
    print("=" * 55)

    # implication chain: p->q->r, then revise by ~r
    print("\n-- Implication chain + revision --")
    bb = BeliefBase()
    bb.add(parse("p"), 3)
    bb.add(parse("p >> q"), 2)
    bb.add(parse("q >> r"), 1)
    print(bb)
    print(f"  entails r? {entails(bb.formulas(), parse('r'))}")

    bb2 = revision(bb, parse("~r"), 2)
    print("After revising by ~r:")
    print(bb2)
    print(f"  entails ~r? {entails(bb2.formulas(), parse('~r'))}")
    print(f"  entails r?  {entails(bb2.formulas(), parse('r'))}")

    # expansion
    print("\n-- Expansion --")
    bb3 = BeliefBase()
    bb3.add(parse("sunny"), 2)
    bb3.add(parse("sunny >> warm"), 1)
    print(bb3)
    bb4 = expansion(bb3, parse("windy"), 1)
    print("After expanding with windy:")
    print(bb4)

    # contraction
    print("\n-- Contraction --")
    bb5 = BeliefBase()
    bb5.add(parse("a"), 3)
    bb5.add(parse("b"), 2)
    bb5.add(parse("a >> c"), 1)
    print(bb5)
    print(f"  entails c? {entails(bb5.formulas(), parse('c'))}")

    bb6 = contraction(bb5, parse("c"))
    print("After contracting c:")
    print(bb6)
    print(f"  entails c? {entails(bb6.formulas(), parse('c'))}")

    # contradicting existing beliefs
    print("\n-- Handling contradictions --")
    bb7 = BeliefBase()
    bb7.add(parse("bird"), 3)
    bb7.add(parse("bird >> flies"), 2)
    print(bb7)
    print(f"  entails flies? {entails(bb7.formulas(), parse('flies'))}")

    bb8 = revision(bb7, parse("~flies"), 3)
    print("After revising by ~flies:")
    print(bb8)
    print(f"  entails flies?  {entails(bb8.formulas(), parse('flies'))}")
    print(f"  entails ~flies? {entails(bb8.formulas(), parse('~flies'))}")


def main():
    demos()

    print()
    run_all()

    print()
    print("=" * 55)
    print("MASTERMIND -- auto play")
    print("=" * 55)
    secret = random.sample(range(N_COL), N_POS)
    play_auto(secret)
    print("\n(run `python3 mastermind.py` for interactive mode)")

if __name__ == "__main__":
    main()
