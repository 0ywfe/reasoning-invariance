# Provenance

Findings produced in two sessions (2026-09-22/23, 2026-09-25/26) using
the OpenRouter API (Jev 1.13) and local Laya inference.

## Session 1: Discovery and method (2026-09-22/23)

- Jev discovered and first API call
- TruthfulQA misconceptions (10/10), reasoning fallacies (8/8),
  academic benchmarks (6/6)
- Phrasing premium discovered; deterministic transforms built
- Evidence invariance: load-bearing facts, interaction effects
- Parameter sweep: 5/5 correct peaks on known constants
- State-vs-prior boundary mapped
- Reasoning Graph v1 and v2 with self-routing
- Best-of-N, majority voting, evidence MCTS tested
- HLE dataset accessed; graduate math scored indeterminate
  (correct calibration)

## Session 2: Laya comparison (2026-09-25/26)

- Laya installed locally (`pip install laya`)
- MPS backend confirmed on M4 MacBook Pro
- Hot latency: 47ms per call, free
- Misconception benchmark: Laya 9/10 vs Jev 10/10
  (lightning claim scored 0.451 on Laya vs 0.08 on Jev —
  ambiguous claim, different error profiles)
- Laya adopted as default backend

## Reproducibility

Jev calls reproducible with model version `typesafe/jev-1.13-20260917`
and identical state/instructions. Near-deterministic (σ=0.004).

Laya calls reproducible with `convaiinnovations/laya` checkpoints
and identical state/questions. Deterministic on same hardware.

## Costs

Session 1 (Jev API): < $0.10 across ~300 calls.
Session 2 (Laya local): $0.00.
