#!/usr/bin/env python3
"""Systematic question generation for Reasoning Invariance.

Transforms give SURFACE invariance on one proposition. They do not give BREADTH.
Four questions dressed in sixteen wordings is still four questions, and the whole
argument for a cheap decision model is that you stop choosing which question to ask.

So questions are generated the same way the transforms are: mechanically, by crossing
a fixed predicate grammar against the subjects the state itself names. The agent
writes NO questions. It writes the subject list -- the components, thresholds, risks
and quantities its own state contains -- and the bank produces the cross product.

    predicates x subjects  ->  N distinct propositions
    each proposition       ->  16 deterministic transforms
    N x 16                 ->  the judgments

Every predicate is a concrete factual proposition about the state, never a question
about whether the reasoning is sound -- the measured rule that makes this work at all
(abstract framings rank backwards; factual ones separate 0.94 vs 0.38/0.42).
"""
from __future__ import annotations

# Each predicate takes one subject. Concrete, factual, single-clause.
PREDICATES: list[str] = [
    "The state contains a measured value for {s} under this configuration.",
    "{s} has been measured on more than one independent draw.",
    "{s} was derived from measured data rather than chosen by a person.",
    "The state reports a confidence interval for {s}.",
    "{s} has been measured on this venue's own recorded tape.",
    "The value of {s} would change if the wallet size changed.",
    "{s} is a quantity the running production code already computes.",
    "This configuration makes {s} larger than the flat-15 baseline does.",
    "This configuration makes {s} smaller than the flat-15 baseline does.",
    "An error in {s} would invalidate this configuration's headline result.",
    "{s} is held fixed across every arm the state describes.",
    "The state's evidence for {s} comes from a single draw only.",
    "{s} can be computed from the logs that already exist.",
    "Deploying this configuration requires {s} to be re-measured first.",
    "{s} is a constant that was fitted on a different population.",
]

# Relations between a configuration and the whole record, subject-free.
GLOBAL: list[str] = [
    "Every component of this configuration has been measured on this tape.",
    "This configuration has been run end to end at least once.",
    "This configuration's result has reproduced on a second independent draw.",
    "The measurements support this configuration closing more capital than it strands.",
    "The measurements support this configuration reaching a grade of 1.40 or above.",
    "The measurements support this configuration beating the flat-15 baseline.",
    "This configuration deploys more capital at once than the flat-15 baseline.",
    "This configuration would strand more capital in absolute terms than the baseline.",
    "This configuration contains a threshold that no measurement in the state justifies.",
    "This configuration contains a component that has never been fitted on this tape.",
    "This configuration can be run without fitting anything new.",
    "This configuration's expected result is already known from the state.",
    "A failure of this configuration would be visible in the grade the state reports.",
    "This configuration exposes the wallet to a loss the state has not measured.",
    "The state contains a measurement that directly contradicts this configuration.",
]


def build(subjects: list[str]) -> list[str]:
    """subjects -> the full cross product plus the global relations."""
    qs = [p.format(s=s) for s in subjects for p in PREDICATES]
    return qs + list(GLOBAL)


def batches(qs: list[str], per: int = 28):
    for i in range(0, len(qs), per):
        yield qs[i:i + per]


if __name__ == "__main__":
    import sys
    subs = sys.argv[1:] or ["the lot size", "the strand rate"]
    qs = build(subs)
    print(f"{len(subs)} subjects x {len(PREDICATES)} predicates + {len(GLOBAL)} global "
          f"= {len(qs)} distinct questions")
    print(f"x 16 transforms = {len(qs)*16} judgments")
    for q in qs[:6]:
        print("   ", q)


# Caveat FRAMES — structural, not lexical. A hedge-word scan misses these entirely:
# "one flag", "worth noting", "the honest limit" contain no hedge vocabulary. Measured
# 2026-09-22 across 4,824 assistant turns: 139 frame hits, 0.029/turn, and 36 of them
# in the single session where the tool that removes them was being built.
CAVEAT_FRAMES = [
    "one flag", "one thing i'd flag", "one caveat", "one correction", "one boundary",
    "one limit", "worth noting", "worth being straight", "worth flagging",
    "the honest limit", "the honest caveat", "the honest version", "i'd flag",
    "to be clear,", "that said,", "for completeness", "i want on the record",
    "stated now rather than", "before it becomes a headline",
]


def caveat_frames(text: str) -> list[str]:
    """Frames present in a draft. Each one is a claim that has not been scored --
    either run it through the panel or delete the sentence."""
    low = text.lower()
    return [f for f in CAVEAT_FRAMES if f in low]
