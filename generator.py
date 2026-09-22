#!/usr/bin/env python3
"""Reasoning Invariance — N=1000+ paraphrase generator.

Three layers that compose multiplicatively:

  Layer 1: SYNONYM TABLES — 50+ domain-neutral swaps applied combinatorially.
           With 50 pairs, each independently on/off on applicable words,
           the number of lexical variants is 2^(matches) per sentence.

  Layer 2: SYNTACTIC FRAMES — 30+ templates that wrap the proposition
           without changing it. "It is the case that [X]", "[X], which holds",
           "The claim [X] is established", etc.

  Layer 3: COMPOSITIONS — Layer 1 × Layer 2. Every synonym variant × every
           frame. If a sentence hits 5 synonym pairs, that's 2^5 × 30 = 960
           preserving variants from two layers alone.

  Layer 4: POLARITY INVERSION — negate each variant for the coherence check.

  Validity filter: optional Jev call per variant to confirm meaning preservation.
  Without it, validity is guaranteed by construction (wrappers + table lookups).

  Evidence bootstrap: random 80% subsets of state, same question, tests whether
  the answer depends on everything shown or one lucky fact.
"""
from __future__ import annotations
import itertools
import random
from typing import Optional


# ──────────────────────────────────────────────────────────────────────
# LAYER 1: Expanded synonym table — domain-neutral, symmetric
# ──────────────────────────────────────────────────────────────────────
SYNONYMS: list[tuple[str, str]] = [
    # verbs
    ("demonstrates", "shows"),
    ("establishes", "proves"),
    ("supports", "backs"),
    ("indicates", "signals"),
    ("requires", "needs"),
    ("produces", "yields"),
    ("contains", "includes"),
    ("reveals", "exposes"),
    ("suggests", "implies"),
    ("confirms", "verifies"),
    ("predicts", "forecasts"),
    ("exceeds", "surpasses"),
    ("reduces", "lowers"),
    ("increases", "raises"),
    ("maintains", "preserves"),
    ("determines", "decides"),
    ("achieves", "attains"),
    ("prevents", "blocks"),
    ("causes", "triggers"),
    ("enables", "allows"),
    # adjectives / adverbs
    ("adequate", "sufficient"),
    ("reliable", "dependable"),
    ("significant", "substantial"),
    ("appropriate", "suitable"),
    ("correct", "right"),
    ("primary", "main"),
    ("robust", "resilient"),
    ("consistent", "stable"),
    ("identical", "equivalent"),
    ("independent", "separate"),
    ("critical", "crucial"),
    ("rapid", "fast"),
    ("approximately", "roughly"),
    ("entirely", "completely"),
    ("precisely", "exactly"),
    # nouns
    ("observations", "data points"),
    ("evidence", "proof"),
    ("outcome", "result"),
    ("method", "approach"),
    ("factor", "variable"),
    ("component", "element"),
    ("threshold", "cutoff"),
    ("distribution", "spread"),
    ("mechanism", "process"),
    ("constraint", "limitation"),
    # phrases
    ("is adequate for", "suffices for"),
    ("is sufficient", "is enough"),
    ("without", "with no"),
    ("every", "each"),
    ("however", "nonetheless"),
    ("therefore", "consequently"),
]


# ──────────────────────────────────────────────────────────────────────
# LAYER 2: Syntactic frames — wrappers that don't touch the proposition
# ──────────────────────────────────────────────────────────────────────
def _strip(t: str) -> str:
    return t.rstrip().rstrip(".").rstrip()


PRESERVING_FRAMES: list[tuple[str, callable]] = [
    ("identity",         lambda c: c),
    ("it_is_true",       lambda c: f"It is true that {_strip(c)}."),
    ("assertive",        lambda c: f"The following is accurate: {_strip(c)}."),
    ("evidential",       lambda c: f"Based on the state provided, {_strip(c)}."),
    ("holds",            lambda c: f"This holds: {_strip(c)}."),
    ("question",         lambda c: f"Is it the case that {_strip(c)}?"),
    ("claim",            lambda c: f"The claim that {_strip(c)} is warranted."),
    ("observe",          lambda c: f"One observes that {_strip(c)}."),
    ("established",      lambda c: f"It has been established that {_strip(c)}."),
    ("note",             lambda c: f"Note that {_strip(c)}."),
    ("given",            lambda c: f"Given the evidence, {_strip(c)}."),
    ("conclude",         lambda c: f"We conclude that {_strip(c)}."),
    ("confirmed",        lambda c: f"It is confirmed that {_strip(c)}."),
    ("verified",         lambda c: f"It has been verified that {_strip(c)}."),
    ("supported",        lambda c: f"The data supports that {_strip(c)}."),
    ("evident",          lambda c: f"It is evident that {_strip(c)}."),
    ("clear",            lambda c: f"It is clear that {_strip(c)}."),
    ("shown",            lambda c: f"It has been shown that {_strip(c)}."),
    ("accepted",         lambda c: f"It is accepted that {_strip(c)}."),
    ("understood",       lambda c: f"It is understood that {_strip(c)}."),
    ("apparent",         lambda c: f"It is apparent that {_strip(c)}."),
    ("double_neg",       lambda c: f"It is not the case that the following is false: {_strip(c)}."),
    ("not_untrue",       lambda c: f"It is not untrue that {_strip(c)}."),
    ("would_agree",      lambda c: f"One would agree that {_strip(c)}."),
    ("fair_to_say",      lambda c: f"It is fair to say that {_strip(c)}."),
    ("stands_that",      lambda c: f"It stands that {_strip(c)}."),
    ("remains_that",     lambda c: f"It remains the case that {_strip(c)}."),
    ("follows_that",     lambda c: f"It follows that {_strip(c)}."),
    ("determined",       lambda c: f"It has been determined that {_strip(c)}."),
    ("can_be_stated",    lambda c: f"It can be stated that {_strip(c)}."),
]

INVERTING_FRAMES: list[tuple[str, callable]] = [
    ("negated",          lambda c: f"It is false that {_strip(c)}."),
    ("inaccurate",       lambda c: f"The following is inaccurate: {_strip(c)}."),
    ("neg_question",     lambda c: f"Is it false that {_strip(c)}?"),
    ("denied",           lambda c: f"It is denied that {_strip(c)}."),
    ("not_the_case",     lambda c: f"It is not the case that {_strip(c)}."),
    ("incorrect",        lambda c: f"It is incorrect that {_strip(c)}."),
    ("unfounded",        lambda c: f"The claim that {_strip(c)} is unfounded."),
    ("contradicted",     lambda c: f"The evidence contradicts that {_strip(c)}."),
]


# ──────────────────────────────────────────────────────────────────────
# LAYER 1 ENGINE: combinatorial synonym application
# ──────────────────────────────────────────────────────────────────────
def _find_applicable_synonyms(text: str) -> list[tuple[str, str]]:
    """Find which synonym pairs have at least one direction present in text."""
    applicable = []
    lower = text.lower()
    for a, b in SYNONYMS:
        if a.lower() in lower or b.lower() in lower:
            applicable.append((a, b))
    return applicable


def _apply_synonym_combo(text: str, combo: tuple[bool, ...],
                         applicable: list[tuple[str, str]]) -> str:
    """Apply a specific combination of synonym swaps."""
    out = text
    for swap, (a, b) in zip(combo, applicable):
        if swap:
            if a in out:
                out = out.replace(a, b, 1)
            elif b in out:
                out = out.replace(b, a, 1)
    return out


def generate_synonym_variants(text: str, max_variants: int = 64) -> list[str]:
    """Generate all combinatorial synonym variants, capped at max_variants."""
    applicable = _find_applicable_synonyms(text)
    if not applicable:
        return [text]

    n = len(applicable)
    if 2**n <= max_variants:
        combos = list(itertools.product([False, True], repeat=n))
    else:
        combos = set()
        combos.add(tuple([False] * n))
        while len(combos) < max_variants:
            combos.add(tuple(random.choice([True, False]) for _ in range(n)))
        combos = list(combos)

    variants = []
    seen = set()
    for combo in combos:
        v = _apply_synonym_combo(text, combo, applicable)
        if v not in seen:
            seen.add(v)
            variants.append(v)
    return variants


# ──────────────────────────────────────────────────────────────────────
# COMPOSER: Layer 1 × Layer 2 = N=1000+
# ──────────────────────────────────────────────────────────────────────
def generate_all(
    claim: str,
    max_total: int = 2000,
    include_inverting: bool = True,
    seed: Optional[int] = None,
) -> list[tuple[str, str, bool]]:
    """Generate up to max_total variants of a claim.

    Returns: [(label, rendered_text, inverts_polarity), ...]
    """
    if seed is not None:
        random.seed(seed)

    syn_variants = generate_synonym_variants(claim, max_variants=64)

    preserving = []
    for si, sv in enumerate(syn_variants):
        for fname, ffunc in PRESERVING_FRAMES:
            label = f"syn_{si:02d}__{fname}"
            rendered = ffunc(sv)
            preserving.append((label, rendered, False))

    inverting = []
    if include_inverting:
        for si, sv in enumerate(syn_variants[:8]):
            for fname, ffunc in INVERTING_FRAMES:
                label = f"syn_{si:02d}__inv_{fname}"
                rendered = ffunc(sv)
                inverting.append((label, rendered, True))

    all_variants = preserving + inverting

    seen = set()
    deduped = []
    for label, text, inv in all_variants:
        if text not in seen:
            seen.add(text)
            deduped.append((label, text, inv))

    inv_set = [x for x in deduped if x[2]]
    pres_set = [x for x in deduped if not x[2]]

    if len(deduped) > max_total:
        keep_pres = max_total - len(inv_set)
        random.shuffle(pres_set)
        pres_set = pres_set[:keep_pres]
        deduped = pres_set + inv_set

    return deduped


# ──────────────────────────────────────────────────────────────────────
# EVIDENCE BOOTSTRAP: random 80% subsets of state
# ──────────────────────────────────────────────────────────────────────
def bootstrap_state(
    state_facts: list[str],
    n_samples: int = 100,
    keep_fraction: float = 0.8,
    seed: Optional[int] = None,
) -> list[list[str]]:
    """Generate n_samples random subsets of state facts.

    Each subset keeps keep_fraction of the facts, randomly selected.
    Returns list of fact-lists, each a valid state to send to Jev.
    """
    if seed is not None:
        random.seed(seed)

    k = max(1, int(len(state_facts) * keep_fraction))
    samples = []
    for _ in range(n_samples):
        subset = random.sample(state_facts, k)
        samples.append(subset)
    return samples


# ──────────────────────────────────────────────────────────────────────
# STATS
# ──────────────────────────────────────────────────────────────────────
def stats(scores: list[float]) -> dict:
    """Compute median, p10, p90, spread, mean, std."""
    s = sorted(scores)
    n = len(s)
    return {
        "n": n,
        "median": s[n // 2],
        "p10": s[int(n * 0.1)],
        "p90": s[int(n * 0.9)],
        "spread": s[int(n * 0.9)] - s[int(n * 0.1)],
        "mean": sum(s) / n,
        "std": (sum((x - sum(s)/n)**2 for x in s) / n) ** 0.5,
        "min": s[0],
        "max": s[-1],
    }


if __name__ == "__main__":
    import sys

    claim = " ".join(sys.argv[1:]) or "The evidence demonstrates that this reliable method produces significant observations without requiring additional constraints."

    variants = generate_all(claim, max_total=2000, seed=42)

    preserving = [v for v in variants if not v[2]]
    inverting = [v for v in variants if v[2]]

    print(f"Claim: {claim}")
    print(f"Total variants: {len(variants)}")
    print(f"  Preserving: {len(preserving)}")
    print(f"  Inverting:  {len(inverting)}")
    print()

    print("--- Sample preserving variants ---")
    for label, text, _ in preserving[:10]:
        print(f"  {label:<30} {text[:90]}")
    print(f"  ... and {len(preserving) - 10} more")
    print()
    print("--- Sample inverting variants ---")
    for label, text, _ in inverting[:5]:
        print(f"  {label:<30} {text[:90]}")
    print(f"  ... and {len(inverting) - 5} more")

    applicable = _find_applicable_synonyms(claim)
    print(f"\nSynonym pairs matched: {len(applicable)}")
    for a, b in applicable:
        print(f"  {a} <-> {b}")
    print(f"Lexical variants: 2^{len(applicable)} = {2**len(applicable)}")
    print(f"x {len(PRESERVING_FRAMES)} frames = {2**len(applicable) * len(PRESERVING_FRAMES)} theoretical max")
