# Refutation condition — lattice_anisotropy

Co-authored (Kavik + Claude, 2026-11-01). CC0. **Written before run.py existed.** Generation 0,
MEASURE. Source: work order WO3 #3 and SIMULATION_REGISTER.md G5. SYNTHETIC skies only; no
observational data (the Auger release was unreachable 2026-11-01; auger_loader_stub.py refuses).

## Statistic

For a lattice orientation R, S(R) = mean over events of (x^4 + y^4 + z^4) in the lattice frame
(a cubic harmonic; isotropic mean 3/5; rises when events cluster on lattice axes). Scanned
statistic = max over 16 fixed random orientations. Threshold = 99th percentile of the scanned
statistic on 150 null skies.

## Skies (40 per condition per seed)

- isotropic, uniform exposure
- aligned: a fraction f of events within ~5 deg of a random lattice's axes (lattice orientation
  random per sky, not on the scan grid)
- dipole: flux proportional to 1 + 0.065 cos(angle to a random direction) (Auger-like amplitude)
- uneven exposure: Auger-like declination weighting, tested against the same-exposure null
  (corrected) and against the uniform-exposure null (uncorrected)

## Refute if — any, at >= 3 of 5 seeds

- false alarm > 0.05 on the dipole
- false alarm > 0.05 on exposure-corrected uneven-exposure skies
- power < 0.5 at n = 2000, f = 0.10

INCONCLUSIVE if the UNCORRECTED uneven-exposure case does not exceed 0.05 false alarm at >= 4 of
5 seeds: the required negative case would then have tested nothing. SUPPORTED requires every
part at >= 4 of 5 seeds.

## Reported, not graded

Power at every (n, f): where the statistic stops seeing the signal (first run, other code:
n = 500 caught only at >= 10% aligned; n = 3000 caught 75% at 3%).
