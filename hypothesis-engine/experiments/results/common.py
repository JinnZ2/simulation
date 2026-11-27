"""Shared helpers for results/<EXP-ID>/run.py: environment record and JSON output.

Run every script from its own folder or from anywhere; paths are resolved from this file.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

RESULTS = Path(__file__).resolve().parent
EXPERIMENTS = RESULTS.parent
ENGINE = EXPERIMENTS.parent


def env() -> dict:
    def sh(*a):
        try:
            return subprocess.run(a, capture_output=True, text=True, cwd=ENGINE).stdout.strip()
        except OSError:
            return ""
    d = {"python": sys.version.split()[0], "platform": platform.platform(),
         "machine": platform.machine(), "cpu_count": os.cpu_count(),
         "commit": sh("git", "rev-parse", "HEAD"),
         "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with open("/proc/cpuinfo") as f:
            d["cpu"] = next((l.split(":", 1)[1].strip() for l in f if l.startswith("model name")), "")
    except OSError:
        d["cpu"] = platform.processor()
    for mod in ("numpy", "scipy", "tigramite"):
        try:
            d[mod] = __import__(mod).__version__
        except Exception:
            pass
    return d


def save(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=False, default=float) + "\n", encoding="utf-8")
