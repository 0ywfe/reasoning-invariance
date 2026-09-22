#!/usr/bin/env python3
"""Fire N variants at Jev via OpenRouter and track convergence.

Usage:
    python3 convergence.py "Your claim here"
    python3 convergence.py --n 500 "Your claim here"
    python3 convergence.py --state "context for the claim" "Your claim here"

Batches questions into groups of 20 per API call (output is free,
questions parallelise). Reports running median/spread at each batch
so you can see convergence in real time.
"""
from __future__ import annotations
import os, sys, json, time, argparse
import requests
from generator import generate_all, stats

API_URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
BATCH_SIZE = 20  # questions per call — output is free, so more = cheaper


def fire_batch(
    questions: list[tuple[str, str, bool]],
    state: str,
    api_key: str,
) -> list[tuple[str, float, bool]]:
    """Send a batch of questions to Jev. Returns [(label, score, inverts)]."""
    q_payload = {}
    meta = {}
    for label, text, inv in questions:
        safe_key = label.replace(".", "_")[:64]
        q_payload[safe_key] = {
            "type": "noul",
            "instructions": text,
        }
        meta[safe_key] = (label, inv)

    body = {
        "model": MODEL,
        "state": state,
        "questions": q_payload,
    }

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    answers = data.get("answers", {})
    cost = data.get("usage", {}).get("cost", 0)

    for key, ans in answers.items():
        label, inv = meta.get(key, (key, False))
        score = ans.get("noul", 0)
        results.append((label, score, inv))

    return results, cost


def run(claim: str, state: str, n: int, api_key: str, seed: int = 42):
    """Generate variants, fire at Jev in batches, report convergence."""
    print(f"Claim: {claim}")
    print(f"State: {state[:100]}{'...' if len(state) > 100 else ''}")
    print(f"Generating up to {n} variants...")

    variants = generate_all(claim, max_total=n, seed=seed)
    preserving = [v for v in variants if not v[2]]
    inverting = [v for v in variants if v[2]]
    print(f"Generated: {len(preserving)} preserving + {len(inverting)} inverting = {len(variants)} total")
    print()

    # fire preserving variants in batches, track convergence
    all_scores = []
    total_cost = 0
    total_calls = 0

    print(f"{'N':>6}  {'median':>7}  {'p10':>6}  {'p90':>6}  {'spread':>7}  {'std':>6}  {'cost':>10}  {'ms':>6}")
    print("-" * 75)

    for i in range(0, len(preserving), BATCH_SIZE):
        batch = preserving[i:i + BATCH_SIZE]
        t0 = time.time()
        try:
            results, cost = fire_batch(batch, state, api_key)
            elapsed = (time.time() - t0) * 1000
            total_cost += cost
            total_calls += 1

            for label, score, inv in results:
                all_scores.append(score)

            if len(all_scores) >= 3:
                s = stats(all_scores)
                print(f"{s['n']:>6}  {s['median']:>7.3f}  {s['p10']:>6.3f}  {s['p90']:>6.3f}  {s['spread']:>7.3f}  {s['std']:>6.3f}  ${total_cost:>9.6f}  {elapsed:>5.0f}")
        except Exception as e:
            print(f"  batch {i//BATCH_SIZE} error: {e}")
            time.sleep(2)

    print("-" * 75)

    # final preserving stats
    ps = stats(all_scores)
    print(f"\nPRESERVING (n={ps['n']}):")
    print(f"  median={ps['median']:.3f}  spread={ps['spread']:.3f}  std={ps['std']:.3f}")
    print(f"  range=[{ps['min']:.3f}, {ps['max']:.3f}]")

    # fire inverting variants
    inv_scores = []
    if inverting:
        print(f"\nFiring {len(inverting)} inverting variants...")
        for i in range(0, len(inverting), BATCH_SIZE):
            batch = inverting[i:i + BATCH_SIZE]
            try:
                results, cost = fire_batch(batch, state, api_key)
                total_cost += cost
                total_calls += 1
                for label, score, inv in results:
                    inv_scores.append(score)
            except Exception as e:
                print(f"  inverting batch error: {e}")

        if inv_scores:
            invs = stats(inv_scores)
            coherence = abs(ps['median'] + invs['median'] - 1)
            print(f"\nINVERTING (n={invs['n']}):")
            print(f"  median={invs['median']:.3f}  spread={invs['spread']:.3f}")
            print(f"  COHERENCE ERROR: |{ps['median']:.3f} + {invs['median']:.3f} - 1| = {coherence:.3f}")

    print(f"\nTotal: {total_calls} API calls, ${total_cost:.6f}")
    print(f"Verdict: {'SUPPORTED' if ps['median'] > 0.6 else 'UNSUPPORTED' if ps['median'] < 0.4 else 'INDETERMINATE'} at {ps['median']:.3f}, spread {ps['spread']:.3f}")

    # dump raw scores for analysis
    outfile = "convergence_scores.json"
    with open(outfile, "w") as f:
        json.dump({
            "claim": claim,
            "state": state,
            "preserving_scores": all_scores,
            "inverting_scores": inv_scores,
            "stats": ps,
            "total_cost": total_cost,
            "total_calls": total_calls,
        }, f, indent=2)
    print(f"Raw scores saved to {outfile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reasoning Invariance convergence test")
    parser.add_argument("claim", help="The proposition to test")
    parser.add_argument("--n", type=int, default=1000, help="Max variants (default 1000)")
    parser.add_argument("--state", default="", help="Context/evidence for the claim")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Set OPENROUTER_API_KEY in your environment")
        sys.exit(1)

    run(args.claim, args.state or args.claim, args.n, api_key, args.seed)
