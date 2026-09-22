#!/usr/bin/env python3
"""Reasoning Graph v2 — all three Jev primitives, self-routing.

Noul: "is this true?" — the leaf evaluator
Score: "how much?" — the gradient
Choice: "which one?" — the router

Jev decides what to think about next. The graph isn't hardcoded.

Usage:
    python3 reason.py "Your question" --state "context"
"""
from __future__ import annotations
import os, sys, json, time, argparse
import requests

API_URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"


class Jev:
    """Thin wrapper — all three primitives."""

    def __init__(self, api_key: str):
        self.key = api_key
        self.calls = 0
        self.cost = 0

    def _call(self, state, questions) -> dict:
        self.calls += 1
        r = requests.post(API_URL,
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"},
            json={"model": MODEL, "state": state, "questions": questions},
            timeout=30).json()
        self.cost += r.get("usage", {}).get("cost", 0)
        return r

    def noul(self, state: str, instruction: str) -> float:
        r = self._call(state, {"q": {"type": "noul", "instructions": instruction}})
        return r["answers"]["q"]["noul"]

    def noul_batch(self, state: str, instructions: dict[str, str]) -> dict[str, float]:
        qs = {k: {"type": "noul", "instructions": v} for k, v in instructions.items()}
        r = self._call(state, qs)
        return {k: r["answers"][k]["noul"] for k in instructions}

    def score(self, state: str, instruction: str, criteria: list[str]) -> dict:
        r = self._call(state, {"q": {"type": "score", "instructions": instruction, "criteria": criteria}})
        return r["answers"]["q"]

    def choice(self, state: str, instruction: str, criteria: dict[str, str]) -> dict:
        r = self._call(state, {"q": {"type": "choice", "instructions": instruction, "criteria": criteria}})
        return r["answers"]["q"]

    def multi(self, state: str, questions: dict) -> dict:
        """Fire mixed primitives in one call."""
        r = self._call(state, questions)
        return r["answers"]


def reason(question: str, state: str, jev: Jev, max_depth: int = 5) -> dict:
    """The full self-routing reasoning loop."""
    log = []
    depth = 0
    tried = []
    current_state = state

    def emit(msg, indent=0):
        log.append("  " * indent + msg)
        print("  " * indent + msg)

    emit(f"QUESTION: {question}")
    emit(f"STATE: {state[:120]}{'...' if len(state) > 120 else ''}")
    emit("")

    # === STEP 1: Multi-assessment ===
    emit("STEP 1: Assessment (Noul + Score + Choice)")
    answers = jev.multi(state, {
        "supported": {
            "type": "noul",
            "instructions": question,
        },
        "confidence": {
            "type": "score",
            "instructions": "How confident can we be in answering this question given the available evidence?",
            "criteria": ["no_basis", "very_low", "low", "moderate", "high", "certain"],
        },
        "complexity": {
            "type": "score",
            "instructions": "How complex is this question to answer?",
            "criteria": ["trivial", "simple", "moderate", "complex", "requires_decomposition"],
        },
        "question_type": {
            "type": "choice",
            "instructions": "What type of question is this?",
            "criteria": {
                "factual": "Can be answered by looking up a fact",
                "analytical": "Requires analysis of the provided data",
                "predictive": "Asks about a future outcome",
                "comparative": "Asks which option is better",
                "diagnostic": "Asks why something is happening",
            },
        },
    })

    main_score = answers["supported"]["noul"]
    confidence = answers["confidence"]
    complexity = answers["complexity"]
    qtype = answers["question_type"]

    emit(f"  Score:      {main_score:.3f}")
    emit(f"  Confidence: {confidence['score']:.2f}/5 ({confidence['legend']})")
    emit(f"  Complexity: {complexity['score']:.2f}/4 ({complexity['legend']})")
    emit(f"  Type:       {qtype['choice']} (p={qtype['probabilities'][qtype['choice']]:.2f})")
    emit("")

    verdict = "SUPPORTED" if main_score > 0.6 else "UNSUPPORTED" if main_score < 0.4 else "UNCERTAIN"
    emit(f"  Initial verdict: {verdict}")
    emit("")

    # === STEP 2: Invariance check — always runs ===
    emit("STEP 2: Invariance check")
    framings = jev.noul_batch(state, {
        "original": question,
        "negated": f"It is false that {question.rstrip('.')}",
        "conditional": f"Given all the evidence, {question.rstrip('.')}",
        "formal": f"It is the case that {question.rstrip('.')}",
        "strongest": f"The evidence strongly supports that {question.rstrip('.')}",
    })

    positives = [framings["original"], framings["conditional"], framings["formal"], framings["strongest"]]
    median = sorted(positives)[len(positives) // 2]
    spread = max(positives) - min(positives)
    coherence = abs(framings["original"] + framings["negated"] - 1)

    emit(f"  Scores: {', '.join(f'{k}={v:.3f}' for k, v in framings.items())}")
    emit(f"  Median: {median:.3f}  Spread: {spread:.3f}  Coherence error: {coherence:.3f}")

    if abs(median - main_score) > 0.05:
        emit(f"  Phrasing premium detected: {main_score:.3f} \u2192 {median:.3f}")
        main_score = median

    verdict = "SUPPORTED" if main_score > 0.6 else "UNSUPPORTED" if main_score < 0.4 else "UNCERTAIN"
    emit(f"  Verdict after invariance: {verdict}")
    emit("")

    # === STEP 3+: Self-routing loop ===
    while verdict == "UNCERTAIN" and depth < max_depth:
        depth += 1
        emit(f"STEP {depth + 2}: Self-routing (depth {depth})")

        tried_str = f" Already tried: {', '.join(tried)}." if tried else ""
        route_state = (f"{current_state}. Current assessment of '{question}' is "
                      f"{main_score:.3f} (uncertain). Confidence is "
                      f"{confidence['score']:.1f}/5.{tried_str}")

        all_routes = {
            "evidence_audit": "Identify which pieces of evidence are load-bearing and which are noise",
            "decompose": "Break the question into smaller sub-questions that can be answered independently",
            "what_if": "Test what hypothetical additional facts would change the answer",
            "reframe": "The question might be poorly framed \u2014 try stating it differently",
            "accept_uncertainty": "The evidence genuinely does not support a clear answer \u2014 accept indeterminacy",
        }
        available = {k: v for k, v in all_routes.items() if k not in tried}
        if not available:
            available = {"accept_uncertainty": all_routes["accept_uncertainty"]}

        route = jev.choice(route_state,
            "Given the uncertainty, what is the single most valuable next step to resolve this question?",
            available)

        chosen = route["choice"]
        route_conf = route["probabilities"][chosen]
        tried.append(chosen)
        emit(f"  Route: {chosen} (p={route_conf:.2f})")
        emit("")

        if chosen == "evidence_audit":
            emit(f"  Running evidence audit...")
            facts = [f.strip() for f in current_state.split('.') if f.strip()]
            if len(facts) < 2:
                emit(f"  Too few facts to audit ({len(facts)})")
                break

            importance_qs = {}
            for i, fact in enumerate(facts[:15]):
                importance_qs[f"f{i}"] = {
                    "type": "score",
                    "instructions": f"How important is this fact for answering '{question}': {fact}",
                    "criteria": ["irrelevant", "minor", "relevant", "important", "decisive"],
                }
            imp_answers = jev.multi(current_state, importance_qs)

            scored_facts = []
            for i, fact in enumerate(facts[:15]):
                s = imp_answers[f"f{i}"]["score"]
                scored_facts.append((i, fact, s))
            scored_facts.sort(key=lambda x: -x[2])

            emit(f"  Facts ranked by importance:")
            for i, fact, s in scored_facts:
                level = ["irrelevant", "minor", "relevant", "important", "decisive"][min(int(s), 4)]
                emit(f"    [{i}] {s:.1f} ({level}) {fact[:60]}")

            # Drop-each: find actual impact
            emit(f"  Actual impact (drop-each):")
            for i, fact in enumerate(facts[:10]):
                subset = '. '.join(f for j, f in enumerate(facts) if j != i)
                s = jev.noul(subset, question)
                delta = s - main_score
                direction = "HELPS" if delta > 0.02 else "HURTS" if delta < -0.02 else "~"
                emit(f"    [{i}] {delta:+.3f} ({direction}) {fact[:55]}")

        elif chosen == "decompose":
            emit(f"  Decomposing into sub-questions...")
            sub_q_state = f"{current_state}. The question '{question}' is uncertain at {main_score:.3f}."
            subs = jev.multi(sub_q_state, {
                "sufficient": {"type": "noul", "instructions": f"Regarding '{question}': is the evidence sufficient to decide?"},
                "contradictions": {"type": "noul", "instructions": f"Regarding '{question}': are there contradictions in the evidence?"},
                "well_defined": {"type": "noul", "instructions": f"Regarding '{question}': is the question well-defined given this state?"},
                "more_same": {"type": "noul", "instructions": f"Regarding '{question}': would more data of the same type resolve uncertainty?"},
                "different_data": {"type": "noul", "instructions": f"Regarding '{question}': would a different type of data resolve uncertainty?"},
            })

            emit(f"  Sub-questions:")
            emit(f"    Evidence sufficient?     {subs['sufficient']['noul']:.3f}")
            emit(f"    Contradictions?          {subs['contradictions']['noul']:.3f}")
            emit(f"    Well-defined?            {subs['well_defined']['noul']:.3f}")
            emit(f"    More same data helps?    {subs['more_same']['noul']:.3f}")
            emit(f"    Different data helps?    {subs['different_data']['noul']:.3f}")

            what_data = jev.choice(sub_q_state,
                f"What additional information would most help resolve '{question}'?",
                {
                    "financial_projections": "Detailed month-by-month financial projections",
                    "market_data": "Market size, competition, and positioning data",
                    "track_record": "Founder and team track record and past outcomes",
                    "unit_economics": "Customer acquisition cost, lifetime value, margins",
                    "comparable_outcomes": "What happened to similar companies in similar situations",
                })
            emit(f"  Most needed data: {what_data['choice']} (p={what_data['probabilities'][what_data['choice']]:.2f})")

        elif chosen == "what_if":
            emit(f"  Testing hypothetical scenarios...")
            what_ifs = jev.multi(current_state, {
                "opposite": {"type": "noul", "instructions": f"The opposite of '{question}' is true"},
                "best_case": {"type": "noul", "instructions": f"'{question}' is true under the most favorable interpretation"},
                "worst_case": {"type": "noul", "instructions": f"'{question}' is true under the least favorable interpretation"},
                "expert": {"type": "noul", "instructions": f"A domain expert would say '{question}' is true given this evidence"},
                "in_5_years": {"type": "noul", "instructions": f"Looking back 5 years from now, '{question}' turned out to be true"},
            })

            emit(f"  Scenarios:")
            emit(f"    Opposite true?       {what_ifs['opposite']['noul']:.3f}")
            emit(f"    Best case?           {what_ifs['best_case']['noul']:.3f}")
            emit(f"    Worst case?          {what_ifs['worst_case']['noul']:.3f}")
            emit(f"    Expert says?         {what_ifs['expert']['noul']:.3f}")
            emit(f"    Hindsight (5yr)?     {what_ifs['in_5_years']['noul']:.3f}")

            best = what_ifs["best_case"]["noul"]
            worst = what_ifs["worst_case"]["noul"]
            emit(f"  Range: [{worst:.3f}, {best:.3f}] \u2014 gap {best - worst:.3f}")
            revised = (best + worst) / 2
            emit(f"  Revised score (midpoint): {revised:.3f}")
            main_score = revised

        elif chosen == "reframe":
            emit(f"  Testing alternative framings...")
            framings2 = jev.noul_batch(current_state, {
                "original": question,
                "probabilistic": f"It is more likely than not that {question.rstrip('.')}",
                "specific": f"There is strong evidence that {question.rstrip('.')}",
                "hedged": f"There is some reason to believe that {question.rstrip('.')}",
                "negated": f"It is unlikely that {question.rstrip('.')}",
            })

            emit(f"  Framings:")
            for name, s in sorted(framings2.items(), key=lambda x: -x[1]):
                emit(f"    {name:<15} {s:.3f}")

        elif chosen == "accept_uncertainty":
            emit(f"  Jev recommends accepting uncertainty.")
            why = jev.choice(current_state,
                f"Why can't '{question}' be resolved with this evidence?",
                {
                    "insufficient_data": "Not enough evidence to decide",
                    "contradictory": "The evidence points in both directions",
                    "wrong_question": "The question doesn't match the evidence available",
                    "inherently_uncertain": "This is genuinely unpredictable from any evidence",
                    "missing_context": "Key context needed to interpret the evidence is missing",
                })
            emit(f"  Reason: {why['choice']} (p={why['probabilities'][why['choice']]:.2f})")
            break

        emit("")
        verdict = "SUPPORTED" if main_score > 0.6 else "UNSUPPORTED" if main_score < 0.4 else "UNCERTAIN"
        emit(f"  Updated verdict: {verdict} ({main_score:.3f})")
        emit("")

    emit("")
    emit("=" * 60)
    emit("FINAL VERDICT")
    emit("=" * 60)
    emit(f"  Question:  {question}")
    emit(f"  Score:     {main_score:.3f}")
    emit(f"  Verdict:   {verdict}")
    emit(f"  Depth:     {depth}")
    emit(f"  Tried:     {', '.join(tried) if tried else 'none (resolved at invariance)'}")
    emit(f"  API calls: {jev.calls}")
    emit(f"  Cost:      ${jev.cost:.6f}")

    return {
        "question": question,
        "score": main_score,
        "verdict": verdict,
        "depth": depth,
        "tried": tried,
        "calls": jev.calls,
        "cost": jev.cost,
        "log": "\n".join(log),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reasoning Graph v2")
    parser.add_argument("question", help="The question to reason about")
    parser.add_argument("--state", default="", help="Context/evidence")
    parser.add_argument("--depth", type=int, default=5, help="Max reasoning depth")
    args = parser.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Set OPENROUTER_API_KEY")
        sys.exit(1)

    j = Jev(key)
    result = reason(args.question, args.state or args.question, j, args.depth)
