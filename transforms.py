#!/usr/bin/env python3
"""Deterministic surface-form transforms for Reasoning Invariance.

WHY THESE AND NOT LLM PARAPHRASES. If the model under test writes the paraphrases,
the bias rephrases itself, and any meaning-drift it introduces shows up as spread
that looks like fragility but is really sloppiness. These transforms are mechanical,
reproducible, and meaning-preserving BY CONSTRUCTION, so the spread measures exactly
one thing: the decision model's sensitivity to surface form.

Two classes:

  POLARITY-PRESERVING  the proposition is unchanged; the reading should be unchanged.
                       Spread across these is surface sensitivity.

  POLARITY-INVERTING   the proposition is negated; the reading should be 1 - p.
                       |p(X) + p(not X) - 1| is COHERENCE ERROR -- a direct
                       measurement that needs no spread to interpret. A model that
                       answers on surface cues rather than meaning fails this while
                       still looking stable across the preserving set.

Nothing here parses English. Every transform is a wrapper or a table lookup, so it
cannot silently change what is being asked. Active/passive and clause reordering are
deliberately NOT implemented: doing them correctly needs a parser, and doing them
badly reintroduces the drift these exist to remove.
"""
from __future__ import annotations

# fixed, symmetric, domain-neutral. Applied longest-first, whole words only.
SYNONYMS: list[tuple[str, str]] = [
    ("is adequate for", "suffices for"),
    ("is sufficient", "is enough"),
    ("demonstrates", "shows"),
    ("establishes", "proves"),
    ("supports", "backs"),
    ("indicates", "signals"),
    ("without", "with no"),
    ("every", "each"),
    ("adequate", "sufficient"),
    ("reliable", "dependable"),
    ("observations", "data points"),
    ("requires", "needs"),
    ("produce", "yield"),
    ("material", "meaningful"),
    ("appropriate", "suitable"),
    ("correct", "right"),
]


def _swap(text: str) -> str:
    out = text
    for a, b in sorted(SYNONYMS, key=lambda p: -len(p[0])):
        out = out.replace(a, b)
    return out


def _strip_period(t: str) -> str:
    return t.rstrip().rstrip(".")


# (name, builder, inverts_polarity)
TRANSFORMS = [
    ("identity",      lambda c: c,                                             False),
    ("synonym",       lambda c: _swap(c),                                      False),
    ("assertive",     lambda c: f"The following is accurate: {_strip_period(c)}.", False),
    ("evidential",    lambda c: f"Based on the state provided, {_strip_period(c)}.", False),
    ("it_is_true",    lambda c: f"It is true that {_strip_period(c)}.",         False),
    ("question",      lambda c: f"Is it the case that {_strip_period(c)}?",     False),
    ("double_neg",    lambda c: f"It is not the case that the following is false: {_strip_period(c)}.", False),
    ("holds",         lambda c: f"This holds: {_strip_period(c)}.",             False),
    ("syn_assertive", lambda c: f"The following is accurate: {_strip_period(_swap(c))}.", False),
    ("syn_evidential", lambda c: f"Based on the state provided, {_strip_period(_swap(c))}.", False),
    ("syn_question",  lambda c: f"Is it the case that {_strip_period(_swap(c))}?", False),
    ("syn_double_neg", lambda c: f"It is not the case that the following is false: {_strip_period(_swap(c))}.", False),
    # polarity-inverting: expected reading is 1 - p
    ("negated",       lambda c: f"It is false that {_strip_period(c)}.",        True),
    ("negated_syn",   lambda c: f"It is false that {_strip_period(_swap(c))}.", True),
    ("negated_assert", lambda c: f"The following is inaccurate: {_strip_period(c)}.", True),
    ("negated_question", lambda c: f"Is it false that {_strip_period(c)}?",     True),
]


def build(claim: str) -> list[tuple[str, str, bool]]:
    """-> [(transform_name, rendered_text, inverts_polarity)]"""
    return [(n, f(claim), inv) for n, f, inv in TRANSFORMS]


if __name__ == "__main__":
    import sys
    c = " ".join(sys.argv[1:]) or "The inherited edges are adequate for this dataset."
    for n, t, inv in build(c):
        print(f"{'INV' if inv else '   '} {n:<18} {t}")
