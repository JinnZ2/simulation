"""B4.2 -- one prompt file per (item, reconstructor), text_verbatim only.

    python3 reconstruct.py items.jsonl N_RECONSTRUCTORS OUTDIR

Writes OUTDIR/<item_id>__<reconstructor_id>.jsonl, each holding one row
with exactly one field, text_verbatim, copied byte for byte. No other
reconstructor's output, no requirement example, no category list, no
prior run. OUTDIR/manifest.jsonl (item_id, reconstructor_id, file) is for
the operator and is never shown to a reconstructor.

RULE: no example requirement is ever shown. An example is the category
re-entering at intake.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from items import load_items  # noqa: E402
from runrecord import SchemaError, main_guard, write_jsonl  # noqa: E402

PROMPT_FIELDS = ("text_verbatim",)


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def prompt_row(item: dict) -> dict:
    row = {"text_verbatim": item["text_verbatim"]}
    extra = [f for f in row if f not in PROMPT_FIELDS]
    if extra:
        raise SchemaError(f"prompt for {item['item_id']!r} would carry field '{extra[0]}'")
    return row


def emit(items: list[dict], n_reconstructors: int, outdir: Path) -> list[dict]:
    if n_reconstructors < 1:
        raise SchemaError("N_RECONSTRUCTORS must be >= 1")
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for item in items:
        for k in range(1, n_reconstructors + 1):
            rid = f"r{k:03d}"
            fname = f"{_safe(item['item_id'])}__{rid}.jsonl"
            write_jsonl(outdir / fname, [prompt_row(item)])
            manifest.append({"item_id": item["item_id"], "reconstructor_id": rid, "file": fname})
    write_jsonl(outdir / "manifest.jsonl", manifest)
    return manifest


def _body(args):
    items = load_items(args[0])
    manifest = emit(items, int(args[1]), Path(args[2]))
    n = len({m["reconstructor_id"] for m in manifest})
    return ("empty" if not manifest else "ok"), {"items": len(items), "reconstructors": n, "prompts": len(manifest)}, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("b4.reconstruct", argv, ["<in:items.jsonl>", "N_RECONSTRUCTORS", "<out:OUTDIR>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
