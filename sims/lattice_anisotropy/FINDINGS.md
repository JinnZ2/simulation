# Findings — lattice_anisotropy

Co-authored (Kavik + Claude, 2026-11-01). CC0. SYNTHETIC skies; no observational data.

**INCONCLUSIVE**, by the pre-committed rule: the required negative case did not fire. Without the
exposure correction, uneven exposure raised the false-alarm rate to at most 0.025 -- under the
0.05 the case needed to exceed. A correction cannot be shown necessary by a case that does not
fail without it.

```text
                                n = 500            n = 2000
power, f = 0.10 aligned         0.38 - 0.60        0.90 - 0.975   (claim: >= 0.5 at n=2000)
power, f = 0.03 aligned         0.00 - 0.10        0.08 - 0.28    (detection limit)
false alarm, 6.5% dipole        0.00 - 0.10        0.00 - 0.03
false alarm, exposure corrected 0.00               0.00 - 0.05
false alarm, exposure UNcorr.   0.00 - 0.03        0.00 - 0.03    (needed > 0.05: did not fire)
false alarm, isotropic null     0.00 - 0.05 over 20 runs of 40 skies (target 0.01)
```

## Reading

- The scan-plus-trials statistic sees a 10% axis-aligned fraction at n = 2000 with high power,
  and does not fire on a 6.5% dipole (one seed 0.10 at n = 500 = 4 of 40 skies; sampling noise
  at this sky count).
- The Auger-like exposure modelled here depends on declination only -- symmetric about the
  polar axis. Reading (PROPOSED, untested): the 4th-order cubic statistic, maximised over 16
  orientations, picks that symmetry up only weakly at n <= 2000. So this run does NOT show that
  uneven exposure fakes a lattice signal, and does NOT show that it cannot.
- First run (other code, 1% false alarm): n = 500 caught only at >= 10% aligned; n = 3000 caught
  75% at 3%; n = 20000 caught 66% at 1%. Same direction here: n = 2000 at 3% caught <= 28%.

## Successor, not an edit

A new pre-registration with an exposure that the statistic can see (e.g. a declination cut plus
an azimuthal / right-ascension modulation, or larger n), so the negative case has power; then
the corrected / uncorrected comparison means something. Real data: blocked (Auger release
unreachable; stub refuses).
