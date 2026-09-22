#!/usr/bin/env python3
"""Reasoning Invariance — a calibrated committed number instead of an adjective.

Fans N genuine paraphrases of ONE proposition at a typed decision model in a single
call (output is free and questions parallelise, so N framings cost about the same as
one), then reports the median and the p10-p90 spread.

READ THE SPREAD BEFORE THE MEDIAN. A spread above 0.25 means the question was
ambiguous: rewrite it rather than averaging it. Measured separation between a
supported and an unsupported claim is ~0.6 (TRUE 0.800 / 0.765, FALSE 0.160 / 0.105).

    invariance.py claim.json              one proposition, N paraphrases
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
    args = [a for a in sys.argv[1:] if a != "--rank"]
    if not args:
        sys.exit(__doc__)
    spec = json.load(open(args[0]))
    sys.exit(rank(spec) if "--rank" in sys.argv[1:] else invariance(spec))
