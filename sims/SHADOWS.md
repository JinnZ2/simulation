# Shadow register

Structure that exists but that nothing here can currently see. The name is the user's: *shadow
shapes* — patterns inferable the way dark matter is, from their effect on what we can measure
rather than from direct observation.

The analogy is load-bearing and worth being precise about. Dark matter was not proposed because
there was a gap in the sky. It was proposed because **two measurements that should have agreed
didn't** — galactic rotation curves against visible mass — and the discrepancy was systematic,
reproducible, and structured. That is the standard a shadow has to meet before it is worth anything:
a *residual*, not an absence.

There are infinitely many things nobody has measured, and almost all of them are nothing.

---

## Two kinds, kept apart on purpose

| | detected | named |
|---|---|---|
| basis | a residual in artifacts we already have | a person's judgement that a domain has no instrument |
| tool | [`shadow.py`](shadow.py) | this file, §2 |
| evidence | reported with every entry | none available by construction |
| failure mode | false positives from coincidence | unfalsifiable speculation |

Mixing them is how this kind of thinking goes wrong. A detected shadow can be checked. A named one
can only be argued about, and calling it "detected" would launder an opinion into a measurement.
`shadow.py` does the first and refuses the second.

---

## 1. Detected — what `shadow.py` looks for

Five detectors, each built around a specific residual. Run `python3 shadow.py`.

**Censoring.** A metric piling up at exactly one value that also appears as a config limit. That is
not a distribution, it is a wall, and everything past it is invisible by construction. *Found:*
`shape_csd`'s `tau_final` sits at the 600-step `recovery_max_t` ceiling in 93% of observations —
the recovery-time divergence is measured largely through a wall.

**Discretization.** Mesh parameters — grid size, timestep, epochs, probe counts — held fixed. The
answer is computed *on* that mesh, so its independence is asserted rather than shown. *Found:* `N`
in `fractal_basin`, later confirmed to move α by 0.08–0.15.

**Cross-sim.** A parameter one sim varies and another pins. This is the closest analogue here to the
rotation-curve argument: the residual is between two sims that should agree about what matters. If
varying a knob changed an answer over there, pinning it here is an untested assumption backed by
somebody else's measurement. *Found:* `hidden` in `kappa_eff`, later confirmed to change the
curvature profile qualitatively.

**Claim.** Assertions in a sim's `claim` that no refutation condition reaches. *Found:*
`fractal_basin`'s "the two-well boundary is not fractal" — asserted, never tested, and contradicted
by its own data while the verdict stood.

**Null monoculture.** Every sim carries exactly one null, so it excludes exactly one alternative
explanation. Every other explanation for the same signal is untested. `shape_csd`'s single null was
wrong in its geometry and it took a full successor generation to find out.

### Backtest

`python3 shadow.py --backtest` checks the detectors against three shadows this repo discovered the
hard way — `N` in `fractal_basin`, `hidden` and `epochs` in `kappa_eff` — using only artifacts that
existed *before* the follow-ups ran. All three are recovered.

That is the weakest test that could have failed. It shows the detectors aren't vacuous; it does not
show they find *new* shadows. For that, two independent finds since:

- `ep2_prereg`'s `detection_median_lead_differential_scan` pinned at one value in 67% of runs.
- **`shape_csd_g1`'s lead is right-censored at 0.7409** — the maximum the design can measure.
  Detection fires at the first compression past baseline, so "74% lead" means "at or before the
  first point we looked." Nobody noticed this by hand, including in the same session that produced
  the result.

### Known false positives

Stated so the output is read with the right suspicion:

- **Coincidental value matches.** A ceiling at 0.0 or 1.0 will match some config parameter by
  accident. The tool reports the pile-up but withholds attribution and says so.
- **Synonym gaps in the claim detector.** `refute_if` written in symbols (`|alpha(2N) − alpha(N)|`)
  against a claim written in words ("uncertainty exponent... converged") shows no overlap and gets
  flagged. `basin_convergence` trips this and is a false positive.
- **Name-based discretization matching** is a heuristic. `creep_per_step` is a physical rate that
  matches the pattern.

Claim and discretization findings are candidates for triage, not verdicts.

---

## 2. Named — no instrument exists

Hand-maintained. **Nothing here is detected**; each is a judgement that a domain the ecosystem
cares about has no measurement pointed at it. Sourced from the research notes rather than invented.

| shadow | why nothing sees it | nearest instrument |
|---|---|---|
| **Snap latency as an information channel** | `snap_information` proved the ringdown carries zero bits about load *by algebra*. notes/18 §3 argues the information lives in event *timing* and hysteresis loop shape. Nothing here measures either. | E-P8 in notes/15 — designed, never run |
| **The physical instrument's real noise floor** | Every sim's null models the apparatus as clean. `ep2_prereg`'s rigid arm has no load-dependent recovery time by construction; a printed frame will. All false-positive rates here are optimistic by an unknown factor. | the two-frame build itself |
| **Compression geometry** | `research/TODO.md` states five hypotheses about representational damage. `sims/` contains zero compression experiments. The entire charter is unmeasured. | notes/10 §2.1 says the geometry battery is stdlib-feasible at ≤256² |
| **Whether refutations are themselves reliable** | `shape_csd_g1` reversed its parent by fixing one control. How often is a refutation wrong? Five REFUTED verdicts here, one overturned, and no way to estimate the rate. | nothing — would need deliberate replication of refutations |
| **The gap between sim and print** | Every claim in `sims/` is about a model of an instrument. No physical measurement has ever entered this ledger. | GBCB's timestamped CSV contract |
| **Wada threshold in damping** | The fraction goes 8% → 0% between γ = 0.25 and 0.5, and 8% → 0% again when the grid doubles. Neither transition is located. Two shadows crossing. | a γ sweep at converged resolution |

### The register's own shadow

This table lists what its authors could think of. Domains nobody in this ecosystem has considered
are not in it, and there is no procedure here that would find them. That is not false modesty — it
is the actual limit of the method, and it is why §2 is separated from §1 rather than merged into a
single impressive-looking list.

---

## Why this belongs in `sims/` rather than in a notes file

Every shadow above, once located, becomes a pre-registration. `censoring` on `shape_csd_g1` says
extend the compression grid below 0.128. `discretization` on `fractal_basin` produced
`basin_convergence`, which refuted a SUPPORTED-and-replicated result. `cross_sim` on `kappa_eff`
produced `kappa_eff_g1`.

A shadow that does not turn into a refutation condition is just a feeling about the dark.
