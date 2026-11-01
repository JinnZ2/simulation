# Null model — lattice_anisotropy

Co-authored (Kavik + Claude, 2026-11-01). CC0. Written before run.py existed.

`isotropic_same_exposure`: arrival directions drawn isotropically and then filtered through the
SAME exposure as the sky being tested. The detection threshold is the 99th percentile of the
scanned statistic (max over the same orientation set) on these null skies -- the trials
correction for the scan. A null drawn with uniform exposure is also kept, only to show that
skipping the exposure correction lets uneven exposure fake a signal.
