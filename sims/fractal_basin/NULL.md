# Null model — fractal_basin

**Null model name:** `shuffle_labels`

## What the null does

Take the measured basin grid — the array assigning each initial condition `(x, v)` to the well it
eventually settles in — and randomly permute the labels across grid cells. Cell *contents* are
preserved (the same number of cells belong to each basin) but all spatial structure is destroyed.

The uncertainty exponent is then measured on the shuffled grid by exactly the same procedure used
on the real one.

## What result would mean "no effect"

The uncertainty exponent α comes from how the fraction of ε-uncertain initial conditions scales
with probe separation:

```
f(ε) ~ ε^α
```

- **Smooth boundary:** doubling measurement precision halves the uncertain fraction → **α = 1**,
  boundary dimension `D = 2 - α = 1`.
- **Fractal boundary:** precision buys less than proportional certainty → **0 < α < 1**, `D > 1`.
- **No spatial structure at all** (the null): whether two nearby cells share a label is independent
  of how near they are, so `f(ε)` is flat in ε → **α ≈ 0**.

So the null pins the *floor*, not the ceiling. A shuffled grid looks maximally "fractal" by this
statistic while containing no dynamics whatsoever. This is precisely why the null is mandatory
here: a small α is not by itself evidence of a fractal basin boundary. It is only evidence if it
sits clearly **above** the shuffled floor while remaining clearly **below** the smooth value of 1.

## The three-way discrimination this sets up

| | α | meaning |
|---|---|---|
| null (`shuffle_labels`) | ≈ 0 | no spatial structure |
| **fractal boundary** | **0 < α < 1** | the claim |
| smooth boundary | ≈ 1 | structure, but not fractal |

A result is only interesting if it lands in the middle band, and the distance to *both* edges has
to be checked. `REFUTE.md` commits to how far.

## Secondary measure: Wada

The Wada fraction — boundary cells whose neighbourhood touches all three basins — has its own null.
Under `shuffle_labels` with three roughly equal basins, a small neighbourhood of a shuffled grid
touches all three labels with high probability, so the shuffled Wada fraction is *high*. As with α,
the shuffled value is the structureless reference, not the "no effect" direction. Wada is reported
as a descriptive secondary and is not part of the refutation condition.
