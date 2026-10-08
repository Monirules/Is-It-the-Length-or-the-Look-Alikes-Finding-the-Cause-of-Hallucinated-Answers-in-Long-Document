"""riker/find_lookalikes.py

For every RIKER2 trap question (L11, L12) at 32K, 128K and 200K, searches its document for records that
look like the asked item, and marks the question "look alike present" or "no look alike".

How a question is read
  Each trap question names a record by its KEY: lease = (tenant, landlord, start date);
  field report = (agent, prospect, date); HR evaluation = (employee, period). The names and dates are
  read from the question text with fixed patterns.
  L11: one name in the key does not exist (e.g. a made-up agent). L12: the record exists, but the asked
  optional field (pet deposit, manager comments, ...) is absent.

How a record is compared with the asked key (each part of the key separately)
  exact          same name / same date
  near_spelling  a name 1-2 letters different ("names one letter apart")
  shared_name    a different person who shares the first or the last name
  other_party    a different person
  other_date     same names, different date or period ("the same name with a different year")

Look-alike record = a record (not the asked record itself) that matches the asked key in every part
but ONE. For L12 it must also HAVE the asked field (that is where a made-up value would come from).
For a two-part key (HR: employee, period) the differing part must be close (near_spelling, shared_name
or other_date): another person's evaluation in the same period is only "weak".
A name 1-2 letters from an asked name anywhere in the document text also counts (text_near_spelling).

  look alike present   at least one look-alike record           (strength "strong")
  no look alike        none; "weak" marks questions where some record matches only one part of the key

The search uses the ground truth database to list records and their fields, and CHECKS IN THE TEXT
that each look-alike record is really in the document the models read (and where: lookalike_pos).

Output (project folder, small)
  outputs/riker/lookalikes.csv            one row per trap question and length
  outputs/riker/lookalikes_summary.md     counts, and whether look-alikes grow with length

Usage (Ubuntu/WSL, nullscale env, project folder; after download_riker.py; about 1 minute)
  python -m riker.find_lookalikes
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from riker.common import CONTEXTS, OUT_DIR, TRAP_LEVELS, corpus_files, load_db, load_tests, riker_root, split_corpus  # noqa: E402

# ----------------------------------------------------------------------------- reading questions

_STOP = r"(?:Does|Did|Do|Is|Was|Were|Has|Have|What|Who|When|Which|How|Where|In|For|The|According|Reply|Manager|Comments)"
NAME = rf"(?!{_STOP}\b)[A-Z][a-zA-Z\-]+(?: (?!{_STOP}\b)[A-Z][a-zA-Z\-]+){{1,3}}"
DATE = r"\d{4}-\d{2}-\d{2}"
PERIOD = r"(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}"

PATTERNS = {
    "lease_document": [rf"(?P<lessee>{NAME})'s? lease with (?P<lessor>{NAME}) starting (?P<date>{DATE})"],
    "field_report": [rf"(?P<agent>{NAME})'s? field report about (?P<lessee>{NAME}) on (?P<date>{DATE})",
                     rf"did (?P<agent>{NAME}) file about (?P<lessee>{NAME}) on (?P<date>{DATE})"],
    "hr": [rf"(?P<employee>{NAME})'s? evaluation for (?P<period>{PERIOD})",
           rf"(?:does|did) (?P<employee>{NAME}) (?:work in|hold|have)\b.*?(?:their|the) (?P<period>{PERIOD}) evaluation",
           rf"(?P<employee>{NAME})'s? (?P<period>{PERIOD}) evaluation"],
}
# key slots of each record type: question slot -> database column
SLOTS = {
    "lease_document": ("lease_documents", {"lessee": "lessee", "lessor": "lessor", "date": "start_date"}),
    "field_report": ("field_reports", {"agent": "agent", "lessee": "lessee", "date": "report_date"}),
    "hr": ("hr_reports", {"employee": "employee_name", "period": "evaluation_period"}),
}
DATE_SLOTS = {"date", "period"}

# (pattern in the question, value column, presence flag column). First match wins.
FIELDS = {
    "lease_document": [
        (r"pet deposit", "pet_deposit", "has_pet_clause"), (r"pets? (?:are )?allowed|what pets", "pet_details", "has_pet_clause"),
        (r"\bpet", None, "has_pet_clause"), (r"parking spaces", "parking_spaces", "has_parking_clause"),
        (r"parking fee", "parking_fee", "has_parking_clause"), (r"parking", None, "has_parking_clause"),
        (r"what utilities|utilities (?:are )?included in", "utilities_included", "has_utilities_clause"),
        (r"utilit", None, "has_utilities_clause"), (r"subleas|sublet", None, "has_sublease_clause"),
        (r"early termination fee", "early_termination_fee", "has_early_termination_clause"),
        (r"notice period", "early_termination_notice", "has_early_termination_clause"),
        (r"early termination", None, "has_early_termination_clause"), (r"agent", "agent", "has_agent"),
        (r"guarantor", "guarantor", "has_guarantor"), (r"security deposit|deposit", "security_deposit", None),
        (r"\brent\b", "monthly_rent", None), (r"\bend\b", "end_date", None), (r"duration|how long", "duration", None),
        (r"property|address|located", "property_address", None)],
    "field_report": [
        (r"manager (?:that|who) commented|which manager", "manager_name", "has_manager_notes"),
        (r"manager'?s comments|MANAGER'S COMMENTS|manager comments|manager notes", "manager_comments", "has_manager_notes"),
        (r"follow-up reason|reason for (?:the )?follow", "follow_up_reason", "has_follow_up"),
        (r"follow-up date|when .*follow", "follow_up_date", "has_follow_up"), (r"follow", None, "has_follow_up"),
        (r"what competitor|competitor property is", "competitor_property", "has_competitor"),
        (r"competitor", None, "has_competitor"),
        (r"what are the property condition|condition notes in", "condition_notes", "has_property_condition"),
        (r"condition", None, "has_property_condition"), (r"objection|concern", "objection_details", "has_objections"),
        (r"referral", "referral_source", "has_referral"), (r"closed deal", "report_type", None),
        (r"type of field report|report type", "report_type", None), (r"\brent\b", "monthly_rent", None),
        (r"deposit", "security_deposit", None), (r"property", "property_address", None)],
    "hr": [
        (r"manager comments", "manager_comments", "has_manager_comments"), (r"conducted|review date", "review_date", None),
        (r"rating", "performance_rating", None), (r"department", "department", None),
        (r"position|role|title", "employee_role", None), (r"review(?:ed|er)", "reviewer_name", None),
        (r"summary", "performance_summary", None)],
}
YES_NO = re.compile(r"^(?:Does|Do|Did|Is|Was|Were|Has|Have)\b")


def parse_question(doc_type: str, text: str) -> dict | None:
    for pat in PATTERNS.get(doc_type, []):
        m = re.search(pat, text)
        if m:
            return {k: v.strip() for k, v in m.groupdict().items()}
    return None


def asked_field(doc_type: str, text: str) -> tuple[str | None, str | None]:
    for pat, col, flag in FIELDS.get(doc_type, []):
        if re.search(pat, text, re.I):
            return col, flag
    return None, None


# ----------------------------------------------------------------------------- comparing

def edit_distance(a: str, b: str, cap: int = 3) -> int:
    """Levenshtein distance, stops early above cap."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        best = cur[0]
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            best = min(best, cur[j])
        if best > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def name_state(asked: str, rec: str | None) -> str:
    if not rec:
        return "other_party"
    a, r = asked.lower().strip(), rec.lower().strip()
    if a == r:
        return "exact"
    if edit_distance(a, r, 2) <= 2:
        return "near_spelling"
    at, rt = a.split(), r.split()
    if at and rt and (at[0] == rt[0] or at[-1] == rt[-1]):
        return "shared_name"
    return "other_party"


def compare(q: dict, rec: dict, slotmap: dict) -> dict:
    states = {}
    for slot, col in slotmap.items():
        if slot in DATE_SLOTS:
            states[slot] = "exact" if str(rec.get(col) or "").strip() == q[slot] else "other_date"
        else:
            states[slot] = name_state(q[slot], rec.get(col))
    return states


def has_field(rec: dict, col: str | None, flag: str | None) -> bool:
    if flag and not rec.get(flag):
        return False
    if col:
        v = rec.get(col)
        return v is not None and str(v).strip() != ""
    return bool(flag)


def field_value(rec: dict, col: str | None, flag: str | None, yes_no: bool, question: str) -> str | None:
    if yes_no:
        if col == "report_type" and "closed deal" in question.lower():
            return "Yes" if rec.get("report_type") == "closed_deal" else "No"
        if flag:
            return "Yes" if rec.get(flag) else "No"
        return None
    v = rec.get(col) if col else None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return None if v is None else str(v)


_TEXT_NAME = re.compile(r"\b[A-Z][a-z]+(?:-[A-Z][a-z]+)? [A-Z][a-z]+(?:-[A-Z][a-z]+)?\b")


def find_for_question(t: dict, db: dict, docs: dict, md_len: int, text_names: set[str]) -> dict:
    dtype, level, qtext = t["doc_type"], t["level"], t["question"]
    row = {"question_id": t["question_id"], "doc_type": dtype, "level": level, "template": t.get("template_no"),
           "question": qtext, "expected": t.get("expected_response")}
    q = parse_question(dtype, qtext)
    if q is None or dtype not in SLOTS:
        row.update(parse_ok=False, lookalike_present=None, lookalike_strength="unparsed")
        return row
    table, slotmap = SLOTS[dtype]
    col, flag = asked_field(dtype, qtext)
    yes_no = bool(YES_NO.match(qtext))
    names = {s: v for s, v in q.items() if s not in DATE_SLOTS}
    in_text = {s: (v in text_names) for s, v in names.items()}
    row.update(parse_ok=True, parties=json.dumps(q), field=col or flag, yes_no=yes_no,
               missing_party=";".join(s for s, ok in in_text.items() if not ok))
    asked, look, partial = [], [], []
    for rec in db.get(table, []):
        st = compare(q, rec, slotmap)
        diff = [s for s, v in st.items() if v != "exact"]
        if not diff:
            asked.append(rec)
            continue
        if level == "L12" and not has_field(rec, col, flag):
            continue
        if len(diff) == 1 and (len(st) >= 3 or st[diff[0]] != "other_party"):
            look.append((rec, st[diff[0]], diff[0]))
        elif len(st) - len(diff) >= 1:
            # weak: shares part of the key only (for a 2-part key such as an HR evaluation, a different
            # person in the same period is weak, not a look-alike)
            partial.append(rec)
    # names 1-2 letters from an asked name anywhere in the text
    near_text = sorted({n for v in names.values() for n in text_names
                        if n != v and abs(len(n) - len(v)) <= 2 and edit_distance(n.lower(), v.lower(), 2) <= 2})
    kinds = Counter(k for _, k, _ in look)
    if near_text and not kinds.get("near_spelling"):
        kinds["text_near_spelling"] = len(near_text)
    present = bool(look) or bool(near_text)
    order = {"near_spelling": 0, "other_date": 1, "shared_name": 2, "other_party": 3}
    look.sort(key=lambda x: order.get(x[1], 9))
    best = look[0][0] if look else None
    pos = None
    if best is not None and best["doc_id"] in docs:
        d = docs[best["doc_id"]]
        pos = round((d["start"] + d["end"]) / 2 / md_len, 4)
    row.update(
        lookalike_present=present,
        lookalike_strength="strong" if present else ("weak" if partial else "none"),
        lookalike_kinds=";".join(f"{k}:{v}" for k, v in kinds.items()),
        best_kind=look[0][1] if look else ("text_near_spelling" if near_text else ""),
        differing_slot=look[0][2] if look else "",
        n_lookalikes=len(look), n_partial=len(partial),
        lookalike_doc_ids=";".join(r["doc_id"] for r, _, _ in look[:20]),
        lookalike_in_text=all(r["doc_id"] in docs for r, _, _ in look),
        lookalike_value=field_value(best, col, flag, yes_no, qtext) if best is not None else None,
        lookalike_values=json.dumps(sorted({v for v in (field_value(r, col, flag, yes_no, qtext) for r, _, _ in look) if v})),
        lookalike_pos=pos,
        text_near_names=";".join(near_text[:10]),
        asked_record=";".join(r["doc_id"] for r in asked),
        asked_record_has_field=any(has_field(r, col, flag) for r in asked) if asked else None,
    )
    return row


# ----------------------------------------------------------------------------- main

def run(root: Path) -> list[dict]:
    rows = []
    for k in CONTEXTS:
        files = corpus_files(root, k)
        if not all(files.values()):
            print(f"{k}K: files missing ({files}); skipped")
            continue
        md = files["md"].read_text(encoding="utf-8")
        docs = split_corpus(md)
        db = load_db(files["db"])
        tests = [t for t in load_tests(files["yaml"]) if t["level"] in TRAP_LEVELS]
        text_names = set(_TEXT_NAME.findall(md))
        for t in tests:
            r = find_for_question(t, db, docs, len(md), text_names)
            r["context_k"] = k
            rows.append(r)
        got = [r for r in rows if r["context_k"] == k]
        print(f"{k}K: {len(got)} trap questions, look-alike present in "
              f"{sum(bool(r.get('lookalike_present')) for r in got)}, unparsed {sum(not r['parse_ok'] for r in got)}")
    return rows


def write_summary(rows: list[dict], out: Path) -> None:
    ok = [r for r in rows if r["parse_ok"]]
    L = ["# Look-alike records in RIKER2's trap questions", "",
         "Made by riker/find_lookalikes.py. A look-alike record matches the asked record's key (names, date) in every part "
         "but one; for L12 it must also have the asked field. See the script's docstring for the rules.", "",
         f"{len(rows)} trap questions; {len(rows) - len(ok)} could not be read (unparsed).", "",
         "## Look alike present, by length and level", "",
         "| length | level | questions | look alike present | no look alike | of which weak (one part of the key matches) | mean look-alike records per question |",
         "|---|---|---|---|---|---|---|"]
    for k in CONTEXTS:
        for lv in TRAP_LEVELS + ("all",):
            s = [r for r in ok if r["context_k"] == k and (lv == "all" or r["level"] == lv)]
            if not s:
                continue
            pres = sum(r["lookalike_present"] for r in s)
            L.append(f"| {k}K | {lv} | {len(s)} | {pres} ({100 * pres / len(s):.0f}%) | {len(s) - pres} | "
                     f"{sum(r['lookalike_strength'] == 'weak' for r in s)} | {sum(r['n_lookalikes'] for r in s) / len(s):.2f} |")
    L += ["", "## By document type (all lengths)", "",
          "| document type | level | questions | present | kinds of the closest look-alike |", "|---|---|---|---|---|"]
    by = defaultdict(list)
    for r in ok:
        by[(r["doc_type"], r["level"])].append(r)
    for (dtp, lv), s in sorted(by.items()):
        kinds = Counter(r["best_kind"] or "none" for r in s)
        L.append(f"| {dtp} | {lv} | {len(s)} | {sum(r['lookalike_present'] for r in s)} | "
                 + ", ".join(f"{k} {v}" for k, v in kinds.most_common()) + " |")
    pos = [r["lookalike_pos"] for r in ok if r.get("lookalike_pos") is not None]
    L += ["", f"Look-alike records found in the document text: "
          f"{sum(bool(r.get('lookalike_in_text')) for r in ok if r['lookalike_present'])} of "
          f"{sum(bool(r['lookalike_present']) for r in ok)} questions with a look-alike.",
          f"Position of the closest look-alike in the document (0 = start, 1 = end): "
          + (f"median {sorted(pos)[len(pos) // 2]:.2f}, range {min(pos):.2f}-{max(pos):.2f}" if pos else "n/a"),
          f"L11 questions where every asked name is in the text (no made-up name found): "
          f"{sum(1 for r in ok if r['level'] == 'L11' and not r['missing_party'])}", "",
          "## Examples", ""]
    for kind in ("near_spelling", "other_date", "shared_name", "other_party", "text_near_spelling", ""):
        ex = [r for r in ok if r["best_kind"] == kind][:2]
        for r in ex:
            L.append(f"- {r['context_k']}K `{r['question_id']}` ({kind or 'no look-alike'}): {r['question']}  "
                     f"-> look-alike {r['lookalike_doc_ids'].split(';')[0] if r['lookalike_doc_ids'] else '-'}"
                     f", value `{r.get('lookalike_value')}`")
    (out / "lookalikes_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main(argv=None) -> list[dict]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="RIKER2 folder (default: paths.yaml data.riker2)")
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else riker_root()
    rows = run(root)
    if not rows:
        sys.exit("no trap questions found. Run riker/download_riker.py first.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    keys = ["context_k", "question_id", "doc_type", "level", "template", "question", "expected", "parse_ok", "field",
            "yes_no", "parties", "missing_party", "lookalike_present", "lookalike_strength", "best_kind",
            "differing_slot", "lookalike_kinds", "n_lookalikes", "n_partial", "lookalike_doc_ids", "lookalike_in_text",
            "lookalike_value", "lookalike_values", "lookalike_pos", "text_near_names", "asked_record",
            "asked_record_has_field"]
    with open(OUT_DIR / "lookalikes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    write_summary(rows, OUT_DIR)
    print(f"\nsaved {OUT_DIR / 'lookalikes.csv'} and lookalikes_summary.md\nNext:  python -m riker.reanalyze_riker")
    return rows


if __name__ == "__main__":
    main()
