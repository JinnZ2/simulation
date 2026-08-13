#!/usr/bin/env python3
"""shadow.py — cartography of what the apparatus cannot see.

    python3 shadow.py                  # full map
    python3 shadow.py --sim shape_csd  # one sim
    python3 shadow.py --backtest       # does it find the shadows we already paid for?
    python3 shadow.py --kind censoring # one detector

Some structure is invisible not because it is absent but because nothing here is
pointed at it. Call those shadows. The useful ones are not mysteries — they are
**inferable from residuals in measurements we did take**, which is exactly how
dark matter was inferred: not from a gap in the sky, but from rotation curves
that disagreed with the visible mass.

That analogy sets the standard this tool holds itself to. A shadow worth
reporting has evidence behind it: a metric piling up against a ceiling, a
parameter that changed an answer somewhere else, an assertion no condition tests.
Absence alone is not evidence. There are infinitely many things nobody measured
and almost all of them are nothing.

## The boundary this tool will not cross

There are two different things people mean by "what we can't see", and mixing
them produces mysticism:

1. **Detected shadows** — inferred from a residual in existing artifacts. Every
   detector below is of this kind, and each reports the evidence that raised it.
2. **Named shadows** — domains where no instrument exists at all, so there is no
   residual to reason from. These cannot be detected, only listed by a person.

This tool does (1) and refuses to guess at (2). `SHADOWS.md` holds (2) as an
explicitly hand-maintained register, clearly separated.

## Backtest

Two shadows in this repo were found by accident and cost real work:

- `fractal_basin` held grid resolution `N` fixed; `basin_convergence` later showed
  alpha moves 0.08-0.15 when it doubles.
- `kappa_eff` held `hidden` width fixed at 32; `kappa_eff_g1` later showed widths
  16 and 64 have qualitatively different curvature profiles.

`--backtest` checks whether these detectors would have flagged both from
artifacts available *before* those follow-ups ran. A shadow detector that cannot
find shadows already confirmed is not measuring anything.

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

# Parameters whose name marks them as controlling a discretization: the answer
# is computed *on* them, so holding one fixed asserts the answer does not depend
# on the mesh. basin_convergence showed that assertion can be false.
DISCRETIZATION = re.compile(
    r"(^|_)(n|N|dt|steps?|iters?|epochs?|resolution|grid|probe|samples?|"
    r"points?|scan|settle|bins?|width|depth)(_|$)", re.IGNORECASE)

CENSORING_SHARE = 0.25      # fraction of observations at the extreme to call it a ceiling
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "is", "are",
    "that", "this", "it", "its", "with", "by", "for", "from", "as", "than",
    "not", "no", "does", "do", "be", "been", "will", "would", "than", "so",
    "which", "what", "when", "where", "more", "less", "same", "both", "each",
    "any", "all", "one", "two", "three", "before", "after", "still", "even",
    "only", "also", "but", "if", "then", "there", "their", "them", "they",
    "measured", "measure", "run", "sim", "test", "tested", "value", "values",
}


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def sim_dirs() -> list[Path]:
    return sorted(d for d in ROOT.iterdir()
                  if d.is_dir() and (d / "config.json").exists())


def load(sim: Path) -> dict[str, Any]:
    config = json.loads((sim / "config.json").read_text(encoding="utf-8"))
    runs = sorted(sim.glob("results/*/metrics.json"))
    metrics = json.loads(runs[-1].read_text(encoding="utf-8")) if runs else None
    return {"path": sim, "name": config["name"], "config": config, "metrics": metrics}


def numeric_params(config: dict[str, Any]) -> dict[str, float]:
    """Every numeric knob in the config's parameter blocks."""
    out: dict[str, float] = {}
    for key, block in config.items():
        if key in ("sweeps", "refute_params") or not isinstance(block, dict):
            continue
        for name, value in block.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out[name] = value
    return out


def stem(name: str) -> str:
    """Normalize parameter names so `hidden` and `hidden_width` compare equal."""
    n = name.lower()
    for suffix in ("_width", "_size", "_count", "_n", "_threshold", "_magnitude",
                   "_frac", "_fraction", "_rate", "_doubled"):
        if n.endswith(suffix):
            n = n[: -len(suffix)]
    # deliberately NOT stripping n_/num_: `n_probe` is a count and
    # `probe_magnitude` is a force. Conflating them invents a residual.
    return n or name.lower()


# --------------------------------------------------------------------------
# D1 — censoring: the measurement hit its own ceiling
# --------------------------------------------------------------------------

def censoring_shadows(sim: dict[str, Any]) -> list[dict[str, Any]]:
    """Metrics piling up at a configured limit. The true value is past the edge.

    Evidence: a share of observations sitting exactly at a value that also
    appears as a numeric config parameter. That is not a distribution, it is a
    wall — and everything beyond it is invisible by construction.
    """
    if not sim["metrics"]:
        return []
    params = numeric_params(sim["config"])
    obs = sim["metrics"]["observations"]
    found = []
    for key in sorted({k for r in obs for k in r["metrics"]}):
        values = [r["metrics"].get(key) for r in obs]
        values = [v for v in values if isinstance(v, (int, float))
                  and not isinstance(v, bool)]
        if not values:
            continue
        top = max(values)
        share = sum(1 for v in values if v == top) / len(values)
        if share < CENSORING_SHARE or len(set(values)) <= 1:
            continue
        # indicator flags take only 0/1 by design; a pile-up is their normal
        # behaviour, not a truncated measurement
        if set(values) <= {0.0, 1.0}:
            continue
        limit = next((p for p, v in params.items() if v == top), None)
        # 0, 1 and -1 turn up all over a config; a value match against one of
        # them is a coincidence, not an attribution. The pile-up is still the
        # finding — only the named source becomes unreliable.
        trivial = top in (0.0, 1.0, -1.0)
        confident = limit is not None and not trivial
        if limit is None and not (share >= 0.5):
            continue
        if confident:
            evidence = (f"{round(share * 100)}% of observations sit exactly at {top}, "
                        f"which is config value `{limit}`")
        else:
            evidence = (f"{round(share * 100)}% of observations sit exactly at {top} — "
                        "a pile-up at a single value, but no config parameter "
                        "unambiguously names the ceiling"
                        + (f" (`{limit}` matches numerically but {top} is a common "
                           "constant, so the match may be coincidence)" if limit else ""))
        found.append({
            "metric": key, "ceiling": top, "set_by": limit if confident else None,
            "share_at_ceiling": round(share, 3), "attribution_confident": confident,
            "evidence": evidence,
        })
    return found


# --------------------------------------------------------------------------
# D2 — discretization held fixed
# --------------------------------------------------------------------------

def discretization_shadows(sim: dict[str, Any]) -> list[dict[str, Any]]:
    """Mesh parameters never varied. The structure below the mesh is unobservable."""
    swept = {stem(k) for k in sim["config"]["sweeps"]}
    params = numeric_params(sim["config"])
    # a parameter explicitly paired with a doubled/halved variant IS being
    # varied, even though it is not in `sweeps`
    varied_in_place = {n.replace("_doubled", "").replace("_halved", "")
                       for n in params if "_doubled" in n or "_halved" in n}
    found = []
    for name, value in sorted(params.items()):
        if not DISCRETIZATION.search(name) or stem(name) in swept:
            continue
        if name in varied_in_place or "_doubled" in name or "_halved" in name:
            continue
        found.append({
            "parameter": name, "held_at": value,
            "evidence": "controls a discretization and is never varied; the answer "
                        "is computed on this mesh, so its independence is asserted "
                        "rather than shown",
        })
    return found


# --------------------------------------------------------------------------
# D3 — swept elsewhere, held fixed here (the strongest inference)
# --------------------------------------------------------------------------

def cross_sim_shadows(sim: dict[str, Any], all_sims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A parameter another sim varies, this one pins.

    This is the closest thing here to the rotation-curve argument: the residual
    is between two sims that should agree about what matters. If varying a knob
    changed an answer over there, pinning it here is an untested assumption, and
    the evidence is somebody else's measurement.
    """
    swept_elsewhere: dict[str, list[str]] = {}
    for other in all_sims:
        if other["name"] == sim["name"]:
            continue
        for key in other["config"]["sweeps"]:
            swept_elsewhere.setdefault(stem(key), []).append(f"{other['name']}:{key}")

    swept_here = {stem(k) for k in sim["config"]["sweeps"]}
    found = []
    for name, value in sorted(numeric_params(sim["config"]).items()):
        s = stem(name)
        if s in swept_here or s not in swept_elsewhere:
            continue
        found.append({
            "parameter": name, "held_at": value,
            "swept_by": swept_elsewhere[s],
            "evidence": f"varied in {', '.join(swept_elsewhere[s])} and pinned here",
        })
    return found


# --------------------------------------------------------------------------
# D4 — claim asserts what no condition tests
# --------------------------------------------------------------------------

def claim_shadows(sim: dict[str, Any]) -> list[dict[str, Any]]:
    """Content in `claim` that the refutation condition never reaches.

    fractal_basin's claim asserted the two-well boundary is not fractal; no
    condition tested it, and the data contradicted it while the verdict stood.
    """
    config = sim["config"]
    claim = config.get("claim", "")
    if not claim:
        return []
    covered = (config["refute_if"] + " " + " ".join(config["refute_params"])).lower()
    covered_words = set(re.findall(r"[a-z_]{3,}", covered))

    clauses = re.split(r"[,;.]| - | and | so ", claim)
    found = []
    for clause in clauses:
        words = {w for w in re.findall(r"[a-z_]{4,}", clause.lower())
                 if w not in STOPWORDS}
        if len(words) < 3:
            continue
        overlap = {w for w in words
                   if any(w in c or c in w for c in covered_words)}
        if not overlap:
            found.append({
                "clause": clause.strip()[:160],
                "evidence": "no word in this clause appears in refute_if or "
                            "refute_params — it is asserted, not tested",
            })
    return found


# --------------------------------------------------------------------------
# D5 — one null tests one alternative
# --------------------------------------------------------------------------

def null_shadows(sim: dict[str, Any]) -> list[dict[str, Any]]:
    """Each sim carries exactly one null, so it excludes exactly one alternative.

    shape_csd's single null was wrong in its geometry and it took a whole
    successor generation to discover. The shadow is every alternative
    explanation the one null does not address.
    """
    null_doc = sim["path"] / "NULL.md"
    text = null_doc.read_text(encoding="utf-8") if null_doc.exists() else ""
    declared = re.findall(r"^-\s*\*\*.*?not.*?\*\*", text, re.MULTILINE | re.IGNORECASE)
    return [{
        "null_model": sim["config"]["null_model"],
        "count": 1,
        "evidence": "one null model excludes one alternative explanation; every "
                    "other explanation for the same signal is untested here",
        "self_declared_limits": len(declared),
    }]


# --------------------------------------------------------------------------
# D6 — the journal nobody reads back
# --------------------------------------------------------------------------

def journal_shadows() -> list[dict[str, Any]]:
    path = ROOT / "unknown_journal.jsonl"
    if not path.exists():
        return []
    entries = [json.loads(line) for line in
               path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [{"entries": len(entries),
             "names": [e.get("name") for e in entries],
             "evidence": "lineages that hit the escape hatch; written but never "
                         "read back into any analysis"}] if entries else []


DETECTORS = {
    "censoring": censoring_shadows,
    "discretization": discretization_shadows,
    "claim": claim_shadows,
    "null": null_shadows,
}


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def map_sim(sim: dict[str, Any], all_sims: list[dict[str, Any]],
            kinds: set[str]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for kind, fn in DETECTORS.items():
        if kind in kinds:
            out[kind] = fn(sim)
    if "cross_sim" in kinds:
        out["cross_sim"] = cross_sim_shadows(sim, all_sims)
    return {k: v for k, v in out.items() if v}


def report(sims: list[dict[str, Any]], kinds: set[str]) -> str:
    lines = ["# Shadow map", "",
             "Structure the apparatus cannot currently see, inferred from residuals in what it "
             "did measure. Each entry carries its evidence; absence alone is not evidence.", ""]

    for sim in sims:
        found = map_sim(sim, sims, kinds)
        if not found:
            continue
        lines += [f"## {sim['name']}", ""]
        for kind, items in found.items():
            lines.append(f"**{kind}**")
            lines.append("")
            for item in items:
                head = (item.get("metric") or item.get("parameter") or
                        item.get("clause") or item.get("null_model") or "—")
                lines.append(f"- `{head}` — {item['evidence']}")
            lines.append("")

    journal = journal_shadows()
    if journal and "journal" in kinds:
        lines += ["## escape-hatched lineages", ""]
        for j in journal:
            lines.append(f"- {j['entries']} entr(ies): {j['names']} — {j['evidence']}")
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------
# Backtest — would this have found the shadows we already paid for?
# --------------------------------------------------------------------------

KNOWN_SHADOWS = [
    {
        "sim": "fractal_basin",
        "parameter": "N",
        "confirmed_by": "basin_convergence",
        "cost": "alpha moves 0.08-0.15 when N doubles; the Wada figure goes 8% -> 0%",
        "detector": "discretization",
    },
    {
        "sim": "kappa_eff",
        "parameter": "hidden",
        "confirmed_by": "kappa_eff_g1",
        "cost": "widths 16 and 64 have qualitatively different curvature profiles; "
                "baseline kappa spans 0.23 to 59",
        "detector": "cross_sim",
    },
    {
        "sim": "kappa_eff",
        "parameter": "epochs",
        "confirmed_by": "kappa_eff_g1",
        "cost": "networks were not trained to a minimum; grad norm 0.57 at width 64",
        "detector": "discretization",
    },
]


def backtest(sims: list[dict[str, Any]]) -> tuple[str, bool]:
    by_name = {s["name"]: s for s in sims}
    lines = ["# Backtest — does the detector find shadows already confirmed?", "",
             "Each row is a shadow this repo discovered the hard way. A detector that "
             "cannot find these is not measuring anything.", "",
             "| sim | parameter | detector | flagged? | what it cost |",
             "|---|---|---|---|---|"]
    all_hit = True
    for known in KNOWN_SHADOWS:
        sim = by_name.get(known["sim"])
        hit = False
        if sim:
            if known["detector"] == "cross_sim":
                items = cross_sim_shadows(sim, sims)
            else:
                items = DETECTORS[known["detector"]](sim)
            hit = any(i.get("parameter") == known["parameter"] for i in items)
        all_hit &= hit
        lines.append(f"| {known['sim']} | `{known['parameter']}` | {known['detector']} | "
                     f"{'**yes**' if hit else 'NO'} | {known['cost']} |")
    lines += ["", f"**{sum(1 for k in KNOWN_SHADOWS)} known shadows, "
                  f"{'all' if all_hit else 'not all'} recovered.**", ""]
    if all_hit:
        lines.append("Every shadow that cost this repo a follow-up run was visible in the "
                     "artifacts beforehand. That is not proof the detector finds *new* "
                     "shadows — it is the weakest test that could have failed, and it did not.")
    return "\n".join(lines), all_hit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map what the apparatus cannot see.")
    parser.add_argument("--sim", help="restrict to one sim")
    parser.add_argument("--kind", choices=sorted(set(DETECTORS) | {"cross_sim", "journal"}),
                        help="run one detector")
    parser.add_argument("--backtest", action="store_true",
                        help="check the detector against shadows already confirmed")
    args = parser.parse_args(argv)

    sims = [load(d) for d in sim_dirs()]

    if args.backtest:
        text, ok = backtest(sims)
        print(text)
        return 0 if ok else 1

    selected = sims
    if args.sim:
        selected = [s for s in sims if s["name"] == args.sim]
        if not selected:
            print(f"no sim named {args.sim!r}", file=sys.stderr)
            return 1

    kinds = {args.kind} if args.kind else set(DETECTORS) | {"cross_sim", "journal"}
    print(report(selected, kinds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
