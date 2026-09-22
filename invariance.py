#!/usr/bin/env python3
"""Reasoning Invariance — a calibrated committed number instead of an adjective.

Fans N genuine paraphrases of ONE proposition at a typed decision model in a single
call (output is free and questions parallelise, so N framings cost about the same as
one), then reports the median and the p10-p90 spread.

READ THE SPREAD BEFORE THE MEDIAN. A spread above 0.25 means the question was
ambiguous: rewrite it rather than averaging it. Measured separation between a
supported and an unsupported claim is ~0.6 (TRUE 0.800 / 0.765, FALSE 0.160 / 0.105).

    invariance.py claim.json              one proposition, DETERMINISTIC transforms
    invariance.py --paraphrases claim.json  hand-written paraphrases instead
    invariance.py --rank items.json       one question, N items, ranked

claim.json:
    {"state": {"claim": "...", "evidence": "..."},
     "paraphrases": ["...", "...", ...]}          # >= 12, GENUINE paraphrases

items.json — the re-examination form: when a measurement is corrected, rank what it
invalidates:
    {"state": {"correction": "..."},
     "questions": {"factual proposition A": null, "factual proposition B": null},
     "items": {"item-name": "the text of the banked verdict", ...}}
    -> each item is scored against every question; ranked by the product.

Requires OPENROUTER_API_KEY. Model served at /api/alpha/decisions (a decisions model;
/chat/completions rejects it).
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
import urllib.error
import urllib.request

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = os.environ.get("INVARIANCE_MODEL", "typesafe/jev-1.13")
SPREAD_GATE = float(os.environ.get("INVARIANCE_SPREAD_GATE", "0.25"))
MIN_PARAPHRASES = 12


def _call(state: dict, questions: dict) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set (it lives in ~/.zshrc; source it first)")
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(
        URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as fh:
            return json.load(fh)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:300]}")


def _pct(v: list[float], q: float) -> float:
    return sorted(v)[min(len(v) - 1, int(q * len(v)))]


def transformed(spec: dict) -> int:
    """Deterministic surface-form transforms. The LLM writes ONE proposition; the
    transforms are mechanical, so the spread measures the decision model's surface
    sensitivity rather than the LLM's rephrasing. Polarity-inverting transforms give
    a coherence check that needs no spread to read: p(X) + p(not X) should be 1."""
    import transforms
    claim = spec["state"].get("claim") or spec["claim"]
    tf = transforms.build(claim)
    r = _call(spec["state"], {f"t{i}": {"type": "noul", "instructions": t}
                              for i, (_, t, _) in enumerate(tf)})
    keep, inv = [], []
    for i, (name, text, inverts) in enumerate(tf):
        v = r["answers"][f"t{i}"]["noul"]
        (inv if inverts else keep).append((name, v))
        print(f"  {'INV ' if inverts else '    '}{v:5.3f}  {name:<18} {text[:72]}")
    vals = [v for _, v in keep]
    lo, hi = _pct(vals, 0.10), _pct(vals, 0.90)
    spread, med = hi - lo, st.median(vals)
    print(f"\n  polarity-preserving: median {med:.3f}  p10 {lo:.2f}  p90 {hi:.2f}"
          f"  spread {spread:.2f}   n={len(vals)}")
    if inv:
        ivals = [v for _, v in inv]
        imed = st.median(ivals)
        coh = abs(med + imed - 1.0)
        print(f"  polarity-inverting : median {imed:.3f}   "
              f"COHERENCE ERROR |p(X)+p(notX)-1| = {coh:.3f}")
        if coh > 0.20:
            print(f"  INCOHERENT — the model does not treat the negation as the negation. "
                  f"The reading is not about the proposition; it is about the surface.")
            return 3
    print(f"  {len(tf)} transforms, one call, ${r['usage']['cost']:.6f}")
    if spread > SPREAD_GATE:
        print(f"\n  SURFACE-SENSITIVE — spread {spread:.2f} > {SPREAD_GATE} across transforms "
              f"that cannot have changed the meaning.\n  The reading is fragile to form. Do not "
              f"act on the median.")
        return 2
    verdict = ("SUPPORTED" if med >= 0.65 else
               "UNSUPPORTED" if med <= 0.35 else "INDETERMINATE")
    print(f"\n  {verdict} — median {med:.3f}, invariant to surface form (spread {spread:.2f}).")
    return 0


def invariance(spec: dict) -> int:
    ph = spec["paraphrases"]
    if len(ph) < MIN_PARAPHRASES:
        print(f"WARNING only {len(ph)} paraphrases; {MIN_PARAPHRASES}+ makes the spread "
              f"meaningful. Reporting anyway.\n")
    r = _call(spec["state"], {f"p{i}": {"type": "noul", "instructions": t}
                              for i, t in enumerate(ph)})
    vals = [r["answers"][f"p{i}"]["noul"] for i in range(len(ph))]
    lo, hi = _pct(vals, 0.10), _pct(vals, 0.90)
    spread, med = hi - lo, st.median(vals)

    for t, v in sorted(zip(ph, vals), key=lambda x: -x[1]):
        print(f"  {v:5.3f}  {t[:96]}")
    print(f"\n  median {med:.3f}   p10 {lo:.2f}   p90 {hi:.2f}   spread {spread:.2f}"
          f"   min {min(vals):.2f}   max {max(vals):.2f}")
    print(f"  {len(ph)} framings, one call, ${r['usage']['cost']:.6f}")

    if spread > SPREAD_GATE:
        print(f"\n  AMBIGUOUS — spread {spread:.2f} > {SPREAD_GATE}. The QUESTION is the "
              f"problem, not the answer.\n  Rewrite the paraphrases so they state the same "
              f"proposition, then re-run. Do NOT act on the median.")
        return 2
    verdict = ("SUPPORTED" if med >= 0.65 else
               "UNSUPPORTED" if med <= 0.35 else "INDETERMINATE")
    print(f"\n  {verdict} — median {med:.3f}, stable across framings (spread {spread:.2f}).")
    if verdict == "INDETERMINATE":
        print("  The claim is stably mid. That is a real answer: the evidence does not decide "
              "it.\n  Name the measurement that would, and run that instead.")
    return 0


def rank(spec: dict) -> int:
    qs = {k: {"type": "noul", "instructions": k} for k in spec["questions"]}
    rows, cost = [], 0.0
    for name, text in spec["items"].items():
        state = dict(spec["state"]); state["item"] = text
        r = _call(state, qs)
        v = {k: r["answers"][k]["noul"] for k in qs}
        prod = 1.0
        for x in v.values():
            prod *= x
        rows.append((name, v, prod)); cost += r["usage"]["cost"]
    rows.sort(key=lambda x: -x[2])
    keys = list(qs)
    print("  " + "item".ljust(26) + "".join(k[:18].rjust(20) for k in keys) + "product".rjust(10))
    for name, v, prod in rows:
        print("  " + name[:26].ljust(26) + "".join(f"{v[k]:>20.2f}" for k in keys)
              + f"{prod:>10.3f}")
    print(f"\n  {len(rows)} items x {len(keys)} questions, ${cost:.5f}")
    print("  Top of the list is where to look first. It is a ranking, not a verdict.")
    return 0


if __name__ == "__main__":
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    spec = json.load(open(args[0]))
    if "--rank" in flags:
        sys.exit(rank(spec))
    sys.exit(invariance(spec) if "--paraphrases" in flags else transformed(spec))
