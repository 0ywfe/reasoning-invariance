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
import math
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
    """Rank items against questions, with EVERY question invarianced.

    A single phrasing per question is not a measurement -- it is one reading, which
    is the thing this tool exists to refuse. Each question is expanded through the
    same deterministic transforms as the single-claim path, so every cell carries a
    median, a spread and a coherence error. A cell whose question is surface-sensitive
    or incoherent is reported and EXCLUDED from the product rather than silently
    ranked on."""
    import transforms
    qtexts = list(spec["questions"])
    rows, cost, flagged = [], 0.0, []
    for name, text in spec["items"].items():
        state = dict(spec["state"]); state["item"] = text
        qs, meta = {}, {}
        for qi, qt in enumerate(qtexts):
            for ti, (tn, rendered, inv) in enumerate(transforms.build(qt)):
                key = f"q{qi}t{ti}"
                qs[key] = {"type": "noul", "instructions": rendered}
                meta[key] = (qi, inv)
        r = _call(state, qs); cost += r["usage"]["cost"]
        cell = {}
        for qi in range(len(qtexts)):
            keep = [r["answers"][k]["noul"] for k, (q, inv) in meta.items() if q == qi and not inv]
            invs = [r["answers"][k]["noul"] for k, (q, inv) in meta.items() if q == qi and inv]
            med = st.median(keep); spread = _pct(keep, 0.90) - _pct(keep, 0.10)
            coh = abs(med + st.median(invs) - 1.0) if invs else 0.0
            ok = spread <= SPREAD_GATE and coh <= 0.20
            if not ok:
                flagged.append((name, qtexts[qi], med, spread, coh))
            cell[qi] = (med, spread, coh, ok)
        kept = [cell[qi][0] for qi in range(len(qtexts)) if cell[qi][3]]
        # GEOMETRIC MEAN, not product: excluded cells leave items with different
        # factor counts, and a raw product rewards an item for having had a
        # question thrown out.
        prod = (math.prod(kept) ** (1.0 / len(kept))) if kept else float("nan")
        rows.append((name, cell, prod))
    rows.sort(key=lambda x: -x[2])
    print("  " + "item".ljust(26) + "".join(f"q{i}  med/sprd/coh".rjust(22)
                                            for i in range(len(qtexts))) + "geomean".rjust(9))
    for name, cell, prod in rows:
        line = "  " + name[:26].ljust(26)
        for qi in range(len(qtexts)):
            m, sp, co, ok = cell[qi]
            line += f"{m:.2f}/{sp:.2f}/{co:.2f}{'' if ok else '!'}".rjust(22)
        print(line + f"{prod:>9.3f}")
    for i, q in enumerate(qtexts):
        print(f"  q{i}: {q}")
    if flagged:
        print(f"\n  {len(flagged)} cell(s) EXCLUDED from the product — question was "
              f"surface-sensitive or incoherent for that item:")
        for n, q, m, sp, co in flagged[:8]:
            print(f"    {n[:22]:<22} spread {sp:.2f} coh {co:.2f}  {q[:60]}")
    print(f"\n  {len(rows)} items x {len(qtexts)} questions x "
          f"{len(transforms.TRANSFORMS)} transforms = "
          f"{len(rows)*len(qtexts)*len(transforms.TRANSFORMS)} judgments, ${cost:.5f}")
    return 0


def bank(spec: dict) -> int:
    """The full cross: generated questions x deterministic transforms, per item.

    The agent writes the subject list and the state. It writes no questions: those
    are the predicate grammar crossed against the subjects, so breadth is mechanical
    and cannot carry the agent's framing."""
    import transforms, questionbank
    qs_all = questionbank.build(spec["subjects"])
    tf_n = len(transforms.TRANSFORMS)
    print(f"  {len(spec['subjects'])} subjects -> {len(qs_all)} distinct questions "
          f"x {tf_n} transforms = {len(qs_all)*tf_n} judgments per item, "
          f"{len(qs_all)*tf_n*len(spec['items'])} total\n")
    rows, cost = [], 0.0
    percell = {}
    for name, text in spec["items"].items():
        state = dict(spec["state"]); state["configuration"] = text
        keep_med, dropped = [], 0
        for batch in questionbank.batches(qs_all):
            qs, meta = {}, {}
            for qi, qt in enumerate(batch):
                for ti, (_, rendered, inv) in enumerate(transforms.build(qt)):
                    k = f"q{qi}t{ti}"; qs[k] = {"type": "noul", "instructions": rendered}
                    meta[k] = (qi, inv)
            r = _call(state, qs); cost += r["usage"]["cost"]
            for qi, qt in enumerate(batch):
                pres = [r["answers"][k]["noul"] for k, (q, i) in meta.items() if q == qi and not i]
                invs = [r["answers"][k]["noul"] for k, (q, i) in meta.items() if q == qi and i]
                med = st.median(pres); spread = _pct(pres, 0.90) - _pct(pres, 0.10)
                coh = abs(med + st.median(invs) - 1.0) if invs else 0.0
                if spread <= SPREAD_GATE and coh <= 0.20:
                    keep_med.append(med); percell.setdefault(qt, {})[name] = med
                else:
                    dropped += 1
        gm = (math.prod(keep_med) ** (1.0 / len(keep_med))) if keep_med else float("nan")
        rows.append((name, gm, len(keep_med), dropped))
        print(f"  {name[:30]:<30} geomean {gm:.4f}   usable {len(keep_med):>3}/{len(qs_all)}"
              f"   dropped {dropped}")
    json.dump({q: v for q, v in percell.items()}, open("/tmp/invariance_matrix.json", "w"))
    rows.sort(key=lambda x: -x[1])
    print(f"\n  ALL QUESTIONS (geometric mean) — expect this to be FLAT: most questions")
    print(f"  do not discriminate, and averaging them washes out the ones that do.")
    for n, gm, k, d in rows:
        print(f"    {n[:34]:<34} {gm:.4f}   on {k} usable questions")

    # Rank on the questions that SEPARATE. The cut is the gap distribution's own
    # top decile -- derived from the data, not chosen.
    gaps = []
    for q, per in percell.items():
        if len(per) == len(spec["items"]):
            v = list(per.values()); gaps.append((max(v) - min(v), q, per))
    gaps.sort(reverse=True)
    if gaps:
        cut = gaps[max(0, int(0.10 * len(gaps)))][0]
        sel = [(g, q, per) for g, q, per in gaps if g >= cut]
        print(f"\n  DISCRIMINATING SUBSET: {len(sel)} of {len(gaps)} questions with gap >= "
              f"{cut:.2f} (the gap distribution's own top decile)")
        srow = []
        for name in spec["items"]:
            vals = [per[name] for _, _, per in sel]
            srow.append((name, math.prod(vals) ** (1.0 / len(vals))))
        srow.sort(key=lambda x: -x[1])
        print(f"  RANKED on the subset that actually separates:")
        for n, gm in srow:
            print(f"    {n[:34]:<34} {gm:.4f}")
    disc = []
    for q, per in percell.items():
        if len(per) >= len(spec["items"]) - 1:
            v = list(per.values()); disc.append((max(v) - min(v), q, per))
    disc.sort(reverse=True)
    print(f"\n  MOST DISCRIMINATING QUESTIONS (widest spread across configurations)")
    for gap, q, per in disc[:6]:
        top = max(per, key=per.get); bot = min(per, key=per.get)
        print(f"    gap {gap:.2f}  {q[:76]}")
        print(f"              high {top[:26]} {per[top]:.2f} | low {bot[:26]} {per[bot]:.2f}")
    print(f"\n  ${cost:.4f}")
    return 0


if __name__ == "__main__":
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    spec = json.load(open(args[0]))
    if "--bank" in flags:
        sys.exit(bank(spec))
    if "--rank" in flags:
        sys.exit(rank(spec))
    sys.exit(invariance(spec) if "--paraphrases" in flags else transformed(spec))
