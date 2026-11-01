#!/usr/bin/env python3
"""
landauer_budget.py -- order-of-magnitude energy budget for simulating the observable universe.

STATUS: DERIVED arithmetic on cited inputs, co-authored (Kavik + Claude, 2026-11-01). CC0. stdlib.
Not a harness sim (no claim graded); a calculator for SIMULATION_REGISTER.md. Assumptions A2
(our physics) and A3 (irreversible compute) are REQUIRED for these numbers to mean anything.

Every input is printed with its source; VERIFY = not checked against the primary source here.
"""
import math

K_B = 1.380649e-23        # J/K, exact (SI 2019 definition)
C = 2.99792458e8          # m/s, exact

INPUTS = {
    "ops":        (1e120, "total elementary operations the universe could have performed "
                          "(Lloyd 2002, PRL 88, 237901, 'Computational capacity of the universe'; VERIFY)"),
    "bits":       (1e90,  "bits registered in matter, same source (VERIFY)"),
    "T_cmb":      (2.725, "K, cosmic microwave background temperature (VERIFY: 2.7255 K, Fixsen 2009)"),
    "mass_kg":    (1.5e53, "kg, ordinary (baryonic) matter in the observable universe, order of "
                           "magnitude (VERIFY; estimates vary by ~2x)"),
    "genome_bits": (1e10, "bits, order of a large genome (VERIFY; human ~6e9 bp x 2 bits)"),
    "T_body":     (310.0, "K, body temperature"),
}


def landauer(bits, T):
    return bits * K_B * T * math.log(2)


def main():
    v = {k: x[0] for k, x in INPUTS.items()}
    print("LANDAUER BUDGET -- order of magnitude; requires A2 and A3 (SIMULATION_REGISTER.md)\n")
    for k, (val, src) in INPUTS.items():
        print("  %-12s %-10.3g %s" % (k, val, src))
    e_ops = landauer(v["ops"], v["T_cmb"])
    e_mass = v["mass_kg"] * C ** 2
    print("\n  erasure cost of %.0e ops at %.3f K   = %.2e J   (one bit erased per op: upper reading)"
          % (v["ops"], v["T_cmb"], e_ops))
    print("  mass-energy of ordinary matter       = %.2e J" % e_mass)
    print("  ratio                                = 10^%.1f" % math.log10(e_ops / e_mass))
    print("\n  classical storage of the full quantum state of %.0e two-level systems needs" % v["bits"])
    print("  2^%.0e complex amplitudes: log10(log10(amplitudes)) = %.1f  -- a separate, far larger term"
          % (v["bits"], math.log10(v["bits"] * math.log10(2))))
    g = landauer(v["genome_bits"], v["T_body"])
    print("\n  deleting a %.0e-bit genome at %.0f K = %.1e J  (Landauer bound; rebuild cost = evolutionary time)"
          % (v["genome_bits"], v["T_body"], g))
    print("\n  If A3 fails (reversible compute), the first line has no lower bound above ~0.")


if __name__ == "__main__":
    main()
