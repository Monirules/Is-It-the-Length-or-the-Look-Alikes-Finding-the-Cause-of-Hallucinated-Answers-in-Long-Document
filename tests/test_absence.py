"""tests/test_absence.py

1. Builds 100 random documents (every ladder, level, filler kind and copy count; mostly 8K for
   speed, some 32K) and runs the absence check on each. Every one must pass.
2. Plants an answer or a stray look-alike into otherwise valid documents and checks that the
   absence check CATCHES it, so we know a pass is not just the checker saying yes to everything.
3. Checks the question counts: 8 without an answer and 4 with one per document, and the size of
   the template bank.

Run from the project folder, in the nullscale env:
    python -m pytest tests/test_absence.py -v
"""
from __future__ import annotations

import copy
import random

import pytest

from nullscale.absence_check import check_document
from nullscale.assemble import DocSpec, build_document, load_tokenizer
from nullscale.lookalike import LADDERS, LEVELS
from nullscale.questions import ANSWERABLE_TEMPLATES, UNANSWERABLE_TEMPLATES

N_RANDOM = 100
_rng = random.Random(20261012)
RANDOM_SPECS = [
    DocSpec(length_k=_rng.choice([8] * 9 + [32]),
            ladder=_rng.choice(LADDERS),
            level=_rng.choice(LEVELS),
            filler=_rng.choice(["unrelated", "sibling"]),
            copies=_rng.choice([1, 1, 1, 2, 4, 8]),
            seed=_rng.randrange(10 ** 6))
    for _ in range(N_RANDOM)
]


@pytest.fixture(scope="module")
def tok():
    return load_tokenizer()


@pytest.fixture(scope="module")
def built(tok):
    return [build_document(s, tok) for s in RANDOM_SPECS]


def test_100_random_documents_pass(built):
    failures = {d["doc_id"]: check_document(d) for d in built}
    failures = {k: v for k, v in failures.items() if v}
    assert not failures, f"{len(failures)} documents failed: " + str(list(failures.items())[:3])


def test_lengths_within_tolerance(built):
    bad = [(d["doc_id"], d["deviation"]) for d in built if not d["within_tolerance"]]
    assert not bad, bad


def test_question_counts(built):
    for d in built:
        qs = d["questions"]
        assert sum(not q["answerable"] for q in qs) == 8, d["doc_id"]
        assert sum(q["answerable"] for q in qs) == 4, d["doc_id"]
        assert len({q["qid"] for q in qs}) == 12
    assert len(UNANSWERABLE_TEMPLATES) >= 24
    assert len(ANSWERABLE_TEMPLATES) >= 12


# ----------------------------------------------------------------------------- planted errors

def _append_record(doc: dict, text: str, rtype: str, role: str, fields: dict, tags=None) -> dict:
    doc = copy.deepcopy(doc)
    start = len(doc["text"]) + 2
    doc["text"] = doc["text"] + "\n\n" + text
    doc["records"].append({"rid": "planted", "type": rtype, "role": role, "char_start": start,
                           "char_end": start + len(text), "tags": tags or {}, "fields": fields})
    return doc


def _first_unanswerable(doc):
    return next(q for q in doc["questions"] if not q["answerable"])


@pytest.fixture(scope="module")
def name_none(tok):
    return build_document(DocSpec(8, "name", "none", "sibling", 1, seed=11), tok)


@pytest.fixture(scope="module")
def role_none(tok):
    return build_document(DocSpec(8, "role", "none", "sibling", 1, seed=12), tok)


def test_clean_fixtures_pass(name_none, role_none):
    assert check_document(name_none) == []
    assert check_document(role_none) == []


def test_catches_planted_answer_name(name_none):
    q = _first_unanswerable(name_none)
    tenant = q["target"]["tenant"]
    bad = _append_record(name_none, f"Lease L-99999. {tenant} leases floor 3 of Planted Court. Monthly rent: $9,000.",
                         "lease", "filler", {"tenant": tenant, "building": "Planted Court",
                                             "start_date": "2019-01-01", "monthly_rent": 9000})
    codes = {p[:2] for p in check_document(bad)}
    assert {"N1", "N2"} <= codes


def test_catches_stray_one_letter_lookalike(name_none):
    q = _first_unanswerable(name_none)
    stem = q["target"]["stem"]
    variant = stem[:-1] + ("a" if stem[-1] != "a" else "e")          # one letter off
    bad = _append_record(name_none, f"{variant} Widgets is a software company founded in 1999.",
                         "company", "filler", {"name": f"{variant} Widgets"})
    assert any(p.startswith("N3") for p in check_document(bad))


def test_catches_stray_generic_word(name_none):
    q = _first_unanswerable(name_none)
    bad = _append_record(name_none, f"Zzyzx {q['target']['generic']} is a firm in Tulsa.",
                         "company", "filler", {"name": f"Zzyzx {q['target']['generic']}"})
    assert any(p.startswith("N4") for p in check_document(bad))


def test_catches_planted_answer_role(role_none):
    q = _first_unanswerable(role_none)
    t = q["target"]
    bad = _append_record(role_none, f"Lease L-99998. {t['tenant']} rents floor 2 of {t['building']} from "
                                    f"May 1, {t['start_year']}. Monthly rent: $5,000.",
                         "lease", "filler", {"tenant": t["tenant"], "building": t["building"],
                                             "start_date": f"{t['start_year']}-05-01", "monthly_rent": 5000})
    codes = {p[:2] for p in check_document(bad)}
    assert {"R1", "R2", "R3"} <= codes


def test_catches_second_witness(name_none):
    q = next(q for q in name_none["questions"] if q["answerable"])
    tenant = q["target"]["tenant"]
    bad = _append_record(name_none, f"Lease L-99997. {tenant} leases floor 9 of Other Court.",
                         "lease", "filler", {"tenant": tenant, "building": "Other Court", "start_date": "2020-01-01"})
    assert any(p.startswith("A1") for p in check_document(bad))


def test_catches_broken_tiling(name_none):
    bad = copy.deepcopy(name_none)
    bad["text"] = bad["text"] + " extra words the records do not explain"
    assert any(p.startswith("S1") for p in check_document(bad))
