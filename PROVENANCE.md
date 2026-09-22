# Reasoning Invariance — Provenance

All findings in this study were produced live in a single
session (2026-09-22/23) by Ethan (0ywfe) in conversation
with Claude, using the OpenRouter API to access TypeSafe AI's
Jev 1.13 model.

## Timeline

- 2026-09-22 ~21:00 UTC: Session begins. Jev discovered via
  web search. First API call.
- 2026-09-22 ~22:00: TruthfulQA misconceptions (10/10),
  reasoning fallacies (8/8), academic benchmarks (6/6).
- 2026-09-22 ~23:00: Phrasing premium discovered. Deterministic
  transforms replace LLM paraphrases.
- 2026-09-23 ~00:00: Evidence invariance invented. Load-bearing
  facts identified. Interaction effects measured.
- 2026-09-23 ~01:00: Parameter sweep invented. 5/5 correct
  peaks on known constants. Startup prior extracted (6/10).
- 2026-09-23 ~02:00: State-vs-prior boundary mapped. Novel
  domains = pure state reading. Known domains = state must
  overcome prior.
- 2026-09-23 ~03:00: Real error caught on #646 (size-plane
  edges). Correction posted.
- 2026-09-23 ~04:00: Reasoning Graph v1 built and pushed.
- 2026-09-23 ~05:00: All three inference techniques tested
  (best-of-N, majority voting, evidence MCTS).
- 2026-09-23 ~06:00: Reasoning Graph v2 with all three
  primitives and self-routing. Bug fixes (route memory,
  invariance always runs).
- 2026-09-23 ~07:00: HLE dataset accessed. Graduate math
  scored indeterminate (correct calibration). HLE-style
  knowledge verification (paired claims).
- 2026-09-23 ~08:00: Applied to 91 CPCV batteries. Grade
  misleading (0.92). Regrade recommended (0.83). Missing
  context diagnosis confirmed on desk data.

## API costs

Total session spend: < $0.10 across ~300 API calls.
All calls logged via OpenRouter usage tracking.

## Reproducibility

Every API call is reproducible with the same model version
(typesafe/jev-1.13-20260917) and the same state/instructions.
Jev's near-determinism (σ=0.004 on repeated calls) means
results should replicate within ±0.01.
