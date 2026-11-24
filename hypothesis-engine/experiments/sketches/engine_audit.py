#!/usr/bin/env python3
"""SKETCH, NOT RESULTS. Offline, stdlib-only audit of the hypothesis engine's own output.

Implements the measurement side of EXP-ENG-01..04 (see ../engine-validity.md).
Reads hypothesis-engine/data/* and git history READ-ONLY; writes nothing.

    python3 engine_audit.py relevance     # EXP-ENG-01: on-topic rate of surviving claims
    python3 engine_audit.py control       # EXP-ENG-02: corroboration() same-topic vs cross-topic vs shuffled
    python3 engine_audit.py survival      # EXP-ENG-03: P(survive) vs topic pool size under a lexical null
    python3 engine_audit.py churn [N]     # README note: content change across the last N engine commits

The relevance proxy in `relevance` is itself lexical (core-term regex per topic).
It is a screening instrument for a human-labelled audit, not a relevance judgement.
"""
from __future__ import annotations

import json
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]          # hypothesis-engine/
DATA = ENGINE / "data"
sys.path.insert(0, str(ENGINE / "scripts"))
import hypothesis_engine as he  # noqa: E402  (same folder tree; read-only use)

# Core-term regexes per topic. Deliberately narrow; edit and re-run, they are a
# pre-registration target for EXP-ENG-01, not a finding.
CORE = {
    "activation-aware quantization": r"quantiz|\bptq\b|\bawq\b|gptq|low-bit|int4|int8|\bfp4\b",
    "structured sparsity and hardware-matched pruning": r"prun|sparsit|\b2:4\b|n:m",
    "compression composition and ordering": r"(prun|quantiz|low-rank|distill).*(prun|quantiz|low-rank|distill)",
    "representation geometry under compression": r"kernel alignment|\bcka\b|svcca|effective rank|intrinsic dimension|representation(al)? similarity",
    "deployment-aware compression metrics": r"(quantiz|prun|compress).*(latency|energy|pareto|calibrat|memory)|(latency|energy|pareto|calibrat|memory).*(quantiz|prun|compress)",
    "calibration and falsifiability of LLM agents": r"(calibrat|confidence|uncertaint|falsif).*(language model|llm|agent)|(language model|llm|agent).*(calibrat|confidence|uncertaint|falsif)",
    "hidden variable detection / causal discovery from residuals": r"(latent|hidden|unobserved|confound).*(causal|residual)|(causal|residual).*(latent|hidden|unobserved|confound)",
    "world models and curiosity-driven learning": r"world model|curiosity|intrinsic (motivation|reward)|active inference|surprise minimi|model-based reinforcement",
}


def load():
    findings = he.read_jsonl(DATA / "findings_log.jsonl")
    claims = json.loads((DATA / "claim_tree.json").read_text(encoding="utf-8"))["claims"]
    return findings, claims


def surviving(c):
    return c["status"] == "survived" or c["beta_confidence"] >= 0.7


def cmd_relevance():
    findings, claims = load()
    by_hash = {f["hash"]: f for f in findings}
    print(f"{'topic':55s} {'surv':>5s} {'core-hit':>8s} {'arxiv surv':>10s} {'arxiv core-hit':>14s}")
    for topic, pat in CORE.items():
        rx = re.compile(pat, re.I | re.S)
        surv = [c for c in claims if c["scope"].get("topic") == topic and surviving(c)]
        def hit(c):
            f = by_hash.get(c["id"], {})
            return bool(rx.search(f"{f.get('title','')} {f.get('abstract','')}"))
        ax = [c for c in surv if c["scope"].get("source") == "arxiv"]
        print(f"{topic[:55]:55s} {len(surv):5d} {sum(map(hit, surv)):8d} {len(ax):10d} {sum(map(hit, ax)):14d}")


def cmd_control(pairs_per_claim: int = 20, seed: int = 0):
    """corroboration() pass rate for same-topic, cross-topic and token-shuffled partners."""
    findings, claims = load()
    rng = random.Random(seed)
    by_topic = defaultdict(list)
    for f in findings:
        by_topic[f["topic"]].append(f)
    vocab = [t for f in findings for t in re.findall(r"[a-z0-9]+", f.get("abstract", "").lower())]
    rates = {k: Counter() for k in ("same", "cross", "shuffled")}
    for c in claims:
        t = c["scope"].get("topic", "")
        same = [f for f in by_topic[t] if f["hash"] != c["id"]]
        other = [f for f in findings if f["topic"] != t]
        for arm, pool in (("same", same), ("cross", other)):
            for f in rng.sample(pool, min(pairs_per_claim, len(pool))):
                v = he.corroboration(c["text"], f"{f['title']} {f['abstract']}")
                rates[arm][v] += 1
        for _ in range(pairs_per_claim):  # word salad of abstract-like length
            salad = " ".join(rng.choice(vocab) for _ in range(150))
            rates["shuffled"][he.corroboration(c["text"], salad)] += 1
    for arm, cnt in rates.items():
        n = sum(cnt.values())
        print(f"{arm:9s} n={n:6d}  +1={cnt[1]/n:.4f}  -1={cnt[-1]/n:.4f}  0={cnt[0]/n:.4f}")
    print("(descriptive; per-pair rates. Survival needs 3 cumulative +1 against ~all same-topic findings.)")


def cmd_survival(seed: int = 1):
    """Code-reading premise (stage_test): every run re-tests each active claim against
    ALL same-topic findings, and pass/fail counts accumulate across runs. So a claim
    with k_pos >= 1 positive partners and k_neg == 0 negative partners reaches
    passed >= 3 (status=survived, absorbing) within ceil(3 / k_pos) runs, whatever
    the partner says. This command counts claims meeting that condition with the
    real same-topic pool vs a size-matched pool drawn from OTHER topics."""
    findings, claims = load()
    rng = random.Random(seed)
    by_topic = defaultdict(list)
    for f in findings:
        by_topic[f["topic"]].append(f)
    def k(c, pool):
        v = [he.corroboration(c["text"], f"{f['title']} {f['abstract']}") for f in pool
             if f["hash"] != c["id"]]
        return sum(x > 0 for x in v), sum(x < 0 for x in v)
    print(f"{'topic':55s} {'claims':>6s} {'real: k+>=1,k-=0':>16s} {'cross-topic pool':>16s}")
    for topic in sorted(by_topic):
        cs = [c for c in claims if c["scope"].get("topic") == topic]
        other = [f for f in findings if f["topic"] != topic]
        real = sum(1 for c in cs if (lambda a: a[0] >= 1 and a[1] == 0)(k(c, by_topic[topic])))
        ctrl = sum(1 for c in cs if (lambda a: a[0] >= 1 and a[1] == 0)(
            k(c, rng.sample(other, min(len(other), len(by_topic[topic]))))))
        print(f"{topic[:55]:55s} {len(cs):6d} {real:16d} {ctrl:16d}")


def cmd_churn(n: int = 6):
    hyp = "hypothesis-engine/hypotheses"
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                          cwd=ENGINE).stdout.strip()
    commits = subprocess.run(["git", "log", "--format=%h %ad", "--date=short", f"-{n+1}", "--", hyp],
                             capture_output=True, text=True, cwd=root).stdout.split("\n")
    commits = [c.split() for c in commits if c.strip()]
    def show(c, f):
        r = subprocess.run(["git", "show", f"{c}:{hyp}/{f}"], capture_output=True, text=True, cwd=root)
        return r.stdout if r.returncode == 0 else ""
    def parse(t):
        m = re.search(r"\((\d+) surviving claims\)", t)
        return (int(m.group(1)) if m else 0,
                set(re.findall(r"^- \([\d.]+\) .*\[source\]\((.*?)\)$", t, re.M)),
                (re.search(r"^> (.*)$", t, re.M) or [None, ""])[1],
                re.sub(r"_Regenerated .*_", "", t))
    files = sorted(p.name for p in (ENGINE / "hypotheses").glob("*.md"))
    print("per-commit: +new supporting URLs / surviving count / body changed beyond timestamp")
    for f in files:
        cells = []
        for (c, d), (p, _) in zip(commits[:-1], commits[1:]):
            a, b = parse(show(p, f)), parse(show(c, f))
            cells.append(f"{d[5:]}:+{len(b[1]-a[1])}/{b[0]}{'' if a[3]!=b[3] else '(=)'}{'*' if a[2]!=b[2] else ''}")
        print(f"{f[:-3]:60s} " + " ".join(cells))
    print("(=) body identical except the timestamp line; * headline statement changed")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "relevance"
    arg = [int(a) for a in sys.argv[2:]]
    {"relevance": cmd_relevance, "control": cmd_control, "survival": cmd_survival,
     "churn": cmd_churn}[cmd](*arg)
