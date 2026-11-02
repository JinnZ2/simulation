#!/usr/bin/env python3
"""
auger_loader_stub.py -- loader stub for the Pierre Auger Observatory public data release.

STATUS: STUB, co-authored (2026-11-01). CC0. stdlib.

The lattice-anisotropy statistic (../lattice_anisotropy/) needs arrival directions of the
highest-energy cosmic rays plus the exposure map. Release name, event count and license must be
read from the release itself before any use.

2026-11-01: opendata.auger.org and www.auger.org were NOT reachable from the environment this was
written in (no response through its network proxy). Nothing was downloaded; event count and
license are UNVERIFIED. Per the work order: stop and report; do not substitute synthetic data and
call it real. This file therefore refuses to run without a local file.

Expected input once obtained (VERIFY the real column names against the release):
  CSV with columns  ra_deg, dec_deg, energy_EeV      (one event per row)
"""
import csv
import math
import sys


def load_events(path, min_energy_eev=None):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            e = float(row["energy_EeV"])
            if min_energy_eev is not None and e < min_energy_eev:
                continue
            ra, dec = math.radians(float(row["ra_deg"])), math.radians(float(row["dec_deg"]))
            out.append((math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)))
    return out


def main(argv):
    if len(argv) < 2:
        print("REFUSED: no local Auger release file given. The data was not reachable when this stub "
              "was written; no synthetic stand-in is provided. Usage: auger_loader_stub.py events.csv",
              file=sys.stderr)
        return 3
    ev = load_events(argv[1])
    print("loaded %d events (REAL data only if the file is the official release; record its version, "
          "event count and license)" % len(ev))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
