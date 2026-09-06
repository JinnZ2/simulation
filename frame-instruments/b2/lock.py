"""B2.3 - condition D commit lock, enforced as a process boundary.

  commit  reader_id case_id response.txt commits.jsonl
          appends {reader_id, case_id, response, sha256, utc}; never reads a key
  release reader_id case_id cases.jsonl commits.jsonl output.jsonl
          writes the key row for (reader, case) only if a commit with a valid
          sha256 exists; otherwise the run is void and nothing is written
No invocation holds both a commit and an unlocked key.
"""
import argparse
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import conditions  # noqa: E402


def load_commits(path):
    if not os.path.exists(path):
        return []
    out = []
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        for f in ("reader_id", "case_id", "response", "sha256"):
            rr.field(row, f, where, str)
        out.append(row)
    return out


def commit(reader_id, case_id, response, commits_path):
    row = {"reader_id": reader_id, "case_id": case_id, "response": response,
           "sha256": rr.sha256_text(response),
           "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    os.makedirs(os.path.dirname(os.path.abspath(commits_path)), exist_ok=True)
    with open(commits_path, "a", encoding="utf-8") as f:
        f.write(__import__("json").dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return row


def find_commit(commits, reader_id, case_id):
    for row in commits:
        if row["reader_id"] == reader_id and row["case_id"] == case_id:
            if rr.sha256_text(row["response"]) != row["sha256"]:
                raise rr.Reject("commit for %s/%s has a sha256 that does not match its "
                                "response" % (reader_id, case_id))
            return row
    return None


def release(reader_id, case_id, cases, commits):
    c = find_commit(commits, reader_id, case_id)
    if c is None:
        raise rr.Void("no commit for reader %s case %s; key not released" % (reader_id, case_id))
    case = next((x for x in cases if x["case_id"] == case_id), None)
    if case is None:
        raise rr.Reject("case %s not in cases file" % case_id)
    return {"case_id": case_id, "condition": "D", "presented_text": conditions.key_text(case),
            "reader_id": reader_id, "commit_sha256": c["sha256"]}


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="condition D commit lock")
    sub = p.add_subparsers(dest="verb", required=True)
    c = sub.add_parser("commit")
    for n in ("reader_id", "case_id", "response_file", "commits"):
        c.add_argument(n)
    r = sub.add_parser("release")
    for n in ("reader_id", "case_id", "cases", "commits", "output"):
        r.add_argument(n)
    a = p.parse_args(argv)

    if a.verb == "commit":
        def run():
            with open(a.response_file, encoding="utf-8") as f:
                response = f.read()
            if not response.strip():
                raise rr.Reject("response file is empty")
            commit(a.reader_id, a.case_id, response, a.commits)
            return "ok", {"committed": 1}, ""
        return rr.execute("b2/lock.py commit", vars(a), [a.response_file], a.commits,
                          None, run, runs_path)

    def run():
        row = release(a.reader_id, a.case_id, conditions.load_cases(a.cases),
                      load_commits(a.commits))
        rr.write_jsonl(a.output, [row])
        return "ok", {"released": 1}, ""
    return rr.execute("b2/lock.py release", vars(a), [a.cases, a.commits], a.output,
                      None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
