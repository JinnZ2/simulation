# Convergence ranking -- test design (PROPOSED, no sim yet)

Co-authored (2026-11-01). CC0. Part of [`SIMULATION_REGISTER.md`](SIMULATION_REGISTER.md).

## Question

Which candidate rules of the world are most load-bearing? Rank each by the number of INDEPENDENT
lineages that converged on it. A human-built model of the world is one sampling; independent
lineages are many.

## Candidate rules and example lineages (VERIFY each before counting)

```text
camera-type eye             cephalopods and vertebrates (independent origins)
branching flow networks     trees, river networks, lungs, vasculature, mycorrhizae;
                            Murray's law (1926) for vessel radii as the quantitative form
```

## Design

```text
1 rule list         pre-register the candidate rules and how each is recognised (a measurable
                    form, e.g. an exponent, not a resemblance)
2 lineage census    for each rule, list the lineages showing it, from a published phylogeny
3 independence      control for shared ancestry (Galton's problem): count only origins that a
                    phylogenetic reconstruction scores as separate; weight shared-ancestry
                    cases as one
4 rank              by independent origin count; report the measurable form's spread across
                    lineages, not only the count
5 null              rules picked at random from the same trait space: how many independent
                    origins does a rule get by chance?
refute_if (draft)   the top-ranked rules do not exceed the random-rule null by a pre-committed
                    margin
```

## Limits

- Survivorship: only surviving and fossilised lineages are counted (SIMULATION_REGISTER.md,
  extinction gap).
- "Recognised the same rule" is the weld point: define the measurable form before counting.

## Status

Design only. No data collected, no sim written.
