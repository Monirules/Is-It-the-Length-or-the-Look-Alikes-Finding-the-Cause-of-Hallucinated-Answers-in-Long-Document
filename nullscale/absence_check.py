"""nullscale/absence_check.py

Proves, for every question with no answer, that the answer is not anywhere in the document;
and, for every question with an answer, that exactly one record answers it.

The proof works on two levels:
  ground truth  the records the text was rendered from (saved in the document's .json)
  text          the actual characters the model will read (the .txt), searched directly

Checks per document
  S1  the record spans tile the text exactly (nothing in the text outside a known record)
  S2  the look-alike count matches the design (8 probes x copies, or 0 for level "none")

  Name ladder, per unanswerable question (asked company "Stem Generic"):
    N1  ground truth: no lease has the asked company as tenant
    N2  text: the asked company name does not occur (case and spacing ignored)
    N3  text: every word within 2 edits of the asked stem sits inside this probe's own look-alike
        record, and only at levels that should have one (medium: the stem itself; strong: one edit)
    N4  text: every "<Name> <Generic>" company name with the asked generic word sits inside this
        probe's own look-alike record, and only at weak or strong level
  Role ladder, per unanswerable question (company X, building Y, start year T):
    R1  ground truth: no lease has tenant X, building Y and a start date in year T
    R2  text: X occurs only in X's profile and in this probe's medium/strong look-alikes
    R3  text: Y occurs only in Y's profile and in this probe's weak/strong look-alikes
  Every answerable question:
    A1  ground truth: exactly one lease matches the question's key, and it is the witness
    A2  text: the gold answer string occurs inside the witness record

check_document() returns a list of problems; an empty list means the document passes.
build_dataset.py rebuilds any document that fails with a new seed.

Run on saved documents:   python -m nullscale.absence_check <folder-or-.json files>
"""
from __future__ import annotations

import bisect
import json
import re
import sys
from pathlib import Path

from nullscale.records import edit_distance

SEP = "\n\n"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


class _Spans:
    def __init__(self, records):
        self.records = records
        self.starts = [r["char_start"] for r in records]

    def at(self, pos: int) -> dict | None:
        i = bisect.bisect_right(self.starts, pos) - 1
        if i >= 0 and pos < self.records[i]["char_end"]:
            return self.records[i]
        return None


def _is_own_lookalike(rec: dict | None, pid: str) -> bool:
    return bool(rec) and rec["role"] == "lookalike" and rec["tags"].get("probe_id") == pid


def _leases(records):
    return [r for r in records if r["type"] == "lease"]


def check_document(doc: dict) -> list[str]:
    text, records = doc["text"], doc["records"]
    spec = doc["spec"]
    level, copies = spec["level"], spec["copies"]
    spans = _Spans(records)
    problems: list[str] = []

    # S1: tiling
    pos = 0
    for r in records:
        if r["char_start"] != pos:
            problems.append(f"S1 gap/overlap before record {r['rid']}")
            break
        pos = r["char_end"] + len(SEP)
    if pos - len(SEP) != len(text):
        problems.append("S1 records do not end where the text ends")
    if SEP.join(text[r["char_start"]:r["char_end"]] for r in records) != text:
        problems.append("S1 text is not exactly the records joined")

    # S2: look-alike count
    n_la = sum(r["role"] == "lookalike" for r in records)
    n_probes = sum(not q["answerable"] for q in doc["questions"])
    want = 0 if level == "none" else n_probes * copies
    if n_la != want:
        problems.append(f"S2 expected {want} look-alike records, found {n_la}")

    words = {}
    for m in re.finditer(r"[A-Za-z]{4,}", text):
        words.setdefault(m.group().lower(), []).append(m.start())
    norm_text = _norm(text)

    for q in doc["questions"]:
        t, pid = q["target"], q["probe_id"]
        tag = f"[{pid}]"
        if q["answerable"]:
            key = [r for r in _leases(records) if r["fields"]["tenant"] == t["tenant"] and
                   (spec["ladder"] == "name" or (r["fields"]["building"] == t["building"] and
                                                 r["fields"]["start_date"][:4] == str(t["start_year"])))]
            if len(key) != 1 or key[0]["rid"] != q["witness_rid"]:
                problems.append(f"A1 {tag} {len(key)} leases match the answerable key (want the witness only)")
            wit = next((r for r in records if r["rid"] == q["witness_rid"]), None)
            if wit is None or q["gold"] not in text[wit["char_start"]:wit["char_end"]]:
                problems.append(f"A2 {tag} gold answer {q['gold']!r} not found in the witness record")
            continue

        if spec["ladder"] == "name":
            tenant, stem, generic = t["tenant"], t["stem"].lower(), t["generic"]
            if any(r["fields"]["tenant"] == tenant for r in _leases(records)):
                problems.append(f"N1 {tag} a lease with the asked tenant exists")
            if _norm(tenant) in norm_text:
                problems.append(f"N2 {tag} the asked name '{tenant}' occurs in the text")
            for w, starts in words.items():
                d = edit_distance(w, stem)
                if d > 2:
                    continue
                allowed = (level == "medium" and d == 0) or (level == "strong" and d == 1)
                for st in starts:
                    if not (allowed and _is_own_lookalike(spans.at(st), pid)):
                        problems.append(f"N3 {tag} '{text[st:st + len(w)]}' ({d} edits from the asked stem) "
                                        f"outside this probe's look-alike")
                        break
            for m in re.finditer(r"\b[A-Z][a-z]+ " + re.escape(generic) + r"\b", text):
                rec = spans.at(m.start())
                if not (level in ("weak", "strong") and _is_own_lookalike(rec, pid)):
                    problems.append(f"N4 {tag} '{m.group()}' shares the asked generic word outside the look-alike")
                    break
        else:
            x, y, year = t["tenant"], t["building"], str(t["start_year"])
            for r in _leases(records):
                f = r["fields"]
                if f["tenant"] == x and f["building"] == y and f["start_date"][:4] == year:
                    problems.append(f"R1 {tag} the asked lease exists ({r['rid']})")
            for name, ok_levels, code in ((x, ("medium", "strong"), "R2"), (y, ("weak", "strong"), "R3")):
                for m in re.finditer(re.escape(name), text):
                    rec = spans.at(m.start())
                    own_entity = rec and rec["role"] == "entity" and rec["tags"].get("probe_id") == pid
                    own_la = level in ok_levels and _is_own_lookalike(rec, pid)
                    if not (own_entity or own_la):
                        problems.append(f"{code} {tag} '{name}' mentioned in {rec['role'] if rec else 'no record'} "
                                        f"{rec['rid'] if rec else ''}")
                        break
    return problems


def load_document(json_path: Path) -> dict:
    doc = json.loads(Path(json_path).read_text(encoding="utf-8"))
    doc["text"] = Path(json_path).with_suffix(".txt").read_text(encoding="utf-8")
    return doc


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    files = []
    for a in sys.argv[1:]:
        p = Path(a)
        files += sorted(p.rglob("*.json")) if p.is_dir() else [p]
    files = [f for f in files if f.with_suffix(".txt").exists()]
    n_bad = 0
    for f in files:
        probs = check_document(load_document(f))
        n_bad += bool(probs)
        print(f"{'PASS' if not probs else 'FAIL'}  {f.stem}")
        for p in probs[:5]:
            print(f"      {p}")
    print(f"\n{len(files) - n_bad}/{len(files)} documents pass")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
