"""tests/test_scoring.py  (owner: Jayden; written for the team by M. I. Mahmud)

Tricky example answers with the label a careful human would give. The scoring rules
(score/refusal_rules.py, score/match_answer.py, score/capture_tag.py) must label every one correctly.
Most replies below are real answers from Qwen3 4B in the first PC run (Step 6), lightly shortened;
the rest are the hard cases named in the plan ("It is not listed, but maybe 5,000").

Run from the project folder, in the nullscale env:
    python -m pytest tests/test_scoring.py -v
"""
from __future__ import annotations

import pytest

from score.capture_tag import capture_tags
from score.match_answer import label_answer, parse_dates, parse_floors, parse_money
from score.refusal_rules import answer_part, is_refusal

# (id, field, look-alike values, reply, expected label, expected captured)
NO_ANSWER = [
    # --- plain refusals
    ("refuse_plain", "deposit", [], "The records do not contain information about Cloncler Holdings' lease at "
     "Semquoax Place or any security deposit related to such a lease. Therefore, the answer is not in the records.",
     "refused", False),
    ("refuse_token_na", "monthly_rent", [], "N/A", "refused", False),
    ("refuse_not_found_caps", "floor", ["20"], "NOT FOUND", "refused", False),
    ("refuse_final_answer_line", "end_date", [], "I checked every lease.\n\nFinal answer: Unknown", "refused", False),
    ("refuse_does_not_have", "start_date", [], "The archive does not have a record for Diendpai Holdings.", "refused", False),
    ("refuse_no_such", "deposit", [], "There is no such lease in the records.", "refused", False),
    ("refuse_markdown", "monthly_rent", [], "**Not in the records.**", "refused", False),
    # --- refusals that mention the look-alike as context: still refused (mentions_lookalike is set)
    ("refuse_mentions_lookalike_answer_line", "floor", ["20"],
     "The records do not mention \"Pousquieck Studios.\" The closest match is \"Pousquieck Pharma,\" which leases "
     "space on floor 20 of Keartdris Center.\n\nAnswer: Not in the records.", "refused", False),
    ("refuse_mentions_other_year", "end_date", ["July 28, 2024"],
     "The records do not contain information about a 2021 lease between Rernbeart Robotics and Hostdres Court. The "
     "lease mentioned starts on July 30, 2022, and ends on July 28, 2024. Therefore, there is no 2021 lease between "
     "them, and the expiration date is not in the records.", "refused", False),
    ("refuse_value_then_conclusion", "monthly_rent", ["$6,700"],
     "The lease between Skolkem Engineering and Thommis Point started in 2015, not 2014. The monthly rent is $6,700. "
     "Therefore, there is no lease between Skolkem Engineering and Thommis Point that started in 2014.", "refused", False),
    ("refuse_information_about_is_not_a_hedge", "deposit", [],
     "There is no information about a deposit for Brietrirt Outfitters' lease.", "refused", False),
    ("refuse_with_year_only", "monthly_rent", [],
     "No lease for Gielcam Supply began in 2019, so the rent for that lease is not in the records.", "refused", False),
    # --- made up: plain
    ("madeup_plain_floor", "floor", ["29"], "The space leased by Cainweil Interiors is on floor 29.", "made_up", True),
    ("madeup_plain_money", "monthly_rent", ["$6,050"], "The monthly rent on Praindwoux Outfitters' lease is $6,050.",
     "made_up", True),
    ("madeup_plain_date", "end_date", ["April 10, 2024"], "Quoamcheal Brewing's lease ends on April 10, 2024.",
     "made_up", True),
    ("madeup_date_other_format", "start_date", ["December 30, 2018"], "Answer: 2018-12-30", "made_up", True),
    ("madeup_money_no_symbol", "deposit", ["$12,400"], "12400", "made_up", True),
    ("madeup_money_k", "monthly_rent", ["$5,000"], "About $5k per month.", "made_up", True),
    ("madeup_ordinal_floor", "floor", ["12"], "They lease the 12th floor.", "made_up", True),
    ("madeup_word_floor", "floor", ["3"], "Third floor.", "made_up", True),
    # --- made up while hedging or after refusing (the plan's key example)
    ("madeup_hedge_after_refusal", "monthly_rent", [], "It is not listed, but maybe 5,000.", "made_up", False),
    ("madeup_hedge_probably", "deposit", ["$9,800"], "The deposit is not stated, but it is probably $9,800.",
     "made_up", True),
    ("madeup_refuse_then_conclude_value", "monthly_rent", ["$8,650"],
     "The records do not mention Laskous Networks. The lease mentioned is for Laskoes Networks, which pays $8,650 per "
     "month. Therefore, the monthly rent Laskoes Networks pays under its lease is $8,650.", "made_up", True),
    ("madeup_refuse_then_answer_line", "end_date", ["January 28, 2027"],
     "This exact lease is not listed. The closest is the 2022 lease.\nAnswer: January 28, 2027", "made_up", True),
    ("madeup_invented_value", "monthly_rent", ["$7,900"], "The monthly rent is $3,200.", "made_up", False),
    ("madeup_estimate", "deposit", [], "I cannot find it; my best guess is $10,000.", "made_up", False),
    # --- other: no refusal and no value of the asked kind
    ("other_empty", "monthly_rent", [], "", "other", False),
    ("other_wrong_kind", "monthly_rent", ["$4,000"], "The lease is on floor 12 of Keartdris Center.", "other", False),
    ("other_question_back", "floor", [], "Could you tell me which company you mean?", "other", False),
    ("other_year_is_not_money", "deposit", [], "The lease began in 2019.", "other", False),
]

# (id, field, gold aliases, reply, expected label)
WITH_ANSWER = [
    ("correct_money", "monthly_rent", ["$20,200", "20,200", "20200"], "Toxlund Ventures pays $20,200 per month.", "correct"),
    ("correct_money_other_form", "deposit", ["$58,950"], "The deposit was 58950 dollars.", "correct"),
    ("correct_date_iso", "end_date", ["February 9, 2025", "2025-02-09"], "It ends 2025-02-09.", "correct"),
    ("correct_date_other_order", "start_date", ["May 19, 2022"], "The lease began on 19 May 2022.", "correct"),
    ("correct_floor_words_between", "floor", ["16"], "The floor number on Wiertdrex Holdings' lease is 16.", "correct"),
    ("correct_floor_ordinal", "floor", ["19"], "Bendtom Foods leases the 19th floor.", "correct"),
    ("wrong_refusal", "deposit", ["$38,400"], "The security deposit on that lease is not in the records.", "wrong_refusal"),
    ("wrong_refusal_despite_value_in_context", "floor", ["27"],
     "The records do not specify which floor. The lease information states floor 27, but this is from a different "
     "lease record. Therefore, the answer is not in the records.", "wrong_refusal"),
    ("wrong_value", "monthly_rent", ["$4,550"], "The monthly rent is $4,500.", "wrong"),
    ("wrong_date_off_by_one_day", "end_date", ["March 20, 2027"], "It ends on March 21, 2027.", "wrong"),
    ("other_no_value", "floor", ["4"], "Tiemfoan Printworks has a lease at Keartdris Center.", "other"),
]


@pytest.mark.parametrize("cid,field,la,reply,expected,captured", NO_ANSWER, ids=[c[0] for c in NO_ANSWER])
def test_no_answer_questions(cid, field, la, reply, expected, captured):
    res = label_answer(reply, field, answerable=False)
    assert res["label"] == expected, f"{cid}: got {res['label']} (answer part: {res['answer_part']!r})"
    row = {"field": field, "answerable": False, "response": reply, "lookalike_values": la}
    tags = capture_tags(row, res["label"], res.get("values"))
    assert tags["captured"] == captured, f"{cid}: captured {tags['captured']}"


@pytest.mark.parametrize("cid,field,gold,reply,expected", WITH_ANSWER, ids=[c[0] for c in WITH_ANSWER])
def test_with_answer_questions(cid, field, gold, reply, expected):
    res = label_answer(reply, field, answerable=True, gold_aliases=gold)
    assert res["label"] == expected, f"{cid}: got {res['label']} (answer part: {res['answer_part']!r})"


def test_case_count():
    assert len(NO_ANSWER) + len(WITH_ANSWER) >= 30


def test_three_way_outcome():
    assert label_answer("N/A", "deposit", False)["outcome"] == "correct"
    assert label_answer("$5,000", "deposit", False)["outcome"] == "made_up"
    assert label_answer("$4,500", "deposit", True, ["$4,550"])["outcome"] == "made_up"
    assert label_answer("Not in the records.", "deposit", True, ["$4,550"])["outcome"] == "other"


def test_mentions_lookalike_flag():
    reply = ("The records do not mention Suxtrend Interiors. Suxtrend Logistics is on floor 18 of Sieckthi Hall.\n\n"
             "Answer: Not in the records.")
    res = label_answer(reply, "floor", False)
    tags = capture_tags({"field": "floor", "answerable": False, "response": reply, "lookalike_values": ["18"]},
                        res["label"], res["values"])
    assert res["label"] == "refused" and tags["mentions_lookalike"] and not tags["captured"]


def test_capture_source_with_document():
    doc = "Lease A: rent $7,900 per month. Lease B: rent $3,200 per month."
    row = {"field": "monthly_rent", "answerable": False, "response": "It is $3,200.", "lookalike_values": ["$7,900"]}
    res = label_answer(row["response"], "monthly_rent", False)
    assert capture_tags(row, res["label"], res["values"], doc)["source"] == "other_record"
    row["response"] = "It is $1,111."
    res = label_answer(row["response"], "monthly_rent", False)
    assert capture_tags(row, res["label"], res["values"], doc)["source"] == "not_in_document"


def test_value_parsers():
    assert parse_money("$5,000 and 1,250.50 and $3k, year 2021") == [5000.0, 1250.5, 3000.0]
    assert parse_dates("Jan 5, 2024; 2024-01-05; 5 January 2024; 1/5/2024") == ["2024-01-05"]
    assert parse_dates("February 30, 2024") == []
    assert parse_floors("floor 7, the 12th floor, Floor #3") == [7, 3, 12] or set(parse_floors(
        "floor 7, the 12th floor, Floor #3")) == {3, 7, 12}


def test_answer_part_order():
    assert answer_part("Blah.\nFinal answer: N/A")[1] == "final_line"
    assert answer_part("Not here. Therefore, it is $5.")[1] == "conclusion"
    assert answer_part("The rent is $5. It was a good lease.")[1] == "first_sentence"
    assert is_refusal("Unknown") and not is_refusal("Final answer: No")
