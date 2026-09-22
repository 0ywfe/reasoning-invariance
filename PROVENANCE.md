# Provenance

**2026-09-22.** Stated and measured in a single working session.

The concept came from applying regime invariance — a standard robustness test in quantitative
trading, where a strategy is run across windows, tapes and market conditions to separate edge
from luck — to *reasoning*, with phrasing as the regime.

The enabling condition: `typesafe/jev-1.13`, a calibrated typed decision model released
approximately one week before this was written, priced at ~$0.000013 per decision with free
output and parallel questions. Every measurement in `README.md` was taken against it that day.

The ground truth used was a live quantitative research log with independently known outcomes —
claims that had already been confirmed or refuted by experiment, not by opinion. That is what
makes the separation result a measurement rather than a demonstration.

Order of events, same session:

1. The diagnostic was proposed as a filter on model output; measurement showed the failure rate
   it targeted was ~2 instances in 12,009 sentences, and it was set aside.
2. It was re-proposed as a *decision* primitive rather than a filter.
3. Abstract structural questions were tried and failed (ranked backwards).
4. Concrete factual questions were tried and separated cleanly (0.94 vs 0.38/0.42).
5. Determinism, paraphrase spread and context rot were measured.
6. Phrasing invariance was named by analogy to regime invariance, and tested on four
   known-outcome claims with sixteen true paraphrases each.
7. The correction/re-examination use was tested against a real historical correction and
   recovered, in first rank, a verdict that had been missed by hand for two days.

Steps 3 and 4 are the load-bearing part and are recorded because the first attempt failing is
what establishes that the design rule is a finding rather than an assumption.
