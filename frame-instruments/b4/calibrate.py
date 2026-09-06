"""B4.7 -- calibration on the documented arm only.

    python3 calibrate.py requirements.jsonl items.jsonl factors.jsonl factor_matches.jsonl MATCH_SOURCE calibration.jsonl

items.jsonl must be the documented arm; any other arm exits void.
factors.jsonl carries the causal factors the investigating body named:
  item_id, factor_id, factor_text
factor_matches.jsonl is the external matcher's verdict, one row per
(factor, requirement) pair it considered:
  item_id, factor_id, req, matched          (req = "<reconstructor_id>/<req_id>")

Per (item, reconstructor) and per item pooled across reconstructors:
  recovered      factors with at least one matched requirement
  missed         factors with none
  beyond_report  requirements matched to no factor

beyond_report is NOT scored as error. A reconstruction may reach a node
the investigation did not, and investigations have scope limits. It is
printed and left uninterpreted. This calibrates the protocol on cases
with records and says nothing about the hypothetical arm.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from agree import stamp  # noqa: E402
from agreement import ref  # noqa: E402
from items import load_items  # noqa: E402
from requirements import load_requirements  # noqa: E402
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

FACTOR_FIELDS = ("item_id", "factor_id", "factor_text")
FM_FIELDS = ("item_id", "factor_id", "req", "matched")


def _rows(path, fields, checks) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    for n, r in enumerate(rows, 1):
        where = f"{name} line {n}"
        for f in fields:
            if f not in r:
                raise SchemaError(f"{where}: missing field '{f}'")
        for f in r:
            if f not in fields:
                raise SchemaError(f"{where}: unexpected field '{f}'")
        checks(r, where)
    return rows


def load_factors(path, item_ids) -> list[dict]:
    def check(r, where):
        for f in FACTOR_FIELDS:
            if not isinstance(r[f], str) or not r[f].strip():
                raise SchemaError(f"{where}: field '{f}' must be a non-empty string")
        if r["item_id"] not in item_ids:
            raise SchemaError(f"{where}: item_id {r['item_id']!r} not in items.jsonl")
    return _rows(path, FACTOR_FIELDS, check)


def load_factor_matches(path, factors, reqs) -> list[dict]:
    fk = {(f["item_id"], f["factor_id"]) for f in factors}
    rk = {(r["item_id"], ref(r)) for r in reqs}

    def check(r, where):
        if not isinstance(r["matched"], bool):
            raise SchemaError(f"{where}: field 'matched' must be true or false")
        if (r["item_id"], r["factor_id"]) not in fk:
            raise SchemaError(f"{where}: factor {r['factor_id']!r} not in factors for item {r['item_id']!r}")
        if (r["item_id"], r["req"]) not in rk:
            raise SchemaError(f"{where}: req {r['req']!r} not in requirements for item {r['item_id']!r}")
    return _rows(path, FM_FIELDS, check)


def calibrate(items, reqs, factors, fmatches) -> list[dict]:
    facts = defaultdict(list)
    for f in factors:
        facts[f["item_id"]].append(f["factor_id"])
    hit_f, hit_r = defaultdict(set), defaultdict(set)
    for m in fmatches:
        if m["matched"]:
            rid = m["req"].split("/")[0]
            hit_f[(m["item_id"], rid)].add(m["factor_id"])
            hit_r[m["item_id"]].add(m["req"])
    by_item = defaultdict(list)
    for r in reqs:
        by_item[r["item_id"]].append(r)
    out = []
    for item in sorted(it["item_id"] for it in items):
        named = set(facts[item])
        recs = sorted({r["reconstructor_id"] for r in by_item[item]})
        pooled_hit = set()
        for rid in recs:
            got = hit_f[(item, rid)] & named
            pooled_hit |= got
            mine = [r for r in by_item[item] if r["reconstructor_id"] == rid]
            beyond = sum(1 for r in mine if ref(r) not in hit_r[item])
            out.append({"kind": "reconstructor", "item_id": item, "reconstructor_id": rid,
                        "named_factors": len(named), "recovered": len(got), "missed": len(named - got),
                        "beyond_report": beyond, "n_requirements": len(mine)})
        beyond_all = sum(1 for r in by_item[item] if ref(r) not in hit_r[item])
        out.append({"kind": "item", "item_id": item, "n_reconstructors": len(recs),
                    "named_factors": len(named), "recovered": len(pooled_hit), "missed": len(named - pooled_hit),
                    "beyond_report": beyond_all, "n_requirements": len(by_item[item])})
    return out


def _body(args):
    reqs = load_requirements(args[0])
    items = load_items(args[1])
    if not items:
        return "empty", {}, "no items"
    if items[0]["arm"] != "documented":
        return "void", {"items": len(items)}, f"arm={items[0]['arm']}; calibration runs on the documented arm only"
    ids = {it["item_id"] for it in items}
    factors = load_factors(args[2], ids)
    fmatches = load_factor_matches(args[3], factors, reqs)
    rows = stamp(calibrate(items, [r for r in reqs if r["item_id"] in ids], factors, fmatches), args[4])
    write_jsonl(args[5], rows)
    item_rows = [r for r in rows if r["kind"] == "item"]
    counts = {"items": len(item_rows), "recovered": sum(r["recovered"] for r in item_rows),
              "missed": sum(r["missed"] for r in item_rows), "beyond_report": sum(r["beyond_report"] for r in item_rows)}
    return "ok", counts, f"match_source={args[4]}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ["<in:requirements.jsonl>", "<in:items.jsonl>", "<in:factors.jsonl>", "<in:factor_matches.jsonl>",
             "MATCH_SOURCE", "<out:calibration.jsonl>"]
    return main_guard("b4.calibrate", argv, names, None, _body)


if __name__ == "__main__":
    sys.exit(main())
