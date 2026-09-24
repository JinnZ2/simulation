"""B4.2 - one prompt file per (item, reconstructor), holding text_verbatim only.

Built from items.jsonl alone. No other reconstructor's output, no example
requirement, no category list, no prior run. Every written file is re-read
and asserted to hold exactly the one field.

Command: python3 reconstruct.py items.jsonl outdir/ --reconstructors r1 r2 ...
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import items as items_mod  # noqa: E402

ONLY_FIELD = "text_verbatim"


def write_prompts(items, reconstructors, outdir):
    if len(set(reconstructors)) != len(reconstructors):
        raise rr.Reject("reconstructor ids repeat")
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for item in items:
        for rid in reconstructors:
            path = os.path.join(outdir, "%s__%s.json" % (item["item_id"], rid))
            with open(path, "w", encoding="utf-8") as f:
                json.dump({ONLY_FIELD: item[ONLY_FIELD]}, f, ensure_ascii=False)
            with open(path, encoding="utf-8") as f:
                back = json.load(f)
            if set(back) != {ONLY_FIELD} or back[ONLY_FIELD] != item[ONLY_FIELD]:
                raise rr.Reject("%s: written file does not hold exactly %r" % (path, ONLY_FIELD))
            paths.append(path)
    return paths


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="reconstructor prompt files")
    p.add_argument("items")
    p.add_argument("outdir")
    p.add_argument("--reconstructors", nargs="+", required=True)
    a = p.parse_args(argv)

    def run():
        items = items_mod.load_items(a.items)
        paths = write_prompts(items, a.reconstructors, a.outdir)
        counts = {"items": len(items), "reconstructors": len(a.reconstructors), "files": len(paths)}
        return ("ok" if paths else "empty"), counts, ""

    return rr.execute("b4/reconstruct.py", vars(a), [a.items], a.outdir, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
