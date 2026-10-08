"""score/match_answer.py

Labels each answer, after cleaning spaces, capital letters, "$", commas and date formats.

Detailed label (column `label`)
  question WITH an answer in the document
    correct         the answer part contains the gold value (any written form of it)
    wrong_refusal   the model said "not found" although the answer is there
    wrong           the model gave a different value of the asked kind
    other           neither (empty, off-topic, no value)
  question with NO answer in the document (the trap questions)
    refused         the model said "not found" (this is the right behaviour)
    made_up         the answer part commits to a value of the asked kind, EVEN IF it hedges
                    ("It is not listed, but maybe $5,000" is made up)
    other           neither (empty, off-topic, asks a question back, ...)

Plain three-way label from the plan (column `outcome`)
  correct   = correct (with answer) or refused (no answer)
  made_up   = made_up (no answer) or wrong (with answer: a wrong value was given)
  other     = everything else, including wrong_refusal

"Value of the asked kind": money for monthly_rent / deposit, a full date for start_date / end_date,
a floor number for floor. A number of another kind (a year, a floor in a rent question) is not an
answer to the question.

Only the ANSWER PART of the reply is judged (score/refusal_rules.answer_part): the final "Answer:"
line, else the concluding sentence, else the first sentence. If the answer part neither refuses nor
gives a value, the whole reply is searched for a committed value as a fallback.

Usage
  from score.match_answer import label_row        # row = one saved answer (agreed format)
  python -m score.match_answer --field monthly_rent --no-answer --text "Not listed, maybe $5,000."
"""
from __future__ import annotations

import argparse
import datetime as dt
import re

from score.refusal_rules import (answer_part, clean, has_hedge, is_abstain_token, refusal_info, says_not_found,
                                 sentences)

KIND = {"monthly_rent": "money", "deposit": "money", "rent": "money", "security_deposit": "money",
        "start_date": "date", "end_date": "date", "floor": "floor",
        "nq_answer": "text"}                     # Exp 6 (Natural Questions): free-text answers

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
     "november", "december"], 1)}
_MON_ABBR = {k[:3]: v for k, v in _MONTHS.items()} | {"sept": 9}
_MONTH_RE = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"

_DATE_PATTERNS = [
    re.compile(rf"\b(?P<mon>{_MONTH_RE})\.?\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<year>\d{{4}})\b", re.I),
    re.compile(rf"\b(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<mon>{_MONTH_RE})\.?,?\s+(?P<year>\d{{4}})\b", re.I),
    re.compile(r"\b(?P<year>\d{4})-(?P<mnum>\d{1,2})-(?P<day>\d{1,2})\b"),
    re.compile(r"\b(?P<mnum>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})\b"),
]
_MONEY = re.compile(r"(?:\$|usd\s*|us\$)\s?(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<k>k|thousand)?\b"
                    r"|\b(?P<num2>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{4,}(?:\.\d+)?)\s*(?P<k2>k|thousand)?\s*(?:dollars|usd)?\b",
                    re.I)
_ORD_WORDS = {w: i for i, w in enumerate(
    ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh",
     "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth",
     "twentieth"], 1)}
_FLOOR = re.compile(
    r"\bfloor(?:\s+(?:number|no\.?))?(?:\s+(?:is|was|of))?\s*[:#]?\s*(?P<a>\d{1,3})\b"
    r"|\b(?P<b>\d{1,3})(?:st|nd|rd|th)[\s-]+floor\b"
    r"|\b(?P<w>" + "|".join(_ORD_WORDS) + r")[\s-]+floor\b"
    r"|^\W*(?:floor\s*)?(?P<c>\d{1,3})(?:st|nd|rd|th)?\W*$"
    r"|\blevel\s+(?P<d>\d{1,3})\b"
    r"|\bfloor(?:\s+number)?\b[^.\d\n]{0,80}?\b(?:is|was|are|were|=)\s*(?:on\s+)?(?:the\s+)?(?:floor\s+)?#?(?P<e>\d{1,3})(?:st|nd|rd|th)?\b(?![,/-]\d)",
    re.I | re.M)


# ----------------------------------------------------------------------------- normalising values

def norm_text(s: str | None) -> str:
    """Lower case, one space, no surrounding punctuation."""
    return re.sub(r"\s+", " ", (s or "").lower()).strip(" .,:;!?\"'()[]")


def parse_dates(text: str) -> list[str]:
    """Every full date in the text, as ISO 'YYYY-MM-DD' (invalid dates are skipped)."""
    out = []
    for pat in _DATE_PATTERNS:
        for m in pat.finditer(text or ""):
            g = m.groupdict()
            try:
                mon = g.get("mnum")
                mon = int(mon) if mon else _MON_ABBR[g["mon"].lower()[:4] if g["mon"].lower().startswith("sept")
                                                     else g["mon"].lower()[:3]]
                d = dt.date(int(g["year"]), mon, int(g["day"]))
            except (ValueError, KeyError):
                continue
            out.append(d.isoformat())
    return list(dict.fromkeys(out))


def parse_money(text: str) -> list[float]:
    """Every money amount: $5,000 / 5,000 / 5000 dollars / $5k. Plain years (1900-2099 without $ or comma)
    are not money."""
    out = []
    for m in _MONEY.finditer(text or ""):
        num = m.group("num") or m.group("num2")
        k = m.group("k") or m.group("k2")
        raw = num.replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        if not m.group("num") and "," not in num and re.fullmatch(r"(19|20)\d\d", raw):
            continue                                   # a year, not an amount
        if k:
            v *= 1000
        out.append(v)
    return list(dict.fromkeys(out))


def parse_floors(text: str) -> list[int]:
    out = []
    for m in _FLOOR.finditer(text or ""):
        if m.group("w"):
            out.append(_ORD_WORDS[m.group("w").lower()])
        else:
            v = next(x for x in (m.group("a"), m.group("b"), m.group("c"), m.group("d"), m.group("e")) if x)
            out.append(int(v))
    return list(dict.fromkeys(out))


def values_of_kind(text: str, kind: str) -> list:
    """Normalised values of one kind found in the text."""
    if kind == "money":
        return parse_money(text)
    if kind == "date":
        return parse_dates(text)
    if kind == "floor":
        return parse_floors(text)
    return []


def normalise_value(value: str | None, kind: str):
    """The single normalised value of a gold or look-alike string (None if it cannot be read)."""
    if value is None:
        return None
    if kind == "floor":
        v = parse_floors(str(value)) or ([int(value)] if str(value).strip().isdigit() else [])
    else:
        v = values_of_kind(str(value), kind)
    return v[0] if v else None


def same_value(a, b, kind: str) -> bool:
    if a is None or b is None:
        return False
    if kind == "money":
        return abs(float(a) - float(b)) < 0.5
    return a == b


def contains_value(text: str, value: str | None, kind: str) -> bool:
    """Does the text state this value (in any written form)?"""
    target = normalise_value(value, kind)
    if target is None:
        return bool(value) and norm_text(value) in norm_text(text)
    return any(same_value(v, target, kind) for v in values_of_kind(text, kind))


# ----------------------------------------------------------------------------- labelling

def committed_values(text: str, kind: str) -> tuple[list, str]:
    """Values of the asked kind that the reply COMMITS to, and the text they came from.
    Uses the answer part; if the answer part neither refuses nor holds a value, falls back to any
    sentence (outside refusal sentences) that states a value."""
    part, _src = answer_part(text)
    vals = values_of_kind(part, kind)
    if vals or says_not_found(part):
        return vals, part
    for s in sentences(text):
        if says_not_found(s) and not has_hedge(s):
            continue
        v = values_of_kind(s, kind)
        if v:
            return v, s
    return [], part


def label_answer(response: str, field: str, answerable: bool, gold_aliases: list[str] | None = None,
                 gold: str | None = None) -> dict:
    """Label one reply. Returns label, outcome, refusal, hedged, answer_part, values."""
    kind = KIND.get(field, "money")
    info = refusal_info(response)
    part = info["answer_part"]
    out = {"refusal": info["refusal"], "hedged": info["hedged"], "answer_part": part,
           "answer_source": info["source"], "first_refuses": info["first_refuses"]}
    if info["empty"]:
        out.update(label="other", outcome="other", values=[])
        return out
    vals, src_text = committed_values(response, kind)
    out["values"] = [str(v) for v in vals]
    part_refuses = says_not_found(part)
    hedged_part = has_hedge(src_text) or has_hedge(part)

    if answerable:
        aliases = [g for g in (gold_aliases or []) if g] or ([gold] if gold else [])
        hit = any(contains_value(src_text, g, kind) for g in aliases) or \
            any(contains_value(part, g, kind) for g in aliases)
        if hit and not (part_refuses and not values_of_kind(part, kind)):
            lab = "correct"
        elif info["refusal"] or (part_refuses and not vals):
            lab = "wrong_refusal"
        elif vals:
            lab = "wrong"
        else:
            lab = "other"
        out["label"] = lab
        out["outcome"] = {"correct": "correct", "wrong": "made_up"}.get(lab, "other")
        return out

    # question with no answer
    if part_refuses and not hedged_part and not values_of_kind(part, kind):
        lab = "refused"
    elif vals:
        lab = "made_up"                       # a committed value, hedged or not
    elif part_refuses or is_abstain_token(part):
        lab = "refused"                       # a hedged refusal without any value is still a refusal
    else:
        lab = "other"
    out["label"] = lab
    out["outcome"] = {"refused": "correct", "made_up": "made_up"}.get(lab, "other")
    return out


def _norm_qa(s: str) -> str:
    """Standard open-domain QA normalisation (lower case, no punctuation, no articles)."""
    s = re.sub(r"[^\w\s]", " ", (s or "").lower().replace(",", ""))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def label_text_answer(response: str, answerable: bool, gold_aliases: list[str] | None) -> dict:
    """Exp 6: the answer is free text (a name, a place, a year...). A reply that does not refuse and
    says something in its answer part COMMITS to an answer."""
    info = refusal_info(response)
    part = info["answer_part"]
    out = {"refusal": info["refusal"], "hedged": info["hedged"], "answer_part": part,
           "answer_source": info["source"], "first_refuses": info["first_refuses"]}
    if info["empty"]:
        out.update(label="other", outcome="other", values=[])
        return out
    refuses = says_not_found(part) and not has_hedge(part)
    committed = "" if refuses else part.strip()
    out["values"] = [committed] if committed else []
    if answerable:
        hit = any(f" {_norm_qa(g)} " in f" {_norm_qa(part)} " for g in (gold_aliases or []) if _norm_qa(g))
        lab = "correct" if hit else ("wrong_refusal" if refuses else ("wrong" if committed else "other"))
        out.update(label=lab, outcome={"correct": "correct", "wrong": "made_up"}.get(lab, "other"))
    else:
        lab = "refused" if refuses else ("made_up" if committed else "other")
        out.update(label=lab, outcome={"refused": "correct", "made_up": "made_up"}.get(lab, "other"))
    return out


def label_row(row: dict) -> dict:
    """Label one saved answer in the agreed format (README.md)."""
    if KIND.get(row["field"]) == "text":
        return label_text_answer(row.get("response") or "", bool(row["answerable"]), row.get("gold_aliases"))
    return label_answer(row.get("response") or "", row["field"], bool(row["answerable"]),
                        row.get("gold_aliases"), row.get("gold"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", required=True)
    ap.add_argument("--field", default="monthly_rent", choices=sorted(KIND))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--no-answer", action="store_true", help="the question has no answer (default)")
    g.add_argument("--gold", help="the gold answer (the question has an answer)")
    a = ap.parse_args()
    res = label_answer(a.text, a.field, bool(a.gold), [a.gold] if a.gold else None, a.gold)
    for k, v in res.items():
        print(f"{k:14s} {v}")


if __name__ == "__main__":
    main()
