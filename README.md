# Reasoning Invariance

**A capability, not a check: calibrated committed positions for a model that cannot produce
them.**

First stated and measured 2026-09-22. See `PROVENANCE.md` for the timestamp trail.

---

## What this is

An LLM cannot hold a calibrated position. The muscle does not exist. RLHF optimised it to
produce the paragraph that earns approval, not to commit to a number and keep it — so it
returns adjectives ("likely", "probably", "worth investigating") that are not 0.7, and that
move when you rephrase the question.

This is not a corrective for that. **It is the missing capability.** You do not audit someone's
arithmetic with a calculator — you let them compute. A calibrated typed decision model returns
a number where the LLM can only return prose, and the LLM's job becomes what it is actually
good at: generating the candidate framings.

The division of labour:

| | does what | because |
|---|---|---|
| **LLM** | writes the proposition and N genuine paraphrases of it | language generation |
| **decision model** | returns a calibrated probability for each | arithmetic the LLM cannot do |
| **the spread** | says whether the question was well-posed | measurement |

## The test

*Phrasing* invariance describes the mechanism. **Reasoning invariance describes what it tests.**
A claim either holds regardless of how it is framed, or it does not — and if it does not, the
reasoning was fragile, not the wording.

## The claim

A trading strategy that only works in a bull market is regime-dependent — it isn't edge, it's
luck. **A claim that only scores 0.9 when phrased one specific way is phrasing-dependent — it
isn't true, it's well-worded.** Both are the same failure: the signal is an artefact of the
frame rather than the data.

Trading solved this by testing across windows, tapes and market conditions. If the edge
survives, it's real. The same test is now available for reasoning, because a calibrated
decision model returns a *number* instead of a paragraph — so the variance across framings is
visible, measurable and actionable.

**Ask the same proposition 1,000 different ways. The distribution is the answer; the spread is
the diagnostic.**

An LLM asked the same question 1,000 ways returns 1,000 paragraphs that all sound equally
confident. You cannot see the variance because it's buried in prose. That is what this replaces.

## Why it became affordable (the Jevons argument)

The model this was measured on is named for Jevons, and the paradox is the point. Coal
consumption rose when steam engines got efficient, because efficiency made new applications
economical.

Deliberation used to be priced per-decision: minutes of reasoning, real token cost. So you
picked *which* question to ask and committed — and the picking was itself an unexamined
judgment. At ~$0.000013 per decision you stop deciding what to decide about. A fork stops being
"choose a path" and becomes a search over the decision space.

The scarcity was never intelligence. It was that intelligence was priced per-deliberation.

## The three mechanics, measured

**1. Identical calls are near-deterministic.** Ten repeats of one question: `0.91` nine times,
`0.92` twice — **σ = 0.004**. So "1,000 calls on one question" is 1,000 copies of one answer.
The calibrated probability *is already* the aggregated belief; there is no discrete vote to
take, unlike LLM self-consistency sampling.

**2. Variance lives across framings, not samples — but only genuine paraphrases count.**
Eight loosely-related wordings of one proposition spread **0.83** (0.12 to 0.95). Sixteen true
paraphrases of the same proposition spread **0.05–0.15**. The first number was sloppiness: the
wordings weren't the same proposition. **Spread measures question quality first and model
fragility second**, and that ordering is the discipline — in trading you vary the *data* and
hold the *strategy* fixed; here you vary the *wording* and must hold the *proposition* fixed.

**3. Context rot did not bite at this scale.** Padding the state with ~40 repetitions of
irrelevant material moved a reading `0.910 → 0.920`.

## The result

Four claims with independently known outcomes, 16 genuine paraphrases each, one call per claim:

| claim | truth | median | p10–p90 spread |
|---|---|---|---|
| A | TRUE | **0.800** | 0.14 |
| B | TRUE | **0.765** | 0.15 |
| C | **FALSE** (a tautology) | **0.160** | 0.07 |
| D | **FALSE** | **0.105** | 0.05 |

No overlap. **~0.6 of separation** between supported and unsupported. **64 judgments for
$0.00011.**

Claim C is the interesting one: a predictor with a monotone decile curve, a bootstrap-robust
gap of +14.11pp with CI90 excluding zero — and a tautology, because its numerator was constant
across every observation, so the ratio varied only with its denominator. It had survived a
human read. The diagnostic scored it 0.160.

## Question design is the whole game

**Abstract structural questions fail. Concrete factual questions separate.**

Asking *"is this a deterministic function of another quantity in the same analysis?"* returned
0.70 / 0.60 / 0.65 across (true / tautology / true) — **ranked backwards**.

Asking *"the numerator is a constant, so the predictor varies only with its denominator"*
returned **0.94 on the tautology against 0.38 and 0.42** on the two true claims.

> **Rule: ask what is true of the data, never whether the reasoning is sound.**

A decision model reads literally. A wrong answer usually means the instruction is missing
detail, not that the model is weak.

## The standing use: every correction is a re-examination event

When a measurement is corrected, a constant voided or a ruling overturned, fan the entire
banked record against it and rank what is newly suspect.

Run on a real accounting correction over 17 banked "this was refuted" verdicts, scoring
*"was this verdict reached using a measure the defect would have distorted"* × *"does this
approach deploy more capital than its baseline"*:

- the top-ranked verdict (0.86 × 0.59) was one that had in fact been invalidated by the
  correction and sat unrevised for two days until it was found by hand
- the two verdicts that could not possibly be affected floored correctly
- **$0.00033 for all 17**

The verdict that surfaced first had, once revisited, produced the best result in the project.
It would have surfaced two days earlier.

## The boundary

The evidence handed to the panel for claim C included the conditioning test that exposed the
tautology. **Without that test having been run, C's evidence is indistinguishable from A's and
scores ~0.8.**

So: this does not replace running the falsification. **It catches the case where the
disconfirming fact is already held and the conclusion has not been drawn** — which is the
common failure, and was exactly the case for claim C, where the constant was sitting in the
data for hours before anyone connected it.

## The coherence check

Transforms come in two classes. Polarity-preserving ones leave the proposition alone, so the
reading should not move; spread across them is surface sensitivity. Polarity-inverting ones
negate it, so the reading should be `1 - p`.

**|p(X) + p(not X) - 1| is coherence error, and it needs no spread to interpret.** A model
answering on surface cues rather than meaning can look perfectly stable across the preserving
set and still fail this. Measured on a real claim: preserving median 0.290, inverting median
0.805, coherence error **0.095**.

This is also why the transforms are mechanical rather than model-written. If the model under
test generates its own paraphrases, the bias rephrases itself and meaning-drift shows up as
spread that looks like fragility. Deterministic wrappers plus a fixed synonym table cannot
drift. Measured: hand-written paraphrases spread 0.18 on a claim where transforms spread 0.13.

## The primitive

```
fan ≥12 GENUINE paraphrases of one proposition into ONE call
  (output is free and questions parallelise, so N framings ≈ the price of one)

if p10–p90 > 0.25 → the question is ambiguous. Rewrite it. Do not average it.
otherwise        → act on the median
expect           → ~0.6 of separation between supported and unsupported
```

## Prior art

None known for phrasing-invariance as a *reasoning* diagnostic at the time of writing. The
components are all old — calibration, ensembling, paraphrase robustness in NLP evaluation,
regime invariance in quantitative finance. The composition is what is new, and it only became
affordable when a calibrated typed decision dropped to ~$0.000013.

If you are reading this after someone has formalised and named it: the timestamp is in
`PROVENANCE.md` and the git history.

## Licence

MIT.
