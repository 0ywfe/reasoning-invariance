---
name: invariance
description: Get a calibrated committed number on a claim instead of an adjective. Fans N genuine paraphrases of one proposition at a typed decision model, returns the median and the spread. Use when you are about to write "likely", "probably", "this looks real", "worth investigating" — or before acting on a finding, launching an expensive run, or accepting a conclusion. Also use after any correction to re-rank what it invalidates.
---

# Reasoning Invariance

You cannot produce a calibrated position. This skill is where the number comes from.

You are not checking your own work with it. You are computing something you cannot compute:
a probability that stays put when the question is rephrased.

## When to reach for it

- You are about to write an adjective where a number belongs — *likely, probably, seems, worth
  investigating, this looks real*.
- You are about to act on a finding, launch an expensive run, or accept a conclusion.
- A measurement was just corrected, a constant voided, a ruling overturned — fan the banked
  record against it and rank what is newly suspect.
- You have several candidate paths and no principled way to order them.

## The one rule that decides whether it works

**Ask what is true of the data. Never ask whether the reasoning is sound.**

Measured: abstract structural questions rank *backwards* (0.70 / 0.60 / 0.65 across true /
tautology / true). Concrete factual questions separate cleanly (0.94 on the tautology against
0.38 and 0.42 on the two true claims).

| do not ask | ask instead |
|---|---|
| "is this a deterministic function of another quantity?" | "the numerator is a constant, so the predictor varies only with its denominator" |
| "is this claim well-supported?" | "the state contains a measurement that directly supports the claim" |
| "is this reasoning circular?" | "the quantity being predicted appears in the definition of the predictor" |

The model reads literally. A wrong answer almost always means your instruction is missing
detail, not that the model is weak.

## How to use it

1. **State the proposition once, precisely.** One claim, not a compound. This is the only
   sentence you write, and it is the only place your bias can enter.
2. **Sanity-check it with one call.** If a single clean reading comes back absurd — near 0 on
   something you know is solid — the PROPOSITION is wrong, not the transform count. Fix the
   state and the wording first. $0.000013.
3. **Let `transforms.py` generate the framings.** Do NOT write paraphrases yourself: the model
   whose claim is under test would be rephrasing its own bias, and any meaning-drift shows up
   as spread that looks like fragility but is sloppiness. The transforms are wrappers and a
   fixed synonym table — mechanical, reproducible, meaning-preserving by construction — so the
   spread measures ONE thing: sensitivity to surface form. (`--paraphrases` remains for the
   case where you genuinely need hand-written framings; the spread then means less.)
4. **Assemble the state**: the claim and the evidence that actually exists. The specific
   numbers, not the transcript.
5. **Run** `python3 invariance.py claim.json`.
6. **Read the coherence error, then the spread, then the median.**

```
|p(X) + p(not X) - 1| > 0.20  →  INCOHERENT. The model is reading the surface, not the
                                 proposition. The number means nothing. Stop.
p10-p90 > 0.25                →  SURFACE-SENSITIVE. The reading moves under transforms
                                 that cannot have changed the meaning. Do not act.
otherwise                     →  act on the median.
separation                    →  expect ~0.6 between supported and unsupported;
                                 measured TRUE 0.800 / 0.765 vs FALSE 0.160 / 0.105.
```

The coherence check is the one that needs no interpretation. A model answering on surface cues
can look perfectly stable across polarity-preserving framings and still fail it — which is why
it is read first.

## Put the evidence in the state

The state field is where the evidence goes. Put it there.

If the fact that would settle the claim does not exist yet, **run the query that produces it,
then run this.** That is the work. It is not a limitation any more than a calculator is limited
by needing you to type the numbers.

What this buys you is the case where the settling fact is already in your hands and you have not
drawn the conclusion — which is the common failure. A tautology with a monotone decile curve and
a bootstrap-robust +14.11pp gap survived a human read for hours because the constant numerator
that killed it was sitting in the data, unconnected. Scored 0.160 the moment it was in the state.

## Do not

- Do not ensemble identical calls. Repeats are near-deterministic — σ = 0.004 over ten. You get
  copies, not information.
- Do not average a wide spread into a tidy number. A wide spread is the finding.
- Do not ask it a question about your venue, your domain, or your data that it has no state for.
  It is calibrated on general data; it answers what is in front of it.
- Do not ask it to count. Error grows with size; iterate one question per item instead.
