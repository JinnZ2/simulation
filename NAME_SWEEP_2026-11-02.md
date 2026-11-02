# Name sweep 2026-11-02

One personal name (written `<name>` below) was removed from file contents. Git history was not rewritten,
so past commit messages and past file versions still carry it. Commit messages from now
on carry no name.

## Rule applied

```text
"Co-authored (<name> + Claude)" and similar headers  -> "Co-authored" (the date is kept)
"[stated] (<name>)"                                   -> "[stated]"
"OBSERVED by <name>", "OBSERVED (<name>)"              -> "OBSERVED (field report)"
any other attribution                                -> name dropped, status tag kept
"<name>'s method/frame/tool"                          -> "the method / a working tool"
```

Only the name changed on each line. Vendored and upstream third-party files were not touched.

## Files changed (replacements)

```text
sims/ising_critical_slowing/FINDINGS.md                        1
sims/ising_critical_slowing/NULL.md                            1
sims/ising_critical_slowing/REFUTE.md                          1
sims/ising_critical_slowing/run.py                             1
sims/lattice_anisotropy/FINDINGS.md                            1
sims/lattice_anisotropy/NULL.md                                1
sims/lattice_anisotropy/REFUTE.md                              1
sims/lattice_anisotropy/run.py                                 1
sims/render_ledger/FINDINGS.md                                 1
sims/render_ledger/NULL.md                                     1
sims/render_ledger/REFUTE.md                                   1
sims/render_ledger/run.py                                      1
sims/simulation_register/CONVERGENCE_RANKING.md                1
sims/simulation_register/README.md                             1
sims/simulation_register/SIMULATION_REGISTER.md                2
sims/simulation_register/auger_loader_stub.py                  1
sims/simulation_register/landauer_budget.py                    1
sims/simulation_register/phase_change_entropy.py               1
```

18 files, 19 replacements.

## Left in place, for the owner's call

These are identity or rights records, not attributions. Removing the name from them would
change what the line records, so they are listed here instead of edited:

```text
sims/ising_critical_slowing/config.json    "co_authored" field of a pre-registered config
sims/lattice_anisotropy/config.json        same
sims/render_ledger/config.json             same
```
Each of these configs has a `config_hash` recorded in `sims/ledger.jsonl` at run time.
Editing the field would make the recorded hash stop matching the file. `ledger_hook.py --check` hashes
metrics, not configs, so no test would catch it. A config is also a pre-registration file.
Changing it is a new pre-registration, not a cleanup.

## Where removing the name changed meaning

```text
sims/simulation_register/SIMULATION_REGISTER.md   "## Filter (<name>)" -> "## Filter": whose filter is no longer stated
```

## Test results

The suites were run before and after the sweep, and the counts below match. See the
commit message for the exact commands.
