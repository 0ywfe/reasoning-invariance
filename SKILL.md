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

1. **State the proposition once, precisely.** One claim. Not a compound.
2. **Sanity-check with ONE paraphrase first.** Twelve real paraphrases of a precise technical
   claim is slow work, and if you write sloppy ones the spread measures your sloppiness rather
   than the claim's fragility. So fire a single clean framing first. If it returns something
   absurd — near 0 on a claim you know is solid, near 1 on one you know is broken — the
   PROPOSITION STATEMENT is wrong, not the paraphrase count. Fix the state and the wording
   before spending the effort on twelve. One call, $0.000013.
3. **Write ≥12 GENUINE paraphrases.** This is the part only you can do, and the part that
   decides whether the result means anything. They must be the *same proposition* in different
   words — not related propositions. If two of your paraphrases could have different truth
   values, you have written two questions and the spread will measure your sloppiness rather
   than the claim's fragility.
4. **Assemble the state**: the claim, and the evidence that actually exists. Not the whole
   transcript — the specific numbers.
5. **Run** `python3 invariance.py state.json` (see `invariance.py`; one call, all paraphrases,
   output is free so N framings cost about the same as one).
6. **Read the spread before the median.**

```
p10–p90 > 0.25   →  the question is ambiguous. REWRITE IT. Do not average it,
                    do not report the median, do not act on it.
p10–p90 ≤ 0.25   →  act on the median.
separation        →  expect ~0.6 between a supported and an unsupported claim;
                    measured TRUE 0.800 / 0.765 against FALSE 0.160 / 0.105.
```

## What it cannot do

It cannot run your falsification for you. If the disconfirming test has not been run, its
evidence is absent from the state and the claim scores as though it were sound.

It catches the case where **you already hold the disconfirming fact and have not drawn the
conclusion.** That is the common failure and it is worth catching — in the session this was
built in, a tautology with a monotone decile curve and a bootstrap-robust +14.11pp gap sat
undetected for hours because the fact that killed it (a constant numerator) was in the data and
unconnected. Scored 0.160.

## Do not

- Do not ensemble identical calls. Repeats are near-deterministic — σ = 0.004 over ten. You get
  copies, not information.
- Do not average a wide spread into a tidy number. A wide spread is the finding.
- Do not ask it a question about your venue, your domain, or your data that it has no state for.
  It is calibrated on general data; it answers what is in front of it.
- Do not ask it to count. Error grows with size; iterate one question per item instead.
