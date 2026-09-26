---
description: |
  Calibrated binary/ordinal/choice decisions on any claim using
  Laya (local, free, ~47ms) or Jev (API, ~150ms, $0.042/MTok).
  Three invariance forms strip framing, evidence, and parameter bias.
  The reasoning graph self-routes through uncertainty.
  Use before committing to any structural claim.
tools:
  - convergence.py   # phrasing invariance runner
  - reason.py        # self-routing reasoning graph (all 3 primitives)
  - generator.py     # deterministic variant generator
  - transforms.py    # 16 surface-form transforms
---

# Reasoning Invariance — Claude Code Skill

## When to use

Before committing to any structural claim. The median is the position.
The spread is the confidence. If you didn't run it, you don't have a
position — you have a paragraph.

## Backends

**Laya (default):** `pip install laya` — local, free, ~47ms on M4 MPS.
Open-source, Apache 2.0. Runs on any machine with PyTorch.

**Jev (fallback):** OpenRouter API at `typesafe/jev-1.13`. $0.042/MTok
input, output free. ~150ms + network. Set `$OPENROUTER_API_KEY`.

## Quick start

```bash
# Phrasing invariance
python3 convergence.py --n 1000 --state "your context" "Your claim"

# Full reasoning graph
python3 reason.py --state "your context" "Your question"
```

## The three primitives

- **Noul** (yes/no, 0→1): `"type": "noul"` — is this true?
- **Score** (ordered spectrum): `"type": "score"` — how much?
- **Choice** (pick one): `"type": "choice"` — which one?

## Three forms of invariance

### 1. Phrasing invariance
Vary words, hold claim. Tight spread = robust. Wide = fragile.

### 2. Evidence invariance
Drop each fact, rescore. The delta is that fact's load.

### 3. Parameter sweep
Sweep a number, find the peak. The peak is the model's belief.

## Rules

1. **JSON state, not prose.** Numbers can't hide things.
2. **Novel domains = pure state reading.** Known domains need stronger evidence.
3. **Compass, not calculator.** Ranks correctly, can't compute.
4. **Missing context = go collect, not force.** The graph tells you what to get.
5. **Single calls are biased upward.** Always run invariance or the graph.

## Interpreting results

| Score | Verdict | Action |
|---|---|---|
| > 0.6 | SUPPORTED | Verify with invariance, then trust |
| 0.4 - 0.6 | UNCERTAIN | Run reasoning graph — it will diagnose why |
| < 0.4 | UNSUPPORTED | Check coherence (negation should be > 0.6) |

| Spread | Meaning |
|---|---|
| < 0.10 | Rock solid |
| 0.10 - 0.25 | Acceptable |
| > 0.25 | Fragile — question is the problem |
