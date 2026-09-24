"""B4.7 - calibration on the documented arm only.

factors.jsonl        item_id, factor_id, factor_text   (what the investigating
                     body named; factor_id unique within its item)
factor_matches.jsonl item_id, req_id, factor_id, matched  (external matching;
                     --match-source records who or what produced it)
Per documented item: recovered (factors with a matched requirement), missed,
and beyond_report (requirements matching no factor) - the third is printed
and left uninterpreted. An items file on the hypothetical arm yields `empty`.

Command: python3 calibrate.py items.jsonl requirements.jsonl factors.jsonl
         factor_matches.jsonl calibration.jsonl --match-source "<who or what>"
"""
import argparse
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import items as items_mod  # noqa: E402
import requirements as req_mod  # noqa: E402


def load_factors(path):
    out, seen = defaultdict(list), set()
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        rr.no_forbidden_fields(row, where)
        for f in ("item_id", "factor_id", "factor_text"):
            rr.field(row, f, where, str)
        key = (row["item_id"], row["factor_id"])
        if key in seen:
            raise rr.Reject("%s: field 'factor_id' duplicates an earlier row" % where)
        seen.add(key)
        out[row["item_id"]].append(row)
    return out


def load_factor_matches(path):
    out = []
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        rr.no_forbidden_fields(row, where)
        for f in ("item_id", "req_id", "factor_id"):
            rr.field(row, f, where, str)
        rr.field(row, "matched", where, bool, allow_bool=True)
        out.append(row)
    return out


def calibrate(items, rows, factors, fmatches, match_source):
    documented = [i for i in items if i["arm"] == "documented"]
    header = {"match_source": match_source, "items_documented": len(documented),
              "items_skipped": len(items) - len(documented)}
    reqs_of = defaultdict(set)
    for r in rows:
        reqs_of[r["item_id"]].add(r["req_id"])
    out = [header]
    for item in documented:
        iid = item["item_id"]
        fids = {f["factor_id"] for f in factors.get(iid, [])}
        rids = reqs_of.get(iid, set())
        hit_f, hit_r = set(), set()
        for m in fmatches:
            if m["matched"] and m["item_id"] == iid and m["factor_id"] in fids and m["req_id"] in rids:
                hit_f.add(m["factor_id"])
                hit_r.add(m["req_id"])
        out.append({"item_id": iid, "n_factors": len(fids), "n_requirements": len(rids),
                    "recovered": len(hit_f), "missed": len(fids - hit_f),
                    "beyond_report": len(rids - hit_r),
                    "recovered_ids": sorted(hit_f), "missed_ids": sorted(fids - hit_f),
                    "beyond_report_ids": sorted(rids - hit_r)})
    return out


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="calibrate against investigation factors")
    for n in ("items", "requirements", "factors", "factor_matches", "output"):
        p.add_argument(n)
    p.add_argument("--match-source", required=True)
    a = p.parse_args(argv)

    def run():
        items = items_mod.load_items(a.items)
        out = calibrate(items, req_mod.load_requirements(a.requirements),
                        load_factors(a.factors), load_factor_matches(a.factor_matches),
                        a.match_source)
        rr.write_jsonl(a.output, out)
        body = out[1:]
        counts = {"items_documented": len(body),
                  "recovered": sum(r["recovered"] for r in body),
                  "missed": sum(r["missed"] for r in body),
                  "beyond_report": sum(r["beyond_report"] for r in body)}
        notes = "" if body else "no documented items; calibration runs on that arm only"
        return ("ok" if body else "empty"), counts, notes

    return rr.execute("b4/calibrate.py", vars(a),
                      [a.items, a.requirements, a.factors, a.factor_matches], a.output,
                      None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
