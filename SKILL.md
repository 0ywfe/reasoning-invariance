---
description: |
  Use Jev (TypeSafe's System One model) for calibrated binary/ordinal/choice
  decisions on any claim.  Three invariance forms strip framing, evidence,
  and parameter bias.  The reasoning graph self-routes through uncertainty.
  Cost: ~$0.000013 per call.  Use before committing to any structural claim.
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

## Quick start

### Single claim check
```bash
python3 convergence.py --n 1000 --state "your context" "Your claim here"
```

### Full reasoning graph
```bash
python3 reason.py --state "your context" "Your question here"
```

## The three primitives

- **Noul** (yes/no, 0→1): `"type": "noul"` — is this true?
- **Score** (ordered spectrum): `"type": "score"` — how much?
- **Choice** (pick one): `"type": "choice"` — which one?

All three in one call:
```json
{
  "model": "typesafe/jev-1.13",
  "state": "your data here — JSON preferred over prose",
  "questions": {
    "supported": {"type": "noul", "instructions": "claim"},
    "severity": {"type": "score", "instructions": "how bad",
                 "criteria": ["none", "low", "medium", "high", "critical"]},
    "action": {"type": "choice", "instructions": "what to do",
               "criteria": {"a": "desc", "b": "desc", "c": "desc"}}
  }
}
```

## Three forms of invariance

### 1. Phrasing invariance
Vary words, hold claim. `convergence.py` generates deterministic
variants and tracks median/spread. Tight spread = robust. Wide = fragile.

### 2. Evidence invariance
Drop each fact from state, rescore. The delta is that fact's load.
Drop pairs for interaction effects.

### 3. Parameter sweep
Sweep a number, find the peak. The peak is the model's belief.
```python
for v in [0.1, 0.2, ..., 1.0]:
    score(f"The optimal value is {v}")
# Peak = Jev's estimate
```

## Rules

1. **JSON state, not prose.** `{"revenue": [45000, 48600, ...]}` not
   "revenue is 45k growing 8%". Numbers can't hide things.
2. **Novel domains = pure state reading.** Your desk data has no
   training contamination. Known domains need stronger evidence.
3. **Jev ranks but can't compute.** Compass, not calculator.
   Agent computes the projection, Jev evaluates if it's credible.
4. **Missing context = go collect, not force a decision.** The graph
   tells you what data to get. Get it. Feed it back. Run again.
5. **Single call scores are biased upward.** Always run invariance
   or the reasoning graph. The phrasing premium is real (0.04-0.07).
6. **The graph uses all three primitives:** Noul evaluates, Score
   ranks, Choice routes. Jev decides what to think about next.

## Interpreting results

| Score | Verdict | Action |
|---|---|---|
| > 0.6 | SUPPORTED | Verify with invariance, then trust |
| 0.4 - 0.6 | UNCERTAIN | Run reasoning graph — it will diagnose why |
| < 0.4 | UNSUPPORTED | Check coherence (negation should be > 0.6) |

| Spread | Meaning |
|---|---|
| < 0.10 | Rock solid — answer is phrasing-invariant |
| 0.10 - 0.25 | Acceptable — mild phrasing sensitivity |
| > 0.25 | Fragile — the question is the problem, not the answer |

## API

Endpoint: `https://openrouter.ai/api/alpha/decisions`
Model: `typesafe/jev-1.13`
Auth: `Bearer $OPENROUTER_API_KEY`
Cost: $0.042/MTok input, output free. ~$0.000013 per call.
