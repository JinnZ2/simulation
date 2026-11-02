# Simulation hypothesis -- assumption register

STATUS: PROPOSED register, co-authored (2026-11-01). CC0.
Toys: [`../lattice_anisotropy/`](../lattice_anisotropy/), [`../render_ledger/`](../render_ledger/),
[`../ising_critical_slowing/`](../ising_critical_slowing/) (Sim Harness Standard v1, self-graded);
calculators in this folder. Index: [`README.md`](README.md).

## Filter

Engineerability. A claim that cannot fail costs the person making it nothing -- a luxury claim.
The burden of a cost accounting sits with the hypothesis. These files turn "we live in a
simulation" into numbers, named assumptions and failure cases.

## Assumptions every future calculation must state

```text
A1 observer set        humans / conscious beings (undefined) / any physical interaction.
                       If any interaction counts (decoherence), the render-on-observation
                       shortcut disappears: everything is always observed.
A2 substrate physics   the simulator runs on our physics. Otherwise no cost is computable and
                       the claim is untestable.
A3 irreversible        compute is irreversible. Reversible computation could approach zero
   compute             Landauer cost; then the energy budget below says nothing.
A4 lattice             geometry and orientation of any discrete space (see defaults below).
A5 known phases only   Earth-only, human-known phases. Plasma, exoplanet, unknown phases and
                       phases sensed by non-human knowers are omitted.
A6 consistency policy  keep a record / recompute with an offset / delete.
```

## Gaps

```text
G1 observer definition   no non-arbitrary definition of an observer: a free parameter that sets
                         the whole cost
G2 population tag        theories scoped to the human-observable read as universal (missing
                         population tag; cf. healing/SCOPE_TAG.md in AI-Consciousness-Sensors)
G3 non-human sensing     absent from observer accounting: phytochrome, gravitropism,
                         mechanosensing, volatile signaling, mycorrhizal networks, cephalopod
                         cognition
G4 phase-change cost     = entropy jump + compute to reach the transition (critical slowing).
                         The second term is not tabulated across domains -> a critical-exponent
                         table is needed (phase_change_entropy.py, ../ising_critical_slowing/)
G5 lattice test          needs an orientation scan and an exposure correction before real data
                         (../lattice_anisotropy/)
G6 deletion vs offset    only true deletion leaves a signature (inconsistent repeat
                         observations); no real-data test yet (../render_ledger/)
G7 Ising toy flaw        the T = 1.5, L = 32 autocorrelation value (83) in the first run was a
                         domain-trapping artifact of a random start; rerun from an ordered start
                         and record both (../ising_critical_slowing/)
```

## Reframe (PROPOSED)

Locality, symmetry/conservation and universality ARE the shortcuts a simulator would use.
"Simulation shortcut" and "physical law" predict the same structure, so the label adds no
testable content unless a signature that only one of them predicts is named (G6 is the one
candidate here: true deletion).

## Lattice: human defaults to state, not assume

```text
periodicity        quasicrystals are ordered but not periodic (Shechtman 1982 observation,
                   published 1984; Nobel 2011) VERIFY dates
cubic              chosen for computational convenience, not physics
regular spacing    causal sets: random (Poisson) sprinkling, no preferred directions. A
                   Beane-type anisotropy test (Beane, Davoudi & Savage 2012, VERIFY) returns
                   null even if spacetime is discrete
fixed / flat       a fixed flat background is assumed
mixed              discrete space with continuous time
```

## Extinction gap

Each lost lineage deletes an independent sampler of the world. Convergence counts run on
survivors only (survivorship bias). Cost asymmetry (DERIVED, order of magnitude):
deleting a ~1e10-bit genome at body temperature costs ~1e10 x k_B (310 K) ln 2 ~ 3e-11 J
(Landauer bound; landauer_budget.py); rebuilding it costs evolutionary time. The two differ by
many orders of magnitude.

## Open

Every figure here carries a source or VERIFY in the calculators. Synthetic results in the toys
are not observational results.
