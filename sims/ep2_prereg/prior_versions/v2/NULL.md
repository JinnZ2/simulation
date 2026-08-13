# Null model: rigid-strut control arm
An identical frame whose 12th strut is rigid (no fold, no snap). It experiences the
same compression steps, same dwell, same creep, same flick protocol, same timing noise.
Recovery time in the null stays flat except for creep drift.

Meaning of "no effect": the t-test detection procedure fires on the null at the same
rate as on the bistable arm. If so, E-P2's detection is an artifact of creep drift +
statistics, not critical slowing down.

Implementation: tau_null(comp) = tau0 * (1 + small creep drift), no fold divergence.
Detection rate on null must be <= 20% (roughly the t-test's nominal false-alarm rate
under drift) for the experiment to be considered sensitive.
