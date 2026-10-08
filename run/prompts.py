"""run/prompts.py

The three fixed prompts. They never change between models or conditions; PROMPT_VERSION goes into
every saved answer so a later change can never be mixed up with an earlier run.

  normal   answer from the records; if they do not contain the answer, say so
  strict   the same, plus an exact abstention phrase and an explicit ban on guessing
  batch12  all 12 questions of a document in one call, numbered answers (Exp 7)

Design rules
  * The document comes FIRST and the question LAST, inside a single user message. Every question
    about the same document then shares an identical prompt prefix, so vLLM's prefix cache
    computes the long document once and reuses it for the other 11 questions.
  * No system message: some model families (e.g. Gemma) do not accept one, and a system message
    would be one more thing that differs between models.

Run  `python -m run.prompts`  to print all three prompts with a short example document.
"""
from __future__ import annotations

import hashlib
import re

STYLES = ("normal", "strict", "batch12")
ABSTAIN_PHRASE = "NOT FOUND"

_HEAD = ("Below is a collection of records from a company archive. Each paragraph is one record.\n\n"
         "<records>\n{document}\n</records>\n\n")

NORMAL = _HEAD + (
    "Answer the question using only the records above. If the records do not contain the answer, "
    "say that it is not in the records.\n\n"
    "Question: {question}\n"
    "Answer briefly.")

STRICT = _HEAD + (
    "Answer the question using only the records above. The answer must be stated explicitly in one "
    "record about exactly the company, building and period the question names. Do not guess, do not "
    "use a similar-looking record, and do not combine records. If no record states the answer, reply "
    f"with exactly: {ABSTAIN_PHRASE}\n\n"
    "Question: {question}\n"
    "Answer briefly.")

BATCH12 = _HEAD + (
    "Answer each question using only the records above. If the records do not contain the answer to "
    "a question, say that it is not in the records.\n\n"
    "Questions:\n{numbered}\n\n"
    "Reply with one line per question, in order, in the form \"<number>. <answer>\". Answer briefly.")

TEMPLATES = {"normal": NORMAL, "strict": STRICT, "batch12": BATCH12}
PROMPT_VERSION = "v1-" + hashlib.sha1("\n".join(TEMPLATES[s] for s in STYLES).encode()).hexdigest()[:8]

# Exp 6 (real text): the same two prompts, worded for Wikipedia passages instead of company records.
# They have their own version tag, so PROMPT_VERSION of the NullScale prompts above stays unchanged.
_WIKI_HEAD = ("Below is a collection of passages from Wikipedia. Each paragraph is one passage.\n\n"
              "<passages>\n{document}\n</passages>\n\n")
WIKI_TEMPLATES = {
    "normal": _WIKI_HEAD + (
        "Answer the question using only the passages above. If the passages do not contain the answer, "
        "say that it is not in the passages.\n\n"
        "Question: {question}\n"
        "Answer briefly."),
    "strict": _WIKI_HEAD + (
        "Answer the question using only the passages above. The answer must be stated explicitly in a "
        "passage about exactly what the question asks. Do not guess, do not use your own knowledge, and do "
        "not use a similar-looking passage. If no passage states the answer, reply with exactly: "
        f"{ABSTAIN_PHRASE}\n\n"
        "Question: {question}\n"
        "Answer briefly."),
}
PROMPT_VERSION_WIKI = "wiki-v1-" + hashlib.sha1("\n".join(WIKI_TEMPLATES[s] for s in ("normal", "strict")).encode()).hexdigest()[:8]


def prompt_version(source: str = "records") -> str:
    return PROMPT_VERSION_WIKI if source == "wikipedia" else PROMPT_VERSION


def build_messages(document: str, question: str, style: str = "normal", source: str = "records") -> list[dict]:
    """Chat messages for ONE question (normal or strict). source="wikipedia" for Exp 6 documents."""
    if style not in ("normal", "strict"):
        raise ValueError(f"style must be normal or strict for one question, got {style}")
    tpl = WIKI_TEMPLATES[style] if source == "wikipedia" else TEMPLATES[style]
    return [{"role": "user", "content": tpl.format(document=document, question=question)}]


def build_batch_messages(document: str, questions: list[str]) -> list[dict]:
    """Chat messages for all questions of a document in one call (batch12)."""
    numbered = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
    return [{"role": "user", "content": BATCH12.format(document=document, numbered=numbered)}]


_LINE = re.compile(r"^\s*(?:\*\*)?\(?(\d{1,2})[.):\]]\s*(?:\*\*)?\s*(.*)$")


def parse_batch_answer(text: str, n: int) -> list[str]:
    """Split a numbered batch reply into n answers ("" where a number is missing).
    Lines that do not start with a number are added to the previous answer."""
    out: dict[int, list[str]] = {}
    cur = None
    for line in text.splitlines():
        m = _LINE.match(line)
        if m and 1 <= int(m.group(1)) <= n and int(m.group(1)) not in out:
            cur = int(m.group(1))
            out[cur] = [m.group(2).strip()]
        elif cur is not None and line.strip():
            out[cur].append(line.strip())
    return [" ".join(out.get(i, [])).strip() for i in range(1, n + 1)]


def main() -> None:
    doc = ("Lease L-10234. Harbor Lane Bakery leases space on floor 4 of Elm Court. The term runs from "
           "March 1, 2019 to March 1, 2024, and the monthly rent is $4,200.\n\n"
           "Weather log, Tarnel Station, June 3, 2021: clear. High 24.1 C, low 12.0 C.")
    print(f"PROMPT_VERSION = {PROMPT_VERSION}\n")
    for style in ("normal", "strict"):
        print(f"==================== {style} ====================")
        print(build_messages(doc, "What monthly rent does Harbor Lane Bakery pay under its lease?", style)[0]["content"])
        print()
    print("==================== batch12 ====================")
    print(build_batch_messages(doc, ["What monthly rent does Harbor Lane Bakery pay under its lease?",
                                     "Which floor does Quarry Point Florist lease?"])[0]["content"])
    print("\nparse_batch_answer example:",
          parse_batch_answer("1. $4,200\n2. Not in the records.", 2))


if __name__ == "__main__":
    main()
