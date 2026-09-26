# Reasoning Invariance

A method for stress-testing decisions by exploiting the gap between
a model's single-call confidence and its distribution across
rephrased, evidence-varied, and parameter-swept variants.

Works with [Laya](https://github.com/NandhaKishorM/laya) (open-source,
local, ~47ms on Apple Silicon) or [TypeSafe Jev](https://typesafe.ai)
(API, ~150ms, $0.042/MTok).

## Install

```bash
# Local (recommended)
pip install laya

# Or use Jev via API
export OPENROUTER_API_KEY=your_key
```

## The core idea

A claim that only scores high under one specific phrasing is
phrasing-dependent, not true — like a trading strategy that only
works in a bull market. Fan N phrasings, take the distribution.
Tight spread = robust answer. Wide spread = your question is the problem.

## Three forms of invariance

### 1. Phrasing invariance
Vary the words, hold the claim. Tests question quality.
- 16 deterministic surface-form transforms (synonym × frame composition)
- Generator produces 1000+ variants without an LLM
- Convergence runner tracks median/spread in real time

### 2. Evidence invariance
Vary the state (drop facts), hold the question. Finds load-bearing facts.
- Drop each fact, rescore → impact delta
- Drop pairs → interaction effects (redundancy vs additivity)
- "What would change your mind?" → test hypothetical additions

### 3. Parameter invariance
Sweep a number in the claim, find the peak. Extracts the model's actual belief.

| Question | True answer | Peak value | Peak score |
|---|---|---|---|
| Earth's age | 4.54 Gyr | 4.5 Gyr | 0.950 |
| Speed of light | 299,792 km/s | 300,000 km/s | 0.960 |
| Water boiling point | 100°C | 100°C | 0.970 |
| World population | ~8.1B | 8B | 0.960 |
| "X/10 startups fail" | ~6/10 (academic) | 6/10 | 0.620 |

The popular "9 out of 10 startups fail" scored 0.45 — the model doesn't
believe it. The peak at 6/10 is closer to the academic literature.

## The Reasoning Graph

`reason.py` — a self-routing reasoning engine using all three primitives
(Noul, Score, Choice):

1. **ASSESS** — score, confidence, complexity, question type (one multi-call)
2. **INVARIANCE CHECK** — always runs, catches phrasing premium
3. **ROUTE** — the model picks its own next step:
   - `evidence_audit` — rank facts by importance, drop-each for impact
   - `decompose` — break into sub-questions, identify what data would help
   - `what_if` — best/worst case, expert view, hindsight
   - `reframe` — alternative framings, coherence check
   - `accept_uncertainty` — explain WHY (missing context, contradictory
     evidence, inherently uncertain, wrong question)
4. **LOOP** — re-score, re-route until verdict or max depth. Each route
   tried once then removed — no loops.

The model decides what to think about next. The graph is the intelligence.
Each node is a dumb decision.

### Example: startup investment

23 calls, $0.0005 on Jev (free on Laya), ~1 second on M4:

```
Score: 0.50 (uncertain)
→ Invariance: confirmed 0.48, no phrasing premium
→ Evidence audit: runway and term sheets are load-bearing
→ Decompose: needs unit economics (0.96 confidence)
→ What-if: range [0.27, 0.69] — too wide
→ Accept uncertainty: reason = missing context
→ What context? CAC/LTV at 0.87 confidence
```

Three independent methods pointed to the same missing data.
The graph is a data collection planner disguised as an evaluator.

## Key findings

### Phrasing premium
Single calls overstate confidence vs invariance median by 0.04–0.07.
Always run invariance or the reasoning graph.

### State vs prior
- **Novel domains** (no training data): pure state reading.
  0.37 → 0.97 with evidence, 0.37 → 0.01 against.
- **Known domains**: state must be strong enough to overcome training prior.
- **Physical laws**: state cannot override. "Water is dry" stays 0.30.

### Calibration on hard questions
HLE-level graduate math: every score 0.31–0.52 (indeterminate).
Frontier LLMs score wrong at 80–90% confidence on the same questions.
These models return ~0.4 and shrug — calibration error near zero on
questions they can't answer.

### Benchmarks

| Benchmark | Score | Cost (Jev) |
|---|---|---|
| TruthfulQA misconceptions | 10/10, all < 0.30 | $0.000018 |
| Reasoning fallacies | 8/8 (Monty Hall 0.96) | $0.000024 |
| Academic paired claims | 6/6, 0.90+ gap | $0.000023 |
| Parameter sweep (5 constants) | 5/5 correct peaks | $0.000017 |

### Laya vs Jev

| | Laya (local) | Jev (API) |
|---|---|---|
| Latency | ~47ms (M4 MPS) | ~150ms + network |
| Cost | Free | $0.042/MTok |
| Misconceptions | 9/10 | 10/10 |
| Reasoning fallacies | Not yet tested | 8/8 |
| Calibration (raw) | ECE 0.466 | ECE 0.246 |
| Calibration (fitted) | ECE 0.081 | — |
| Weights | Open (Apache 2.0) | Closed API |

Laya ships overconfident out of the box. After temperature fitting,
calibration is better than Jev. Invariance corrects both.

## Architecture

```
Data source → JSON state → Decision model evaluates
                              ↓
                     Invariance check
                              ↓
                    Reasoning graph
                              ↓
                 SUPPORTED / UNSUPPORTED
                          or
                 UNCERTAIN → what's missing?
                              → go get it
                              → feed back
                              → run again
```

## Rules

1. **JSON state, not prose.** `{"revenue": [45000, 48600, ...]}` beats
   "revenue is 45k growing 8%." Numbers can't hide things.
2. **The median is the position. The spread is the confidence.** If you
   didn't run invariance, you don't have a position — you have a paragraph.
3. **Novel domains = pure state reading.** No training contamination.
   Known domains need stronger evidence to move the score.
4. **Compass, not calculator.** These models rank correctly but can't
   compute. Use for "which option is better," not "what's 5 × 30."
5. **Missing context = go collect, not force a decision.** The graph
   tells you what data to get. Get it. Feed it back. Run again.

## Files

| File | Purpose |
|---|---|
| `reason.py` | Reasoning Graph v2 — self-routing, all three primitives |
| `convergence.py` | Phrasing invariance runner — median/spread/coherence |
| `generator.py` | Deterministic variant generator — 1000+ variants, no LLM |
| `transforms.py` | 16 surface-form transforms (preserving + inverting) |
| `invariance.py` | Original invariance runner |
| `questionbank.py` | Question bank for benchmarks |
| `SKILL.md` | Claude Code skill definition |

## Quick start

```bash
# Phrasing invariance
python3 convergence.py --n 1000 --state "your context" "Your claim"

# Full reasoning graph
python3 reason.py --state "your context" "Your question"
```

## License

MIT
