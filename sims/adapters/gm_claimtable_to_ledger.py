#!/usr/bin/env python3
"""
gm_claimtable_to_ledger.py — Geometric-manifold- CLAIM_TABLE -> CDT falsification ledger adapter.

Reads a GM CLAIM_TABLE export (JSON list of claim dicts) and appends each claim
to a Cross-Domain-Toolkit falsification_ledger hash chain as a PREDICT entry
with its refutation condition attached. Stdlib only. ~60 LOC.

GM claim fields expected (tolerant): id/claim_id, statement, evidence, status
(e.g. ISS_proof_pending), refutation_condition, timestamp.
Ledger entry: {"type":"PREDICT","claim":...,"refute_if":...,"source":"Geometric-manifold-",
               "prev_hash":...,"hash":...}
"""
import json, hashlib, sys, time

def _h(s): return hashlib.sha256(s.encode()).hexdigest()

def load_chain(path):
    try:
        with open(path) as f: return [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        return []

def append_entry(chain_path, entry, prev_hash):
    entry["prev_hash"] = prev_hash
    entry["hash"] = _h(json.dumps(entry, sort_keys=True) + prev_hash)
    with open(chain_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry["hash"]

def claim_to_entry(c):
    cid = c.get("id") or c.get("claim_id") or "UNKNOWN"
    return {
        "type": "PREDICT",
        "claim_id": f"GM:{cid}",
        "claim": c.get("statement", ""),
        "evidence": c.get("evidence", None),
        "refute_if": c.get("refutation_condition",
                    "no explicit refutation condition exported - REJECT from ledger"),
        "status": c.get("status", "unknown"),
        "source": "Geometric-manifold-/CLAIM_TABLE",
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

def migrate(claim_table_path, ledger_path):
    with open(claim_table_path) as f:
        claims = json.load(f)
    chain = load_chain(ledger_path)
    prev = chain[-1]["hash"] if chain else "GENESIS"
    imported, rejected = 0, 0
    for c in claims:
        e = claim_to_entry(c)
        if "REJECT" in e["refute_if"]:
            rejected += 1
            continue                      # ledger ethos: no refutation condition, no entry
        prev = append_entry(ledger_path, e, prev)
        imported += 1
    print(f"imported {imported} claims -> {ledger_path}; rejected {rejected} (no refutation condition)")

if __name__ == "__main__":
    migrate(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "ledger.jsonl")
