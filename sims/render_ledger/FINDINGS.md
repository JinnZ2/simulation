# Findings — render_ledger

Co-authored (Kavik + Claude, 2026-11-01). CC0. SYNTHETIC world; nothing observational.

**SUPPORTED at 5/5 seeds.** As REFUTE.md stated before the run, parts 1 and 3 hold largely by
construction of the policies: this is an accounting check of A1 and A6, not a discovery.

```text
observer          p      keep-record      recompute        delete
humans_only       0.01   saves 43%        saves 43%        saves 99%, contradicts 99.9% of re-observations
                         coverage 86.5% after 200 steps
humans_only       0.10   saves 4.5%       saves 4.5%       saves 90%, contradicts 99.9%
                         coverage 100%
any_interaction   any    saves 0%         saves 0%         saves 0%, no gaps -> no contradictions
```

## Reading

- At 10% observation the record covers every cell within 200 steps (1 - 0.9^200), so keeping a
  consistent record saves under 5%. The saving lives only in cells nobody ever looks at.
- If any physical interaction counts as observation (A1), the render-on-observation shortcut
  saves nothing under any policy.
- Only true deletion saves real compute, and it is the only policy that leaves a signature:
  repeat observations after a gap disagree with history. That is G6: the one branch with a
  testable prediction, and it has no real-data test.

## Caveats not eliminated

- The contradiction rate (0.999) is set by the state space (1000 states): a fresh random state
  matches history 1/1000 of the time. A real simulator could fake consistency with a smaller
  state space, or with a generator seeded from position and time -- which is the recompute
  policy and costs compute.
- Observation is uniform at random. Clustered observation (people look at the same places)
  would raise savings for keep-record.
