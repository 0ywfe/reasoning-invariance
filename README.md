# Reasoning Invariance

A method for stress-testing decisions by exploiting the gap between
a model's single-call confidence and its distribution across
rephrased, evidence-varied, and parameter-swept variants.

Built on [TypeSafe AI's Jev](https://typesafe.ai) (System One model),
accessed via OpenRouter at `$0.042/MTok` input, output free, ~100ms latency.

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
- Landed correctly on: Earth's age (4.5 Gyr, 0.950), speed of light
  (300k km/s, 0.960), water boiling (100°C, 0.970), world population
  (8B, 0.960), and a novel-domain optimal knee (0.80, 0.690) from
  three data points.
- Startup failure rate: peak at 6/10 (0.62), not the popular "9/10" (0.45).
  Closer to academic literature than the motivational-speaking stat.

## The Reasoning Graph

`reason.py` — a self-routing reasoning engine using all three Jev primitives:

1. **ASSESS** (Noul + Score + Choice) — score, confidence, complexity, question type
2. **INVARIANCE CHECK** — always runs, catches phrasing premium before any verdict
3. **ROUTE** (Choice) — Jev picks its own next step:
   - `evidence_audit` — rank facts by importance, drop-each for actual impact
   - `decompose` — break into sub-questions, identify what data type would help
   - `what_if` — test best/worst case, expert view, hindsight
   - `reframe` — test alternative framings, check coherence
   - `accept_uncertainty` — explain WHY it can't resolve (missing context,
     contradictory evidence, inherently uncertain, wrong question)
4. **LOOP** — re-score, re-route until verdict or max depth. Each route tried
   once then removed — no loops.

Jev decides what to think about next. The graph is the intelligence.
Each node is a dumb decision.

## Key findings

### Phrasing premium
Single Jev calls consistently overstate confidence vs invariance median:

| Claim | Single | Invariance | Δ |
|---|---|---|---|
| Mortgage approved | 0.720 | 0.680 | -0.040 |
| Startup profitable | 0.350 | 0.280 | -0.070 |
| Borderline mortgage | 0.390 | 0.330 | -0.060 |

### State vs prior
- **Novel domains** (zorblax, glimmer, desk data): pure state reading.
  0.37 → 0.97 with evidence, 0.37 → 0.01 against. No prior contamination.
- **Known domains**: state must be strong enough to overcome training prior.
  Startup with basic facts: 0.35. With "5M revenue, market leader": 0.89.
- **Physical laws**: state cannot override. "Water is dry" stays 0.30 even
  with explicit contradicting state.

### Jev doesn't believe "9/10 startups fail"
Direct test: 0.34. Parameter sweep peak at 6/10 (0.62). The popular
figure is a training-data artefact Jev doesn't share.

### Calibration on hard questions
HLE-level graduate math: every score 0.31–0.52 (indeterminate). Frontier
LLMs score wrong at 80-90% confidence on the same questions. Jev returns
~0.4 and shrugs — calibration error near zero on questions it can't answer.

### Benchmark results
- **TruthfulQA misconceptions**: 10/10 correct, all below 0.30. Cost: $0.000018.
- **Reasoning fallacies**: 8/8 correct. Monty Hall 0.96, all fallacies rejected.
- **Academic benchmarks**: 6/6 correct. 0.90+ gap between right and wrong.
- **Knowledge (parameter sweep)**: 5/5 correct peaks on known constants.

### The reasoning graph on real decisions
Startup investment question → 23 API calls, $0.0005:
1. Scored 0.50 (uncertain)
2. Invariance confirmed (0.48, no phrasing premium)
3. Evidence audit: runway and term sheets load-bearing
4. Decomposed: needs unit economics (0.96 confidence)
5. What-if: range [0.27, 0.69] — too wide
6. Accepted uncertainty: reason = missing context
7. Asked WHAT context: CAC/LTV at 0.87 confidence

Three independent methods (evidence audit, decomposition, what-if)
all pointed to the same missing data. The graph is a data collection
planner disguised as an evaluator.

### Applied to 91 trading batteries
Fed all 91 CPCV battery results with the caveat that the grading metric
(x_closed) ignores strand losses:
- Grade misleading? **0.92**
- Best arm (strand-aware)? **knee 0.25 at p=0.99** (the only arm where
  closed exceeds strand basis)
- Next step? **Regrade all 91 batteries at p=0.83**
- Promising batteries surviving strand correction? **Most eliminated (p=0.58)**

## Architecture

```
Agent → formats data as JSON state → Jev evaluates
        ↓
    Question → Invariance check → Reasoning graph
                                    ↓
                            SUPPORTED / UNSUPPORTED
                                    or
                            UNCERTAIN → what's missing? → go get it → loop
```

The agent never concludes. It pipes data. Jev returns numbers.
The operator decides. Nobody in the chain is trained to please
a human rater.

## Rules for the skill

1. **Feed data as JSON state, not prose summaries.** Numbers don't lie.
   Prose hides things.
2. **The median is the position. The spread is the confidence.** If you
   didn't run invariance, you don't have a position — you have a paragraph.
3. **When the domain is novel, Jev reads pure state.** Your desk data has
   no training contamination. Known domains need stronger state to overcome priors.
4. **Jev ranks correctly but can't compute.** Use it for "which option is
   better," not "will this work." Compass, not calculator.
5. **If the graph returns missing context, the answer isn't to force a
   decision — it's to go get what's missing.** The graph told you what to
   collect. Collect it. Feed it back. Run again.
6. **Invariance catches phrasing bias. The reasoning graph catches missing
   data.** They're complementary. Run both.

## Files

- `transforms.py` — 16 deterministic surface-form transforms
- `generator.py` — N=1000+ compositional variant engine
- `convergence.py` — fires N variants, tracks median/spread/coherence
- `reason.py` — Reasoning Graph v2: self-routing with all three primitives
- `invariance.py` — original runner
- `questionbank.py` — question bank
- `SKILL.md` — Claude Code skill definition

## Cost

Knowledge test (10 questions): $0.000018.
Reasoning fallacies (8 questions): $0.000024.
Full reasoning graph (23 calls): $0.0005.
Parameter sweep (10 values): $0.000017.
91-battery roadmap (5 decisions): $0.00003.

Entire study tonight: under a dime.

## Access

Jev via OpenRouter: `typesafe/jev-1.13` at
`https://openrouter.ai/api/alpha/decisions`.
$5 credits ≈ 385,000 calls.
