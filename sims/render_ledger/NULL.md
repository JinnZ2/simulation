# Null model — render_ledger

Co-authored (Kavik + Claude, 2026-11-01). CC0. Written before run.py existed.

`full_compute`: every cell is computed at every step, whatever is observed. Saving = 0 by
definition, contradictions = 0. A render-on-observation policy shows an effect only where it
departs from this: a saving greater than 0, or a contradiction rate greater than 0.

The null is run at every sweep point so the grader compares like with like.
