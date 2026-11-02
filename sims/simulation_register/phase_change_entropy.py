#!/usr/bin/env python3
"""
phase_change_entropy.py -- G4 part (a): entropy jump per transition, in bits.

STATUS: DERIVED arithmetic; inputs from memory, every one VERIFY. Co-authored
(2026-11-01). CC0. stdlib. Not a harness sim. Part (b), the compute needed to REACH a transition
(critical slowing), is ../ising_critical_slowing/.

dS = dH / T_transition (first-order); bits per molecule = dS / (R ln 2); bits per mole x N_A.
"""
import math

R = 8.314462618        # J/(mol K)
N_A = 6.02214076e23    # 1/mol

ROWS = [
    # name, dH J/mol (per unit), T K, unit, source note
    ("ice melting", 6010.0, 273.15, "mol H2O", "dH_fus 6.01 kJ/mol (VERIFY, standard tables)"),
    ("water boiling", 40650.0, 373.15, "mol H2O", "dH_vap 40.65 kJ/mol at 1 atm (VERIFY)"),
    ("DNA unzipping", 92.0 * 330.0, 330.0, "mol base pair",
     "dS ~ 22 cal/(mol K) = 92 J/(mol K) per nearest-neighbour stack (SantaLucia 1998 range ~20-27 cal; VERIFY); "
     "entered as dH = dS x T"),
    ("lipid membrane melt", 36000.0, 314.2, "mol DPPC", "main transition ~36 kJ/mol at ~41 C (VERIFY)"),
    ("protein unfolding", 490000.0, 345.0, "mol protein", "lysozyme-scale dH ~480-500 kJ/mol at Tm ~72 C (VERIFY)"),
]


def main():
    print("ENTROPY JUMP PER TRANSITION -- inputs VERIFY; A5 (known phases only) applies\n")
    print("%-22s %-14s %10s %14s %16s" % ("transition", "per", "dS J/molK", "bits/unit", "bits/mole"))
    for name, dH, T, unit, src in ROWS:
        dS = dH / T
        b = dS / (R * math.log(2))
        print("%-22s %-14s %10.1f %14.2f %16.2e   %s" % (name, unit, dS, b, b * N_A, src))
    up = math.log(2) * R
    print("%-22s %-14s %10.2f %14.2f %16.2e   %s" % ("Curie (upper bound)", "mol spin-1/2", up, 1.0, N_A,
                                                    "R ln 2 per mole of spin-1/2 moments; real magnets release less "
                                                    "at T_c (short-range order); upper bound only"))
    print("\nNot tabulated (G4 gap): the compute needed to reach each transition (critical slowing),")
    print("which needs a critical-exponent table across domains. ../ising_critical_slowing/ is one entry.")


if __name__ == "__main__":
    main()
