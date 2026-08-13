#!/usr/bin/env python3
"""explore.py — recycle refuted claims into candidate successor experiments.

    python3 explore.py                      # report on every sim
    python3 explore.py --sim shape_csd      # one sim
    python3 explore.py --hidden             # hidden-variable scan only
    python3 explore.py --cross-domain       # cross-domain transfer only
    python3 explore.py --scaffold shape_csd # write a successor candidate folder

A refuted claim is the most informative thing this folder produces, and it is
currently a dead end: the verdict lands, FINDINGS.md says what went wrong, and
nothing carries that forward. This walks the gap between "we know why it failed"
and "here is the next pre-registration."

Stdlib only.

## What this tool will not do

It does not write refutation conditions, and it does not run anything.

That restraint is the whole design. A tool that automatically reformulated a
claim until it passed would be an engine for exactly the behaviour HARNESS.md §4
exists to prevent, and it would be *fast* at it. So `--scaffold` emits a folder
whose `refute_if` is deliberately empty — `harness/manifest.py` refuses to load
it — and a REFUTE.md of TODO prompts carrying the diagnosis forward. A human
writes the condition, or the successor never runs.

## The guards

1. **Only refuted or inconclusive claims may be recycled.** This mirrors the
   falsification ledger's `refute()` gate (notes/08 §A.3): a claim that has not
   been refuted cannot be retuned. Recycling a SUPPORTED claim is refused.
2. **Lineage is tracked and bounded.** Successors carry `derived_from` and
   `generation`. At generation 3 the escape hatch fires: the lineage is written
   to `unknown_journal.jsonl` and no further successor is scaffolded. This is
   the same threshold `hypothesis-engine/scripts/hypothesis_engine.py` uses for
   claim reformulation, and it exists for the same reason — a claim patched
   three times is not converging on truth, it is dodging.
3. **Successors are EXPLORATORY.** Scaffolded configs carry `exploratory: true`,
   which `harness/runner.py` already stamps onto the ledger entry. A claim
   reformulated after seeing data never re-enters the ledger as a PREDICT.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
UNKNOWN_JOURNAL = ROOT / "unknown_journal.jsonl"

RECYCLABLE = ("REFUTED", "INCONCLUSIVE")
ESCAPE_HATCH_GENERATION = 3
CORRELATION_THRESHOLD = 0.5      # matches the HND trigger in hypothesis_engine.py


# --------------------------------------------------------------------------
# Cross-domain transfer table, from notes/08 Part B
# --------------------------------------------------------------------------
# The eight domains whose governing equations instantiate the cusp/fold normal
# form directly, per notes/08's cross-cutting observations. A sim whose claim
# rests on fold structure is making a claim about a shape that recurs in all of
# them, so a refutation here is a testable prediction there.

CUSP_DOMAINS = {
    "B1 structural mechanics": "Euler buckling; post-buckling with lateral load maps to "
                               "x' = h + rx - x^3, P/P_cr is the control parameter",
    "B2 thermodynamics": "van der Waals spinodal from (dP/dV)_T = 0; coexistence is literally a cusp",
    "B5 chemistry": "Semenov thermal runaway; heat-balance tangency is a saddle-node",
    "B7 climate tipping": "ice-albedo fold with hysteresis; Stommel AMOC saddle-node under freshwater forcing",
    "B8 ecology": "strong Allee effect; harvest fold at critical effort r(1-A/K)^2/4",
    "B14 power grids": "voltage nose curve; Jacobian singularity is the fold",
    "B26 materials": "Griffith criterion; crack-growth fold in (stress, crack length)",
    "B29 fisheries": "Gordon-Schaefer MSY; overfishing past MSY is a fold with hysteresis",
}

# Structural signatures a sim can carry, and what transfers with them.
SIGNATURES = {
    "fold": {
        "match": ("snap", "fold", "csd", "critical slowing", "bistable", "saddle-node",
                  "spinodal", "basin"),
        "transfers_to": "the eight cusp-structured domains in notes/08 Part B",
        "shared_object": "the saddle-node normal form x' = h + rx - x^3, spinodal h* = 2/sqrt(27)",
        "note": "notes/17 §0 argues these are the same mathematics rather than an analogy: "
                "the Jeans instability growth time and our recovery time share the -1/2 exponent.",
    },
    "information_channel": {
        "match": ("mutual information", "bits", "encode", "decode", "adc", "report", "latency"),
        "transfers_to": "B21 information theory (channel capacity, MI degradation as EWS)",
        "shared_object": "MI(X;Y) with a permutation null; Shannon-Hartley as the hard ceiling",
        "note": "notes/18 §3 ranks snap information channels by (bits x exploitability): "
                "threshold bit, latency, landing-state self-report, hysteresis loop shape.",
    },
    "curvature": {
        "match": ("curvature", "hessian", "kappa", "stiffness", "sharpness"),
        "transfers_to": "notes/09 §2.2 information geometry — OBS/GPTQ as quasi-Fisher corrections",
        "shared_object": "the Fisher-Rao metric; prune/quantize along low-curvature directions",
        "note": "the same 'curvature predicts damage' claim underwrites second-order "
                "compression methods; a refutation here is worth checking there.",
    },
    "detector": {
        "match": ("detection", "false positive", "lead", "warning", "alarm", "indicator"),
        "transfers_to": "notes/12 S6 marker batteries; CDT's six-signal cascade audit",
        "shared_object": "sensitivity/specificity under a pre-registered kill criterion",
        "note": "notes/12 S6 measured var-tau at 60% detection and AC1-tau at 47% with 0% "
                "false alarms — the battery's value was additive coverage, not individual reliability.",
    },
}


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def sim_dirs() -> list[Path]:
    return sorted(d for d in ROOT.iterdir()
                  if d.is_dir() and (d / "config.json").exists())


def latest_metrics(sim: Path) -> dict[str, Any] | None:
    runs = sorted(sim.glob("results/*/metrics.json"))
    if not runs:
        return None
    return json.loads(runs[-1].read_text(encoding="utf-8"))


def load_sim(sim: Path) -> dict[str, Any] | None:
    metrics = latest_metrics(sim)
    if metrics is None:
        return None
    config = json.loads((sim / "config.json").read_text(encoding="utf-8"))
    findings = (sim / "FINDINGS.md")
    return {
        "path": sim,
        "name": config["name"],
        "config": config,
        "metrics": metrics,
        "findings": findings.read_text(encoding="utf-8") if findings.exists() else "",
    }


# --------------------------------------------------------------------------
# Hidden-variable scan
# --------------------------------------------------------------------------

def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def graded_metric_names(sim: dict[str, Any]) -> set[str]:
    """Metric names the verdict actually depended on.

    Approximated by name overlap with refute_params keys and with the words in
    the refute_if prose — the config does not record the mapping explicitly.
    """
    config = sim["config"]
    words = set(re.findall(r"[a-z_]{4,}", config["refute_if"].lower()))
    words |= {k.lower() for k in config["refute_params"]}
    graded = set()
    for row in sim["metrics"]["observations"]:
        for key in row["metrics"]:
            k = key.lower()
            if any(w in k or k in w for w in words):
                graded.add(key)
    return graded


def hidden_variables(sim: dict[str, Any]) -> list[dict[str, Any]]:
    """Recorded-but-ungraded metrics that track the swept parameter.

    Same instrument as the hypothesis engine's HND stage: correlate a candidate
    exogenous series against the thing the claim is about, and flag |r| above
    threshold. A strong correlate that no refutation condition mentions is
    either a confound or the measurement someone should have made instead.
    """
    obs = sim["metrics"]["observations"]
    if not obs:
        return []
    sweeps = list(obs[0]["sweep"])
    graded = graded_metric_names(sim)
    all_metrics = sorted({k for r in obs for k in r["metrics"]})

    def series(key: str) -> list[float] | None:
        values = [r["metrics"].get(key) for r in obs]
        if any(v is None or isinstance(v, bool) or
               (isinstance(v, float) and math.isnan(v)) for v in values):
            return None
        return [float(v) for v in values]

    graded_series = {g: s for g in graded if (s := series(g)) and len(set(s)) > 1}

    found = []
    for key in all_metrics:
        if key in graded:
            continue
        values = series(key)
        if values is None or len(set(values)) <= 1:
            continue

        # A metric that is an affine transform of a graded one (d_boundary = 2 - alpha)
        # is a restatement, not a hidden variable. Flag it so the list stays honest;
        # |r| = 1 against a graded metric is the giveaway.
        restatement = next(
            (g for g, gs in graded_series.items() if abs(abs(pearson(gs, values)) - 1.0) < 1e-6),
            None)

        for sweep_key in sweeps:
            xs = [float(r["sweep"][sweep_key]) for r in obs]
            r = pearson(xs, values)
            if abs(r) > CORRELATION_THRESHOLD:
                found.append({
                    "metric": key, "against": sweep_key, "r": round(r, 3),
                    "spread": [round(min(values), 4), round(max(values), 4)],
                    "restates": restatement,
                })
    # genuine candidates first, restatements after
    return sorted(found, key=lambda f: (f["restates"] is not None, -abs(f["r"])))


# --------------------------------------------------------------------------
# Cross-domain transfer
# --------------------------------------------------------------------------

def signatures_of(sim: dict[str, Any]) -> list[str]:
    text = (sim["config"].get("claim", "") + " " + sim["config"]["name"] + " " +
            sim["config"]["refute_if"]).lower()
    return [name for name, sig in SIGNATURES.items()
            if any(token in text for token in sig["match"])]


def cross_domain(sim: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for name in signatures_of(sim):
        sig = SIGNATURES[name]
        entry = {"signature": name, "transfers_to": sig["transfers_to"],
                 "shared_object": sig["shared_object"], "note": sig["note"]}
        if name == "fold":
            entry["domains"] = CUSP_DOMAINS
        out.append(entry)
    return out


# --------------------------------------------------------------------------
# Successor extraction
# --------------------------------------------------------------------------

def _clip(text: str, limit: int) -> str:
    """Truncate on a word boundary, not mid-word."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


SUCCESSOR_HEADINGS = re.compile(
    r"^#+\s*(.*(?:corrected|would (?:look|require)|next|consequence|rebuild|"
    r"what a real test|not eliminated|confound).*)$",
    re.IGNORECASE | re.MULTILINE)


def successor_leads(sim: dict[str, Any]) -> list[dict[str, str]]:
    """Pull the 'what to do instead' sections out of FINDINGS.md.

    Text extraction, not inference. It surfaces what a person already wrote when
    they diagnosed the failure; it does not decide what the next claim is.
    """
    text = sim["findings"]
    if not text:
        return []
    leads = []
    for match in SUCCESSOR_HEADINGS.finditer(text):
        start = match.end()
        nxt = text.find("\n## ", start)
        body = text[start:nxt if nxt != -1 else len(text)].strip()
        # Bullets in these documents wrap across lines; join continuations into
        # the item they belong to rather than truncating mid-sentence.
        items: list[str] = []
        for line in body.splitlines():
            if re.match(r"^\s*(?:[-*]|\d+\.)\s+\S", line):
                items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line).strip())
            elif items and line.strip() and not line.startswith(("#", "|", ">")):
                items[-1] += " " + line.strip()
        items = [re.sub(r"\*\*|`", "", i).strip() for i in items]
        leads.append({"heading": match.group(1).strip(),
                      "items": items[:6],
                      "prose": _clip(" ".join(body.split()), 400) if not items else ""})
    return leads


# --------------------------------------------------------------------------
# Lineage and the escape hatch
# --------------------------------------------------------------------------

def lineage_of(sim: dict[str, Any]) -> tuple[str | None, int]:
    config = sim["config"]
    return config.get("derived_from"), int(config.get("generation", 0))


def escape_hatch(sim: dict[str, Any], generation: int) -> dict[str, Any]:
    entry = {
        "type": "ESCAPE_HATCH",
        "name": sim["name"],
        "generation": generation,
        "claim": sim["config"].get("claim", ""),
        "verdict": sim["metrics"]["verdict"],
        "reason": f"lineage reached generation {generation}; a claim reformulated "
                  f"{ESCAPE_HATCH_GENERATION} times is not converging",
        "lineage": sim["config"].get("derived_from"),
    }
    with UNKNOWN_JOURNAL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


# --------------------------------------------------------------------------
# Scaffolding a successor
# --------------------------------------------------------------------------

def scaffold(sim: dict[str, Any], dest_name: str | None = None) -> Path:
    verdict = sim["metrics"]["verdict"]
    if verdict not in RECYCLABLE:
        raise SystemExit(
            f"refusing to recycle {sim['name']}: verdict is {verdict}.\n"
            "Only a refuted or inconclusive claim may be reformulated — the same gate "
            "the falsification ledger's refute() applies. Retuning a claim that "
            "survived its test is how claims stop meaning anything.")

    _, generation = lineage_of(sim)
    next_gen = generation + 1
    if next_gen >= ESCAPE_HATCH_GENERATION:
        entry = escape_hatch(sim, next_gen)
        raise SystemExit(
            f"escape hatch fired for {sim['name']} at generation {next_gen}.\n"
            f"Written to {UNKNOWN_JOURNAL.name}; no successor scaffolded.\n"
            f"{entry['reason']}.")

    dest = ROOT / (dest_name or f"{sim['name']}_g{next_gen}")
    if dest.exists():
        raise SystemExit(f"{dest.name} already exists — pick another name with --as")
    dest.mkdir(parents=True)

    hidden = hidden_variables(sim)
    leads = successor_leads(sim)
    transfers = cross_domain(sim)

    config = {
        "name": dest.name,
        "claim": "TODO — state the reformulated claim. It must differ from the parent's "
                 "in substance, not only in threshold.",
        "seeds": sim["config"]["seeds"],
        "sweeps": sim["config"]["sweeps"],
        "null_model": "TODO — name the null. If you cannot name it you do not have an experiment.",
        "refute_if": "",
        "refute_params": {"refute_at_seeds": 3, "support_at_seeds": 4},
        "tier": sim["config"].get("tier", 0),
        "runtime_estimate_s": sim["config"].get("runtime_estimate_s", 60),
        "depends_on": [sim["name"]],
        "derived_from": sim["name"],
        "generation": next_gen,
        "exploratory": True,
    }
    (dest / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Refutation condition — {dest.name}",
        "",
        f"**Successor to `{sim['name']}` (generation {next_gen}), which was "
        f"{verdict}.** Scaffolded by `explore.py`; every TODO below is for a person.",
        "",
        "> This entry is **EXPLORATORY** and will be stamped as such in the ledger. A claim "
        "reformulated after seeing data never re-enters as PREDICT (HARNESS.md §4).",
        "",
        "## Why the parent failed",
        "",
        f"> {sim['metrics']['reason']}",
        "",
        "## TODO — the reformulated claim",
        "",
        "State it, then state what would refute it. `config.json` ships with an empty "
        "`refute_if`, so `harness/manifest.py` will refuse to load this sim until you "
        "write one. That refusal is deliberate.",
        "",
        "- [ ] Claim differs from the parent in substance, not just in threshold",
        "- [ ] Null model named",
        "- [ ] Refutation condition quantitative and pre-committed",
        "- [ ] Committed to git *before* `run.py` exists",
        "",
    ]

    if leads:
        lines += ["## Leads carried over from the parent's FINDINGS.md", ""]
        for lead in leads:
            lines.append(f"### {lead['heading']}")
            lines.append("")
            if lead["items"]:
                lines += [f"- {item}" for item in lead["items"]]
            else:
                lines.append(lead["prose"])
            lines.append("")

    if hidden:
        lines += [
            "## Hidden-variable candidates",
            "",
            "Recorded by the parent, correlated with a swept parameter, and named by no "
            "refutation condition. Each is either a confound or the measurement that should "
            "have been graded.",
            "",
            "| metric | vs | r | range |",
            "|---|---|---:|---|",
        ]
        lines[-2] = "| metric | vs | r | range | note |"
        lines[-1] = "|---|---|---:|---|---|"
        for h in hidden:
            note = f"restates `{h['restates']}`" if h["restates"] else "candidate"
            lines.append(f"| `{h['metric']}` | {h['against']} | {h['r']} | "
                         f"{h['spread'][0]} – {h['spread'][1]} | {note} |")
        lines.append("")

    if transfers:
        lines += ["## Cross-domain transfer", "",
                  "The parent's structure recurs elsewhere. These are prompts, not evidence.", ""]
        for t in transfers:
            lines += [f"**{t['signature']}** → {t['transfers_to']}  ",
                      f"shared object: {t['shared_object']}  ",
                      f"{t['note']}", ""]
            for domain, desc in t.get("domains", {}).items():
                lines.append(f"- *{domain}* — {desc}")
            if t.get("domains"):
                lines.append("")

    (dest / "REFUTE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (dest / "NULL.md").write_text(
        f"# Null model — {dest.name}\n\n"
        f"**TODO.** The parent `{sim['name']}` was {verdict} because:\n\n"
        f"> {sim['metrics']['reason']}\n\n"
        "Name the null before writing any measurement code. State what result would mean "
        "'no effect', and say why the obvious alternative explanation is excluded by it.\n\n"
        f"The parent's null was `{sim['config']['null_model']}`. If you are reusing it, say "
        "why it is still the right control for a different claim; if you are replacing it, "
        "say what the old one failed to exclude.\n", encoding="utf-8")

    return dest


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def report(sims: list[dict[str, Any]], show_hidden: bool, show_cross: bool) -> str:
    out: list[str] = ["# Exploration report", ""]
    recyclable = [s for s in sims if s["metrics"]["verdict"] in RECYCLABLE]
    out += [f"{len(sims)} sim(s) with results; {len(recyclable)} recyclable "
            f"(REFUTED or INCONCLUSIVE).", ""]

    for sim in sims:
        verdict = sim["metrics"]["verdict"]
        _, generation = lineage_of(sim)
        out += [f"## {sim['name']} — {verdict}" +
                (f" (generation {generation})" if generation else ""), ""]

        if verdict not in RECYCLABLE:
            out += ["Not recyclable. A claim that survived its test may not be reformulated.", ""]
        else:
            out += [f"> {sim['metrics']['reason']}", ""]
            if generation + 1 >= ESCAPE_HATCH_GENERATION:
                out += [f"**Escape hatch would fire** — generation {generation + 1} reaches the "
                        f"limit of {ESCAPE_HATCH_GENERATION}. `--scaffold` will journal this "
                        "lineage instead of extending it.", ""]
            else:
                out += [f"Scaffold a successor: `python3 explore.py --scaffold {sim['name']}`", ""]
            leads = successor_leads(sim)
            if leads:
                out += ["**Leads in FINDINGS.md:** " +
                        "; ".join(lead["heading"] for lead in leads), ""]

        if show_hidden:
            hidden = hidden_variables(sim)
            if hidden:
                out += ["**Hidden-variable candidates** (ungraded, |r| > "
                        f"{CORRELATION_THRESHOLD}):", ""]
                for h in hidden:
                    tail = (f"  — restates `{h['restates']}`, not a hidden variable"
                            if h["restates"] else "")
                    out.append(f"- `{h['metric']}` vs {h['against']}: r = {h['r']}, "
                               f"range {h['spread'][0]} – {h['spread'][1]}{tail}")
                out.append("")
            else:
                out += ["No ungraded metric correlates with a swept parameter above "
                        f"|r| = {CORRELATION_THRESHOLD}.", ""]

        if show_cross:
            transfers = cross_domain(sim)
            if transfers:
                out += ["**Cross-domain transfer:** " +
                        "; ".join(f"{t['signature']} → {t['transfers_to']}"
                                  for t in transfers), ""]

    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recycle refuted claims into candidate successor experiments.")
    parser.add_argument("--sim", help="restrict to one sim by name")
    parser.add_argument("--hidden", action="store_true", help="hidden-variable scan only")
    parser.add_argument("--cross-domain", action="store_true", help="cross-domain transfer only")
    parser.add_argument("--scaffold", metavar="SIM", help="write a successor candidate folder")
    parser.add_argument("--as", dest="as_name", help="name for the scaffolded folder")
    args = parser.parse_args(argv)

    loaded = [s for s in (load_sim(d) for d in sim_dirs()) if s]
    if args.sim:
        loaded = [s for s in loaded if s["name"] == args.sim]
        if not loaded:
            print(f"no sim named {args.sim!r} with results", file=sys.stderr)
            return 1

    if args.scaffold:
        target = next((s for s in loaded if s["name"] == args.scaffold), None)
        if target is None:
            print(f"no sim named {args.scaffold!r} with results", file=sys.stderr)
            return 1
        dest = scaffold(target, args.as_name)
        print(f"scaffolded {dest.relative_to(ROOT)}/")
        print("  config.json  — refute_if is EMPTY; the harness will refuse to run it")
        print("  REFUTE.md    — TODO prompts, carried-over leads, hidden variables")
        print("  NULL.md      — TODO")
        print("\nWrite the refutation condition, commit it before run.py exists, then build the sim.")
        return 0

    # default: both analyses unless one is asked for specifically
    show_hidden = args.hidden or not args.cross_domain
    show_cross = args.cross_domain or not args.hidden
    print(report(loaded, show_hidden, show_cross))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
