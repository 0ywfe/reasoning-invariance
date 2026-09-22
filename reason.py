#!/usr/bin/env python3
"""Reasoning Graph — MCTS-style reasoning using Jev as the evaluator.

No single call reasons. A thousand calls wired into a decision tree can.
Each node is a dumb decision. The graph is the intelligence.

Usage:
    python3 reason.py "Should this startup raise a Series A?"
    python3 reason.py --state "context" "Your question"
    python3 reason.py --budget 500 "Complex question"
"""
from __future__ import annotations
import os, sys, json, time, argparse
import requests

API_URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"


class JevNode:
    """One node in the reasoning graph."""
    def __init__(self, claim: str, state: str, score: float = None,
                 parent: 'JevNode' = None, action: str = "root"):
        self.claim = claim
        self.state = state
        self.score = score
        self.parent = parent
        self.action = action
        self.children: list[JevNode] = []
        self.spread = None
        self.coherence = None
        self.load_bearing = None
        self.peak_param = None


class ReasoningGraph:
    """Build a reasoning graph by composing Jev calls."""

    def __init__(self, api_key: str, budget: int = 200):
        self.key = api_key
        self.budget = budget
        self.calls = 0
        self.cost = 0
        self.nodes: list[JevNode] = []

    def _call(self, state, questions) -> dict:
        self.calls += 1
        r = requests.post(API_URL,
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"},
            json={"model": MODEL, "state": state, "questions": questions},
            timeout=30).json()
        self.cost += r.get("usage", {}).get("cost", 0)
        return r

    def score(self, claim: str, state: str) -> float:
        r = self._call(state, {"q": {"type": "noul", "instructions": claim}})
        return r["answers"]["q"]["noul"]

    def score_batch(self, claims: list[str], state: str) -> list[float]:
        qs = {f"q{i}": {"type": "noul", "instructions": c} for i, c in enumerate(claims)}
        r = self._call(state, qs)
        return [r["answers"][f"q{i}"]["noul"] for i in range(len(claims))]

    def assess(self, claim: str, state: str) -> JevNode:
        score = self.score(claim, state)
        node = JevNode(claim, state, score)
        self.nodes.append(node)
        return node

    def diagnose(self, node: JevNode) -> dict:
        """Find what's driving the uncertainty."""
        facts = [f.strip() for f in node.state.split('.') if f.strip()]
        if len(facts) < 2:
            return {"type": "insufficient_state", "facts": len(facts)}

        baseline = node.score
        drops = []
        for i, fact in enumerate(facts):
            subset = '. '.join(f for j, f in enumerate(facts) if j != i)
            s = self.score(node.claim, subset)
            drops.append({"index": i, "fact": fact, "score": s,
                         "delta": s - baseline})

        drops.sort(key=lambda x: -abs(x["delta"]))
        node.load_bearing = drops[0]

        helpers = [d for d in drops if d["delta"] > 0.02]
        hurters = [d for d in drops if d["delta"] < -0.02]

        return {
            "type": "diagnosed",
            "baseline": baseline,
            "load_bearing": drops[0],
            "helpers": helpers,
            "hurters": hurters,
            "neutral": [d for d in drops if abs(d["delta"]) <= 0.02],
        }

    def explore(self, node: JevNode, alternatives: list[str]) -> list[JevNode]:
        """Score alternative claims against the same state."""
        scores = self.score_batch(alternatives, node.state)
        children = []
        for alt, s in zip(alternatives, scores):
            child = JevNode(alt, node.state, s, parent=node, action="explore")
            node.children.append(child)
            self.nodes.append(child)
            children.append(child)
        return children

    def what_if(self, node: JevNode, scenarios: dict[str, str]) -> dict[str, float]:
        """Test hypothetical additions to the state."""
        results = {}
        for name, extra_fact in scenarios.items():
            new_state = node.state + '. ' + extra_fact
            s = self.score(node.claim, new_state)
            results[name] = {"score": s, "delta": s - node.score, "fact": extra_fact}
        return results

    def sweep(self, state: str, template: str, values: list) -> list[tuple]:
        """Sweep a parameter, find the peak."""
        claims = [template.format(v=v) for v in values]
        scores = self.score_batch(claims, state)
        results = list(zip(values, scores))
        peak = max(results, key=lambda x: x[1])
        return results, peak

    def reason(self, question: str, state: str) -> dict:
        """Run the full reasoning graph."""
        log = []
        t0 = time.time()

        log.append("STEP 1: Initial assessment")
        root = self.assess(question, state)
        log.append(f"  Score: {root.score:.3f}")

        verdict = "SUPPORTED" if root.score > 0.6 else "UNSUPPORTED" if root.score < 0.4 else "UNCERTAIN"
        log.append(f"  Initial verdict: {verdict}")

        if verdict != "UNCERTAIN":
            log.append("")
            log.append("STEP 2: Invariance check")
            rephrasings = [
                f"It is true that {question.rstrip('.')}.",
                f"The following holds: {question.rstrip('.')}.",
                f"Based on the evidence, {question.rstrip('.')}.",
                f"It is the case that {question.rstrip('.')}.",
                f"One concludes that {question.rstrip('.')}.",
            ]
            scores = self.score_batch(rephrasings, state)
            median = sorted(scores)[len(scores) // 2]
            spread = sorted(scores)[-1] - sorted(scores)[0]
            log.append(f"  Invariance median: {median:.3f} (spread {spread:.3f})")

            if abs(median - root.score) > 0.1:
                log.append(f"  WARNING: Phrasing premium detected ({root.score:.3f} -> {median:.3f})")
                root.score = median

            verdict = "SUPPORTED" if median > 0.6 else "UNSUPPORTED" if median < 0.4 else "UNCERTAIN"
            log.append(f"  Revised verdict: {verdict}")

        if verdict == "UNCERTAIN":
            log.append("")
            log.append("STEP 3: Diagnosing uncertainty")
            dx = self.diagnose(root)

            if dx["type"] == "diagnosed":
                lb = dx["load_bearing"]
                log.append(f"  Load-bearing fact: [{lb['index']}] {lb['fact'][:70]}")
                log.append(f"    Dropping it moves score {lb['delta']:+.3f}")

                if dx["helpers"]:
                    log.append(f"  Facts HURTING the score (removing helps):")
                    for h in dx["helpers"][:3]:
                        log.append(f"    [{h['index']}] {h['fact'][:60]} ({h['delta']:+.3f})")

                if dx["hurters"]:
                    log.append(f"  Facts HELPING the score (removing hurts):")
                    for h in dx["hurters"][:3]:
                        log.append(f"    [{h['index']}] {h['fact'][:60]} ({h['delta']:+.3f})")

                neutral_count = len(dx["neutral"])
                if neutral_count:
                    log.append(f"  Neutral facts (no impact): {neutral_count}")

        log.append("")
        log.append("VERDICT")
        log.append(f"  Question: {question}")
        log.append(f"  Score: {root.score:.3f}")
        log.append(f"  Answer: {verdict}")
        if root.load_bearing:
            log.append(f"  Depends most on: {root.load_bearing['fact'][:70]}")
        log.append(f"  API calls: {self.calls}")
        log.append(f"  Cost: ${self.cost:.6f}")
        log.append(f"  Time: {time.time() - t0:.1f}s")

        return {
            "question": question,
            "score": root.score,
            "verdict": verdict,
            "log": "\n".join(log),
            "calls": self.calls,
            "cost": self.cost,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reasoning Graph — think with Jev")
    parser.add_argument("question", help="The question to reason about")
    parser.add_argument("--state", default="", help="Context/evidence")
    parser.add_argument("--budget", type=int, default=200, help="Max API calls")
    args = parser.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Set OPENROUTER_API_KEY")
        sys.exit(1)

    graph = ReasoningGraph(key, budget=args.budget)
    result = graph.reason(args.question, args.state or args.question)
    print(result["log"])
