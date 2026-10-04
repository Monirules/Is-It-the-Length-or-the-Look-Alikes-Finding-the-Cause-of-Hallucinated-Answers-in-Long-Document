"""score/refusal_rules.py  (owner: Jayden; written for the team by M. I. Mahmud)

Decides whether a model said "not found". Fixed written rules, no AI judge.

The rule in one line: a reply is a refusal when its ANSWER PART says the answer is not in the
document and does not hedge into a guess.

Which part of the reply is the answer part (in this order):
  1. the text after the LAST "Answer:" / "Final answer:" if the model wrote one;
  2. else the last sentence that starts with a conclusion word ("Therefore", "So", "Thus", "Hence",
     "In conclusion", "In summary", "Overall");
  3. else the FIRST sentence (most models put the verdict first).
Earlier sentences are context. A model that writes "Pousquieck Studios is not in the records. The
closest match, Pousquieck Pharma, is on floor 20. Answer: Not in the records." refused; it only
mentioned the look-alike (see capture_tag.mentions_lookalike).

What counts as "not found" (case does not matter):
  - abstention tokens as the whole answer: N/A, NA, Unknown, NONE, Not found, NOT FOUND, Not available,
    Not applicable, Cannot be determined, Not specified, No information, No answer
  - phrases: "not in the records", "not mentioned", "not listed", "not provided", "not stated",
    "no record of", "no information", "no mention", "cannot find", "unable to determine",
    "does not appear", "does not exist", "does not mention", "does not have", "there is no",
    "no such", "none of the records", "not referenced", "isn't listed", ...
A hedge turns a refusal into a guess: maybe, perhaps, probably, likely, approximately, roughly,
"could be", "might be", possibly, presumably, "I guess", "my best guess", estimate(d), "if I had to".

Run on RIKER2 raw answers (Step 5 check), after riker/download_riker.py:
  python -m score.refusal_rules --riker            # agreement with RIKER2's own scorer on L11/L12
  python -m score.refusal_rules --text "It is not listed, but maybe 5,000."
"""
from __future__ import annotations

import argparse
import re

# ----------------------------------------------------------------------------- patterns

_NOT_WORDS = (r"in|found|mentioned|listed|provided|available|stated|included|specified|given|present|recorded"
              r"|contained|referenced|shown|indicated|documented|disclosed|known|determinable|applicable")
REFUSAL = re.compile(
    r"\b(?:"
    rf"not (?:\w+ ){{0,2}}(?:{_NOT_WORDS})\b"
    r"|(?:isn't|aren't|wasn't|weren't) (?:\w+ ){0,2}(?:" + _NOT_WORDS + r")\b"
    r"|no (?:\w+ ){0,1}(?:record|records|information|info|mention|data|lease|entry|entries|details?|evidence|evaluation"
    r"|report|document|answer|such)\b"
    r"|(?:cannot|can't|can not|could not|couldn't|unable to|not able to) (?:be )?(?:find|found|determine|determined"
    r"|locate|located|answer|answered|identify|identified|confirm|confirmed|verify|verified)"
    r"|(?:does|do|did) not (?:appear|exist|mention|contain|include|state|say|specify|list|have|show|indicate|provide)"
    r"|(?:doesn't|don't|didn't) (?:appear|exist|mention|contain|include|state|say|specify|list|have|show|indicate|provide)"
    r"|there (?:is|are|was|were) no\b|none of the (?:records|documents|reports)"
    r"|no such|neither\b.{0,40}\bnor\b"
    r")", re.I)

# The whole answer part is one of these (RIKER2 asks for "N/A", "Unknown" or "NONE").
ABSTAIN_TOKEN = re.compile(
    r"^\W*(?:n/?a|na|unknown|none|not found|not available|not applicable|not in the (?:records|documents?)"
    r"|cannot be determined|can't be determined|undetermined|not determinable|not specified|not stated"
    r"|no information|no answer|no record|not mentioned|not provided|not listed)\W*$", re.I)

HEDGE = re.compile(
    r"\b(?:maybe|perhaps|probably|likely|approximately|roughly|around|could be|might be|may be|possibly"
    r"|presumably|i (?:would )?guess|my best guess|best guess|estimated?|if i had to|my guess)\b", re.I)

_FINAL = re.compile(r"\b(?:final\s+answer|answer)\s*[:：]", re.I)
_CONCLUDE = re.compile(r"^(?:therefore|so|thus|hence|in conclusion|in summary|overall|to summarize|consequently)\b", re.I)
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(*])|\n+")

# a reply that only hedges or apologises is not an answer either
_EMPTY = re.compile(r"^\W*$")


# ----------------------------------------------------------------------------- helpers

def clean(text: str | None) -> str:
    """Remove thinking blocks and markdown emphasis; collapse spaces."""
    t = text or ""
    t = re.sub(r"<think>.*?</think>", " ", t, flags=re.S | re.I)
    t = re.sub(r"^.*?</think>", " ", t, flags=re.S | re.I)          # an unclosed opening tag was cut off
    t = t.replace("**", "").replace("__", "").replace("`", "")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(clean(text)) if s and s.strip()]


def first_sentence(text: str) -> str:
    s = sentences(text)
    return s[0] if s else ""


def answer_part(text: str) -> tuple[str, str]:
    """(answer part, where it came from): 'final_line' | 'conclusion' | 'first_sentence' | 'empty'."""
    t = clean(text)
    if not t:
        return "", "empty"
    parts = _FINAL.split(t)
    if len(parts) > 1 and parts[-1].strip():
        tail = parts[-1].strip()
        tail = re.split(r"\n\s*\n", tail)[0].strip()                 # stop at the next paragraph
        return tail.strip(" []"), "final_line"
    sents = sentences(t)
    if not sents:                                      # only separators / unusual whitespace
        return t, "first_sentence"
    concl = [s for s in sents[1:] if _CONCLUDE.match(s)]
    if concl:
        return concl[-1], "conclusion"
    return sents[0], "first_sentence"


def is_abstain_token(text: str) -> bool:
    return bool(ABSTAIN_TOKEN.match(clean(text).strip(" .\"'[]")))


def says_not_found(text: str) -> bool:
    """True if this piece of text says the answer is not there (token or phrase)."""
    t = clean(text)
    return is_abstain_token(t) or bool(REFUSAL.search(t))


def has_hedge(text: str) -> bool:
    return bool(HEDGE.search(clean(text)))


def refusal_info(text: str) -> dict:
    """Everything the other rules need about refusing. Keys:
       refusal         the answer part says not found and does not hedge
       answer_part     the text that was judged
       source          final_line | conclusion | first_sentence | empty
       first_refuses   the first sentence says not found (useful to see "refuse, then answer anyway")
       hedged          a hedge word anywhere in the reply
       empty           no text at all"""
    part, src = answer_part(text)
    hedged = has_hedge(text)
    first = first_sentence(text)
    part_refuses = says_not_found(part) if part else False
    return {
        "refusal": bool(part_refuses and not has_hedge(part)),
        "answer_part": part,
        "source": src,
        "first_refuses": says_not_found(first) if first else False,
        "hedged": hedged,
        "empty": src == "empty",
    }


def is_refusal(text: str) -> bool:
    return refusal_info(text)["refusal"]


# ----------------------------------------------------------------------------- RIKER2 check

def riker_check(limit_runs: int | None = None) -> None:
    """Compare these rules with RIKER2's own scorer on the trap questions (L11, L12).
    RIKER2 marks a trap answer correct only when the extracted final answer is N/A / Unknown / NONE.
    Our rule should agree almost always; the disagreements show where the two rule sets differ."""
    import random
    from collections import Counter
    from pathlib import Path

    from riker.common import iter_run_answers, riker_root
    root = riker_root()
    out_dir = Path(__file__).resolve().parents[1] / "outputs" / "riker"
    out_dir.mkdir(parents=True, exist_ok=True)
    conf = Counter()
    first_only = Counter()
    disagree = []
    n = 0
    for row in iter_run_answers(root, levels=("L11", "L12"), limit_runs=limit_runs):
        if row["failed"]:
            continue
        ours = is_refusal(row["response"])
        theirs = bool(row["riker_correct"])
        conf[(ours, theirs)] += 1
        first_only[(says_not_found(first_sentence(row["response"])), theirs)] += 1
        if ours != theirs and len(disagree) < 4000:
            disagree.append(row)
        n += 1
    if not n:
        raise SystemExit("no RIKER2 answers found. Run riker/download_riker.py first.")
    agree = conf[(True, True)] + conf[(False, False)]
    rng = random.Random(0)
    rng.shuffle(disagree)
    L = ["# Refusal rules tested on RIKER2's raw answers (trap questions L11 and L12)", "",
         f"{n:,} answers. RIKER2's scorer says correct (= abstained) when the final answer is N/A, Unknown or NONE.", "",
         "| | RIKER2: abstained | RIKER2: answered |", "|---|---|---|",
         f"| our rule: refusal | {conf[(True, True)]:,} | {conf[(True, False)]:,} |",
         f"| our rule: not a refusal | {conf[(False, True)]:,} | {conf[(False, False)]:,} |", "",
         f"**Agreement: {100 * agree / n:.2f}%** (Cohen's kappa {_kappa(conf):.3f})", "",
         "First sentence only (the plan's simplest rule): agreement "
         f"{100 * (first_only[(True, True)] + first_only[(False, False)]) / n:.2f}%", "",
         "## 40 disagreements to read", ""]
    for r in disagree[:40]:
        L += [f"- **{r['question_id']}** ({r['model']}, {r['context_k']}K) RIKER2 "
              f"{'abstained' if r['riker_correct'] else 'answered'}, ours "
              f"{'refusal' if not r['riker_correct'] else 'not refusal'}; extracted `{(r.get('riker_extracted') or '')[:80]}`",
              f"  > {clean(r['response'])[:400].replace(chr(10), ' ')}"]
    (out_dir / "refusal_rules_on_riker.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:14]))
    print(f"\nsaved {out_dir / 'refusal_rules_on_riker.md'}")


def _kappa(conf) -> float:
    n = sum(conf.values())
    po = (conf[(True, True)] + conf[(False, False)]) / n
    a1 = (conf[(True, True)] + conf[(True, False)]) / n
    b1 = (conf[(True, True)] + conf[(False, True)]) / n
    pe = a1 * b1 + (1 - a1) * (1 - b1)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", help="judge one reply and print the details")
    ap.add_argument("--riker", action="store_true", help="test the rules on RIKER2's raw answers")
    ap.add_argument("--limit-runs", type=int, default=None, help="only the first N RIKER2 runs (quick test)")
    a = ap.parse_args()
    if a.text:
        for k, v in refusal_info(a.text).items():
            print(f"{k:14s} {v}")
    elif a.riker:
        riker_check(a.limit_runs)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
