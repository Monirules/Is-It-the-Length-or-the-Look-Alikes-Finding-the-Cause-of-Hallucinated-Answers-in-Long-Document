"""nullscale/questions.py

Question templates, and the 12 questions each document gets: 8 with no answer, 4 with an answer.

Template bank
  27 templates: 15 for the name ladder (5 lease facts x 3 wordings) and 12 for the role ladder
  (4 lease facts x 3 wordings). The SAME bank is used for questions with and without an answer,
  so the wording of a question never gives away whether it can be answered:
    UNANSWERABLE_TEMPLATES  27  (>= 24 required)
    ANSWERABLE_TEMPLATES    27  (>= 12 required)

Per document
  8 unanswerable probes  u0..u7   each asks about a lease that does not exist and gets its own
                                  look-alike record(s) at the document's ladder and level
  4 answerable questions a0..a3   each asks about a "witness" lease that exists exactly once
  Fact types (rent, deposit, ...) are spread evenly over the questions; answerable and unanswerable
  questions on the same ladder have the same shape (name: only a company; role: company,
  building and start year, with both profile records in the document).

Run  `python -m nullscale.questions`  to print the bank and one document's 12 questions.
"""
from __future__ import annotations

import random
from datetime import date

from nullscale import schema as S
from nullscale.lookalike import Case, make_case, possessive
from nullscale.records import Record, World
from nullscale.render import fmt_date, fmt_money

N_UNANSWERABLE = 8
N_ANSWERABLE = 4

TEMPLATES: dict[str, dict[str, list[str]]] = {
    "name": {
        "monthly_rent": [
            "What monthly rent does {tenant} pay under its lease?",
            "How much is {tenant} charged in rent each month?",
            "According to the records, what is the monthly rent on {tenant_pos} lease?",
        ],
        "deposit": [
            "How large was the security deposit on {tenant_pos} lease?",
            "What deposit did {tenant} pay for its lease?",
            "What security deposit is recorded for {tenant_pos} lease?",
        ],
        "start_date": [
            "On what date did {tenant_pos} lease begin?",
            "When did {tenant} start its lease?",
            "What is the start date of the lease held by {tenant}?",
        ],
        "end_date": [
            "On what date does {tenant_pos} lease end?",
            "When does the lease held by {tenant} expire?",
            "What is the end date of {tenant_pos} lease?",
        ],
        "floor": [
            "Which floor does {tenant} lease?",
            "On what floor is the space leased by {tenant}?",
            "What floor number appears on {tenant_pos} lease?",
        ],
    },
    "role": {
        "monthly_rent": [
            "What was the monthly rent of {tenant_pos} lease at {building} that started in {year}?",
            "How much rent per month did {tenant} pay at {building} under the lease that began in {year}?",
            "For the lease between {tenant} and {building} that started in {year}, what is the monthly rent?",
        ],
        "deposit": [
            "How large was the security deposit on {tenant_pos} lease at {building} that started in {year}?",
            "What deposit did {tenant} pay for its {year} lease at {building}?",
            "For the lease between {tenant} and {building} that started in {year}, what was the deposit?",
        ],
        "end_date": [
            "When does {tenant_pos} lease at {building} that started in {year} end?",
            "On what date does the {year} lease between {tenant} and {building} expire?",
            "What is the end date of the lease {tenant} signed at {building} starting in {year}?",
        ],
        "floor": [
            "Which floor did {tenant} lease at {building} under the lease that started in {year}?",
            "On what floor of {building} is the space {tenant} leased starting in {year}?",
            "For the lease between {tenant} and {building} that started in {year}, which floor is it on?",
        ],
    },
}

UNANSWERABLE_TEMPLATES = [(f"{lad[0].upper()}-{f}-{i}", t) for lad, fs in TEMPLATES.items()
                          for f, ts in fs.items() for i, t in enumerate(ts, 1)]
ANSWERABLE_TEMPLATES = list(UNANSWERABLE_TEMPLATES)     # same wording on purpose (see module doc)
FIELDS = {lad: list(fs) for lad, fs in TEMPLATES.items()}

assert len(UNANSWERABLE_TEMPLATES) >= 24 and len(ANSWERABLE_TEMPLATES) >= 12


# ----------------------------------------------------------------------------- helpers

def fmt_value(field: str, v) -> str:
    """The answer string exactly as it appears in the document text."""
    if v is None:
        return ""
    if isinstance(v, date):
        return fmt_date(v)
    if field in ("monthly_rent", "deposit"):
        return fmt_money(v)
    return str(v)


def value_aliases(field: str, v) -> list[str]:
    """Other ways a correct answer may be written (for scoring)."""
    if v is None:
        return []
    if isinstance(v, date):
        return [fmt_date(v), v.isoformat(), f"{v.month}/{v.day}/{v.year}", f"{v:%b} {v.day}, {v.year}"]
    if field in ("monthly_rent", "deposit"):
        return [fmt_money(v), f"{v:,}", str(v), f"${v}"]
    return [str(v)]


def plan_fields(ladder: str, n: int, rng: random.Random) -> list[str]:
    """n fact types spread as evenly as possible over the ladder's fields."""
    fields = FIELDS[ladder][:]
    rng.shuffle(fields)
    return [fields[i % len(fields)] for i in range(n)]


def phrase(ladder: str, field: str, slots: dict, rng: random.Random) -> tuple[str, str]:
    i = rng.randrange(len(TEMPLATES[ladder][field]))
    tid = f"{ladder[0].upper()}-{field}-{i + 1}"
    text = TEMPLATES[ladder][field][i].format(tenant_pos=possessive(slots["tenant"]), **slots)
    return tid, text


# ----------------------------------------------------------------------------- per document

def _witness(world: World, ladder: str, field: str, aid: str) -> tuple[list[Record], Record, dict]:
    """Records for one answerable question and its target. The witness lease is the only lease
    with that key in the document (fresh names, registered in the world)."""
    rng = world.rng
    extra: list[Record] = []
    if ladder == "name":
        lease = world.lease()
        target = {"probe_id": aid, "tenant": lease.get("tenant"), "field": field}
    else:
        x, y = world.company(), world.building()
        for r in (x, y):
            r.role, r.tags = "entity", {"probe_id": aid}
        year = rng.randint(2014, 2022)
        lease = world.lease(tenant=x.get("name"), building=y.get("name"), start_year=year)
        target = {"probe_id": aid, "tenant": x.get("name"), "building": y.get("name"),
                  "start_year": year, "field": field}
        extra = [x, y]
    if field == "deposit" and "deposit" not in lease.fields:
        lease.fields["deposit"] = world.money(lease.get("monthly_rent"), lease.get("monthly_rent") * 3)
    lease.role, lease.tags = "witness", {"probe_id": aid}
    return extra + [lease], lease, target


def plan_document(world: World, ladder: str, level: str, copies: int,
                  n_unanswerable: int = N_UNANSWERABLE, n_answerable: int = N_ANSWERABLE):
    """Create every question-relevant record for one document.

    Returns (cases, answer_records, questions):
      cases           the n_unanswerable lookalike.Case objects (their entities + look-alikes)
      answer_records  witness leases (+ profiles on the role ladder) for the answerable questions
      questions       12 question dicts in a fixed random order (doc-independent fields only)
    """
    rng = world.rng
    questions, answer_records = [], []
    cases: list[Case] = []
    # name ladder: choose every asked generic word first, so no look-alike of one probe can use
    # another probe's asked word
    generics = [None] * n_unanswerable
    if ladder == "name":
        generics = rng.sample([g for g in S.COMPANY_GENERICS if g not in world.reserved_generics], n_unanswerable)
        world.reserved_generics.update(generics)
    for i, field in enumerate(plan_fields(ladder, n_unanswerable, rng)):
        pid = f"u{i}"
        case = make_case(world, ladder, level, copies, field, probe_id=pid, generic=generics[i])
        slots = {"tenant": case.target["tenant"], "building": case.target.get("building", ""),
                 "year": case.target.get("start_year", "")}
        tid, text = phrase(ladder, field, slots, rng)
        case.question = text
        cases.append(case)
        questions.append({
            "probe_id": pid, "answerable": False, "field": field, "template_id": tid, "question": text,
            "gold": None, "gold_aliases": [], "target": case.target,
            "lookalike_rids": [] if case.level == "decoy" else [r.rid for r in case.lookalikes],
            "lookalike_values": [fmt_value(field, v) for v in case.lookalike_values()],
            "decoy_rids": [r.rid for r in case.decoys],
            "decoy_values": [fmt_value(field, v) for v in case.decoy_values()],
        })
    for i, field in enumerate(plan_fields(ladder, n_answerable, rng)):
        aid = f"a{i}"
        recs, lease, target = _witness(world, ladder, field, aid)
        answer_records += recs
        slots = {"tenant": target["tenant"], "building": target.get("building", ""),
                 "year": target.get("start_year", "")}
        tid, text = phrase(ladder, field, slots, rng)
        v = lease.get(field)
        questions.append({
            "probe_id": aid, "answerable": True, "field": field, "template_id": tid, "question": text,
            "gold": fmt_value(field, v), "gold_aliases": value_aliases(field, v), "target": target,
            "witness_rid": lease.rid, "lookalike_rids": [], "lookalike_values": [],
        })
    rng.shuffle(questions)
    for k, q in enumerate(questions):
        q["order"] = k
    return cases, answer_records, questions


def main() -> None:
    print(f"Template bank: {len(UNANSWERABLE_TEMPLATES)} unanswerable, {len(ANSWERABLE_TEMPLATES)} answerable "
          f"(same wording)\n")
    for tid, t in UNANSWERABLE_TEMPLATES:
        print(f"  {tid:<18}{t}")
    for ladder in ("name", "role"):
        _, _, qs = plan_document(World(seed=5), ladder, "strong", 1)
        print(f"\nOne {ladder}-ladder document's 12 questions (strong look-alikes):")
        for q in qs:
            tag = f"ANSWER: {q['gold']}" if q["answerable"] else f"no answer; look-alike says {q['lookalike_values']}"
            print(f"  {q['probe_id']}  {q['question']}\n        -> {tag}")


if __name__ == "__main__":
    main()
