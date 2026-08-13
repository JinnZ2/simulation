# Notes 18 — The flip as event: zoom states, snap information, shape specialization, coordination
2026-08-14 · responds to: "what if the flip became a zoom state / trigger? what information are
we missing? are different shapes useful for different meta-structures? coordination like a brain
across mitochondria, gut biome, proprioception?"
Anchors: snap-computing literature brief (verified); sims/snap_information_sim.py; HARNESS.md

## 1. The reframe: we've been treating the snap as the END of the experiment.
## The literature treats it as the BEGINNING of the signal.

Key verified anchors that reframe the instrument:
- **Gomez, Moulton & Vella, Nat. Phys. 13, 142 (2017)**: critical slowing down of elastic
  snap-through is a published, measured result with universal −1/4 (pseudo-bistable) and
  −1/2 (fold) power laws. **Our instrument's headline phenomenon is reproducible published
  physics** — which means our contribution isn't the effect, it's the *instrumentation and
  audit integration*. That strengthens, not weakens, the project.
- **Rinzel–Ermentrout / Izhikevich**: a Class I neuron spike IS a saddle-node escape event —
  the same normal form as our strut's snap. The spike is not a failure of the membrane; it is
  the neuron's *report*. Its latency encodes how close the input was to threshold; its period
  diverges as √λ near the bifurcation — the exact analog of our recovery-time divergence.
  (Flag: our strut is overdamped — the analogy holds at fold level, not limit-cycle level.)
- **Yasuda et al., Nature 598, 39 (2021)** and **Chen, Pauly & Reis, Nature 589, 386 (2021)**:
  bistable beams are working memory bits and logic gates in published mechanical computers.
- **Raney et al., PNAS 113, 9722 (2016)**: a chain of bistable elements transmits a bit
  *without attenuation*, each element re-amplifying from stored energy — the mechanical
  action potential.
- **Jiang, Korpas & Raney, Nat. Commun. 10, 128 (2019)**: bifurcation used directly as the
  decision element. Closest published work to "flip as trigger."

## 2. The zoom-state hypothesis — now with a mechanism

"Flip becomes a zoom state" is physically precise:

**Pre-snap**: k_eff → 0, natural frequency → 0, timescale diverges (Gomez 2017). The
instrument lives in SLOW time — it integrates, it accumulates, it is maximally sensitive
and maximally sluggish. Class-I-integrator regime.

**The snap**: order-unity geometry change in ~milliseconds, independent of how slow the
loading was. Timescale separation IS the function (Venus flytrap: Forterre et al. 2005;
LaMSA theory: Ilton et al., Science 360, 2018).

**Post-snap**: new well, new curvature, new natural frequency — my sim measured the
post-snap ringdown frequency recovering the landing-well stiffness to within 2.5%
(implied k=0.702 vs true 0.720). **The snap re-tunes the instrument's native timescale
and mode spectrum. It jumps from a slow integrator to a fast resonator.** That IS a zoom
transition: the same physical object changes its temporal resolution and its filter
characteristics discontinuously, and *announces the new operating point by ringing at it*.

Ecosystem reading: the cascade audit watches slow time; the snap hands off to a fast-time
observer. A two-timescale audit (slow CSD channel pre-snap, fast ringdown channel
post-snap) is a strictly better instrument than either alone — and the handoff event
itself is a ledger entry.

## 3. What information is the snap carrying that we're missing?

From the sim + literature, ranked by (bits × exploitability):

1. **Threshold-crossing bit** (1 bit, certain): "load crossed the fold since last reset."
   We currently log this and stop.
2. **Latency channel** (analog, the one we're missing): WHEN the snap happens, relative to
   ramp start, encodes distance-to-threshold via the −1/2 power law. A snapping element
   driven by a ramp is an analog-to-event-time converter — the same coding Class I neurons
   use. We have been measuring recovery time (pre-snap) but not snap latency (the event
   itself) as an information channel. **E-P8 candidate: ramp-rate sweep, fit
   t_snap ∝ ε^(−1/2), decode load from latency.**
3. **Landing-state self-report** (measured this session): post-snap ringdown frequency =
   landing-well stiffness, 2.5% error in sim. The event calibrates its own aftermath.
4. **Hysteresis loop shape = extrema history** (Preisach/Madelung; Terzi & Mungan,
   PRE 102, 2020 — rigorous): nested minor loops losslessly encode the ordered sequence
   of past load reversals, up to wiping-out. **The loop is not just a signature of
   bistability (E-P6); it is a memory trace of everything the strut has experienced.**
   E-P6 should be upgraded: after random load histories, try to RECONSTRUCT the extrema
   sequence from loop geometry. Flag: coupled arrays likely break pure return-point memory
   — and the *deviation* from RPM measures coupling strength (Sirote-Katz et al. 2024).
5. **What the toy sim says it does NOT carry**: in a symmetric double well, ringdown
   frequency is load-insensitive (MI(load; ringdown) = 0.22 bits of 3.46 max). The load
   information lives in latency and loop shape, not in post-snap frequency. Honest null.

## 4. The flip as trigger — three concrete trigger wirings

- **Physical**: the snap's energy release can mechanically trigger a downstream element
  (transition-front launch, Raney 2016). A 3-strut chain = non-attenuating mechanical
  wire; a Y-junction of two fronts = candidate AND gate (collision-based logic is an
  OPEN niche — no demonstrated mechanical transition-wave gates found in the literature.
  If we build one, it's novel.)
- **Informational**: the snap is the natural trigger for a ledger write + audit regime
  transition + sensor mode switch (phyphox fast-capture arm). Event-driven, not polled.
  Matches KPN/CALM reasoning from notes/11: the snap is a monotone, irrevocable fact —
  exactly the kind of event that needs no coordination protocol.
- **Architectural**: in GM terms, the snap is a hardware interrupt for the repair
  controller: "basin escape has occurred; re-anchor (JS policy) now, not at next
  scheduled check."

## 5. Shape specialization — grounding the fieldlink mapping

The GM fieldlink peer already assigns: data→ICOSA, parameter→DODECA, policy→OCTA,
confidence→TETRA, thermo→CUBE. That was a naming choice. Here is a *principled* version
— the assignment criterion derived from this session's trig brief:

| Shape | Vertices (=sensor channels) | Faces (=readout channels) | Symmetry | First invariant harmonic | Natural meta-structure |
|---|---|---|---|---|---|
| Tetrahedron | 4 | 4 | T_d | ℓ=3 | **Confidence/opinion substrate**: minimal simplex — 4 channels is exactly a subjective-logic opinion tetrad (b,d,u,a) or a 4-way regime simplex. Minimal = nothing spare = confidence. |
| Cube | 8 | 6 | O_h | ℓ=4 | **Thermo/lattice substrate**: Cartesian product structure; its vertex grid IS a 2×2×2 factorial design — thermo state spaces and lattice sims are cubic-native. |
| Octahedron | 6 | 8 | O_h | ℓ=4 | **Policy/failure dashboard** (current): 6 vertices = 3 antipodal PAIRS — natural for signed 3-axis control (±x,±y,±z = push/pull per axis). Polar dual of the cube: action dual to state. |
| Dodecahedron | 20 | 12 | I_h | ℓ=6 | **Parameter manifold**: 20 channels, golden-ratio dihedrals; highest vertex count per face — many parameters, few readouts = compression dashboard. |
| Icosahedron | 12 | 20 | I_h | ℓ=6 | **Data substrate**: 20 readout faces — maximum readout bandwidth; geodesic subdivision standard for sphere sampling (data lives on spheres: directional statistics, embeddings). |

Assignment rule: **match the shape's symmetry group to the signal's natural mode
decomposition; vertex count = input channels; face count = output channels; the first
invariant ℓ = the shape's "resolution floor" for invariant readout.** Note the
cube/octahedron and dodeca/icosa polar duals pair action↔state and parameter↔data —
the fieldlink pairing has geometric meaning after all: duals see the same symmetry from
opposite sides (vertices of one = faces of the other).

Falsifiable test of specialization: run the SAME distortion sim (notes/14) on all five
shapes; the claim predicts octahedron wins on 3-axis signed faults, tetrahedron on
4-way simplex faults, etc. Refuted if one shape dominates all fault classes — then
specialization is decorative.

## 6. Coordination: the brain doesn't centralize — and neither should we

The user's analogy is anatomically accurate in a specific, useful way: the brain does
NOT continuously poll mitochondria, gut, and proprioceptors. The verified architecture
(Sterling allostasis 1988/2004; Barrett & Simmons, Nat. Rev. Neurosci. 2015):

1. **Subsystems are autonomous integral-feedback loops.** Mitochondria regulate ATP
   locally; gut regulates motility locally; the calibration substrate (Barkai–Leibler)
   IS this principle. Each meta-structure/shape should run its own local loop with its
   own local fold-monitors. No shape reports its raw stream.
2. **What travels upward is EVENTS, not telemetry.** Afferent interoceptive traffic is
   sparse and event-like; the snap-as-spike framing gives the mechanical version. In the
   ecosystem: ledgers receive threshold-crossing entries, not time series.
3. **The coordinator predicts rather than reacts** (allostasis = predictive regulation;
   Conant–Ashby: the coordinator must contain a model of the subsystems' variety). The
   coordination layer's job: hold shape-models of each subsystem so that an event from
   the octahedron (policy dashboard snaps) can be *interpreted against* the state of the
   icosahedron (data substrate) — cross-shape inference.
4. **Consistency across shapes = the sheaf condition** (notes/11): each shape is a
   local chart; overlapping claims (e.g., policy and parameter dashboards both touch
   trust radius) must agree on overlaps or the discrepancy is itself a signal (cellular
   sheaf Laplacian kernel = global agreement). This is the rigorous version of
   "connecting and coordinating meta-structures."
5. **Timescale separation as the wiring rule** (Izhikevich fast–slow decomposition):
   fast shapes (snap events, ms–s) report to slow shapes (creep/thermo, hours);
   slow shapes set the thresholds of fast shapes (allostatic set-point adjustment).
   Hierarchy by timescale, not by authority.

Concrete architecture: five shape-instruments (or sim-charts) each running
local CSD/EWS + local ledger → event bus (snap/latency/loop-shape entries only) →
coordination layer holding the five shape-models + sheaf-consistency checker →
discrepancy events feed the cascade audit as a sixth signal class.

## 7. What this session added to the experiment queue
- **E-P8**: snap-latency channel — ramp sweep, t_snap ∝ ε^(−1/2) fit, decode load from
  event time. (The information channel we were missing.)
- **E-P6 upgrade**: loop-shape history reconstruction (RPM test); deviation-from-RPM as
  coupling meter once multiple struts exist.
- **Shape-specialization sim**: same fault battery across five platonic shapes
  (falsifies or grounds the fieldlink mapping).
- **Transition-wave gate**: Y-junction collision AND-gate — flagged as open niche in the
  literature; cheap to try once one strut works.
- **Two-timescale audit**: slow CSD channel + fast ringdown channel with the snap as
  handoff event — a cascade_audit v2 design.

## 8. Contested/honest flags
- Neuron analogy valid at fold level only (overdamped strut ≠ limit-cycle spike).
- RPM in coupled arrays: expected to break; the breakage is the measurement.
- "Snap = interoceptive signal": no quantitative literature; this is OUR contribution,
  anchored conceptually in Sterling/Barrett–Simmons only.
- Collision-based mechanical logic: undemonstrated in literature — novelty opportunity,
  not established fact.
- Toy-sim null: symmetric wells carry ~no load info in ringdown frequency (0.22/3.46
  bits); latency and loop shape are the real analog channels.
