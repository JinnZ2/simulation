# Null model — snap_information

**Null model name:** `shuffle_load_labels`

## What the null does

Run the identical ensemble of snap-through trajectories, collect the `(load, ringdown_frequency)`
pairs, then randomly permute the load labels against the ringdown observations. Estimate mutual
information on the permuted pairing with exactly the same binning and estimator used on the real
pairing.

Nothing about the physics changes. Only the association between load and readout is destroyed.

## What result would mean "no effect"

The claim is that a snap event digitizes the accumulated analogue load — that observing the
post-snap ringdown tells you something about *when in the load cycle the snap happened*. The
natural statistic is mutual information `MI(load; ringdown)` in bits.

The trap: **a plug-in MI estimate on binned data is biased upward and is never zero.** With `n`
samples spread over a 5×5 contingency table, finite-sample noise alone produces
`MI ≈ (bins_x - 1)(bins_y - 1) / (2 n ln 2)` bits even when the two variables are genuinely
independent. Reporting a raw MI of, say, 0.3 bits as evidence of information transfer would be
reporting the estimator's bias.

So "no effect" is not `MI = 0`. It is `MI ≈ MI_null`, where `MI_null` is the same estimator applied
to the same data with the association shuffled out. The only defensible quantity is the **excess**:

```
ΔMI = MI(load; ringdown) - MI_null
```

`REFUTE.md` commits to how large ΔMI must be.

## Why shuffling rather than an analytic bias correction

The bias term above assumes a well-populated table and independent samples. Neither holds cleanly
here: the ringdown-frequency estimate is quantized by the FFT bin spacing, so the marginal is
lumpy, and quantile binning on a lumpy marginal produces uneven occupancy. A permutation null
inherits every one of those pathologies automatically. An analytic correction would not.

## Ceiling

With 11 distinct loads the information available is `log2(11) ≈ 3.46` bits, but the estimator bins
to 5 load bins, so the reachable maximum for this measurement is `log2(5) ≈ 2.32` bits. A result
near 2.32 means the readout is nearly a perfect decoder of the (binned) load; a result near
`MI_null` means it carries nothing the shuffle does not.
