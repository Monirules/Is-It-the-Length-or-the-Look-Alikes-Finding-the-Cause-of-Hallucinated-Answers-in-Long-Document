"""scripts/first_look.py

A first look at real model answers, for the Step 6 check and for showing the professor.

PROVISIONAL SCORING. The official rules are score/refusal_rules.py, match_answer.py and
capture_tag.py; when those exist, score_all.py replaces the scoring below. These rules are simple and
written down so anyone can check them:
  final answer the text after the last "Answer:" if the model wrote one, else the whole reply
  refusal      the first sentence says the answer is not in the records (not found, not listed,
               no record, cannot find, does not mention, does not have, ...)
  answerable   correct       a form of the gold answer appears in the response
               wrong refusal the response refuses
               wrong         anything else
  no answer    made up       the final answer commits to a value of the kind asked (an amount for
                             rent/deposit, a date, a floor number), EVEN IF it hedges
                             ("not listed, but maybe $5,000")
               refused       it refuses up front; values it mentions about OTHER records are context.
                             If one of them is the look-alike's value, mentions_lookalike is set and
                             summary.md reports those separately (a strict reading counts them)
               captured      a made-up answer that contains the look-alike record's value
               refused       it refuses and commits to no value
               other         neither (e.g. an empty or off-topic reply)

Outputs (outputs/first_run/<exp>_<model>_<prompt>/ in the project folder):
  scored.csv           every answer with its label
  summary.md           rates with 95% Wilson intervals, by ladder and look-alike level
  sample_answers.md    20 answers across levels, to read together (the Step 6 check)
  fig5_first_run.png/.pdf    made-up rate by look-alike level, and accuracy on answerable questions
  fig6_capture.png/.pdf      where the made-up answers came from

Usage (Ubuntu, nullscale env, project folder; no GPU needed):
  python scripts/first_look.py --model qwen3_4b --exp exp2
  python scripts/first_look.py --answers path/to/answers.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

LEVELS = ("none", "weak", "medium", "strong")

# ----------------------------------------------------------------------------- provisional scoring

_REFUSAL = re.compile(
    r"\b(?:not (?:\w+ ){0,2}(?:in|found|mentioned|listed|provided|available|stated|included|specified|given|present"
    r"|recorded|contained)\b"
    r"|no (?:record|information|mention|data|lease|entry|details?)\b"
    r"|(?:cannot|can't|can not|unable to) (?:find|determine|locate|answer|identify)"
    r"|(?:does|do|did) not (?:appear|exist|mention|contain|include|state|say|specify|list)"
    r"|(?:doesn't|don't|didn't) (?:appear|exist|mention|contain|include|state|say|specify|list)"
    r"|(?:does not|doesn't|do not|don't) have|no such|not referenced"
    r"|there is no|isn't (?:in|listed|mentioned)|none of the records)", re.I)
_MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december|"
           "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
_VALUE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+\b|\b\d+\b|\b(?:" + _MONTHS + r")\b\.?\s+\d{1,2}", re.I)


def first_sentence(text: str) -> str:
    t = text.strip()
    m = re.search(r"(?<=[.!?])\s|\n", t)
    return t[:m.start()] if m else t


def is_refusal(text: str) -> bool:
    return bool(_REFUSAL.search(first_sentence(text))) or text.strip().upper().startswith("NOT FOUND")


def _norm(s: str) -> str:
    return re.sub(r"[\s,$]", "", s.lower())


def contains_value(response: str, value: str, field: str) -> bool:
    if not value:
        return False
    if field == "floor":
        return re.search(rf"(?<!\d){re.escape(value)}(?!\d)", response) is not None
    return _norm(value) in _norm(response)


_TYPED = {
    "money": re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+\b"),
    "date": re.compile(r"\b(?:" + _MONTHS + r")\b\.?\s+\d{1,2},?\s+\d{4}|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b", re.I),
    "floor": re.compile(r"(?:\bfloor(?: number)?(?: is)?\s*#?\s*(\d{1,3})\b|^\s*(\d{1,3})\s*\.?\s*$|\b(\d{1,3})(?:st|nd|rd|th) floor)", re.I | re.M),
}
_KIND = {"monthly_rent": "money", "deposit": "money", "start_date": "date", "end_date": "date", "floor": "floor"}
_HEDGE = re.compile(r"\b(maybe|perhaps|probably|likely|approximately|roughly|could be|might be|possibly|presumably|I (?:would )?guess|my best guess|estimated?)\b", re.I)


def final_answer(text: str) -> str:
    """The part of the reply that is the answer: after the last 'Answer:' if the model wrote one."""
    parts = re.split(r"\bAnswer\s*:", text, flags=re.I)
    return parts[-1].strip() if len(parts) > 1 else text.strip()


def typed_values(text: str, field: str) -> list[str]:
    """Values of the KIND the question asks for (money for rent/deposit, dates, a floor number)."""
    return [m.group(0) for m in _TYPED[_KIND[field]].finditer(text)]


def label(row: dict) -> dict:
    """See the module docstring. Uses the final answer; counts only values of the asked kind."""
    resp = row.get("response") or ""
    field = row["field"]
    final = final_answer(resp)
    refusal = is_refusal(final) or (final is resp.strip() and is_refusal(resp))
    out = {"refusal": refusal, "mentions_lookalike": False}
    if row["answerable"]:
        aliases = row.get("gold_aliases") or [row.get("gold") or ""]
        correct = any(contains_value(final, g, field) for g in aliases if g)
        out["captured"] = False
        out["label"] = ("correct" if correct and not refusal else
                        "wrong_refusal" if refusal and not correct else "correct" if correct else "wrong")
        return out
    la_vals = [v for v in row.get("lookalike_values") or [] if v]
    out["mentions_lookalike"] = any(contains_value(resp, v, field) for v in la_vals)
    has_answer_line = final is not resp.strip() and final != resp.strip()
    if refusal and not has_answer_line and not _HEDGE.search(resp):
        # refuses up front; any values are context about OTHER records ("the only lease there is 2018")
        out["captured"] = False
        out["label"] = "refused"
        return out
    vals = typed_values(final, field)
    captured = any(contains_value(final, v, field) for v in la_vals)
    out["captured"] = captured
    if captured or vals:
        out["label"] = "made_up"
    else:
        out["label"] = "refused" if refusal else "other"
    return out


# ----------------------------------------------------------------------------- stats

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)


def _pct(k, n):
    p, lo, hi = wilson(k, n)
    return "n/a" if n == 0 else f"{100 * p:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] ({k}/{n})"


# ----------------------------------------------------------------------------- outputs

def write_summary(rows: list[dict], out: Path, title: str) -> None:
    un = [r for r in rows if not r["answerable"]]
    an = [r for r in rows if r["answerable"]]
    lines = [f"# First look: {title}", "",
             "PROVISIONAL scoring (see scripts/first_look.py); official scoring is score/.", "",
             f"{len(rows)} answers from {len({r['doc_id'] for r in rows})} documents: "
             f"{len(un)} with no answer, {len(an)} with an answer.", "",
             "## Questions with no answer: made-up answer rate (95% Wilson interval)", "",
             "| level | name ladder | role ladder | both |", "|---|---|---|---|"]
    for lv in LEVELS:
        cells = []
        for lad in ("name", "role", None):
            s = [r for r in un if r["level"] == lv and (lad is None or r["ladder"] == lad)]
            cells.append(_pct(sum(r["label"] == "made_up" for r in s), len(s)))
        lines.append(f"| {lv} | " + " | ".join(cells) + " |")
    ment = [r for r in un if r["label"] == "refused" and r.get("mentions_lookalike")]
    lines += ["", "Refused, but mentioned the look-alike record's value as context (NOT counted as made up above; "
              "a strict reading would count them): "
              + ", ".join(f"{lv} {sum(r['level'] == lv for r in ment)}" for lv in LEVELS)]
    mu = [r for r in un if r["label"] == "made_up"]
    lines += ["", "## Where the made-up answers came from", "",
              f"Made-up answers that copied the look-alike record's value: "
              f"{_pct(sum(r['captured'] for r in mu), len(mu))}", "",
              "| level | made up | copied look-alike |", "|---|---|---|"]
    for lv in LEVELS:
        s = [r for r in mu if r["level"] == lv]
        lines.append(f"| {lv} | {len(s)} | {sum(r['captured'] for r in s)} |")
    lines += ["", "## Questions with an answer", "",
              f"Correct: {_pct(sum(r['label'] == 'correct' for r in an), len(an))}  ",
              f"Wrongly refused: {_pct(sum(r['label'] == 'wrong_refusal' for r in an), len(an))}  ",
              f"Wrong value: {_pct(sum(r['label'] == 'wrong' for r in an), len(an))}", "",
              "## Health checks", "",
              f"- labels: {dict(Counter(r['label'] for r in rows))}",
              f"- truncated at max_tokens: {sum(bool(r.get('truncated')) for r in rows)}",
              f"- empty responses: {sum(not (r.get('response') or '').strip() for r in rows)}"]
    cached = [r["cached_prompt_tokens"] for r in rows if r.get("cached_prompt_tokens") and r.get("call_size", 1) > 1]
    prompt = [r["n_prompt_tokens"] for r in rows if r.get("cached_prompt_tokens") and r.get("call_size", 1) > 1]
    if cached:
        lines.append(f"- document reuse: questions 2-12 took {sum(cached) / len(cached):,.0f} of "
                     f"{sum(prompt) / len(prompt):,.0f} prompt tokens from the cache on average")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def write_samples(rows: list[dict], out: Path, n: int = 20, seed: int = 0) -> None:
    """20 answers to read together: 3 per level x 4 levels of no-answer questions + 8 with an answer,
    preferring a mix of labels."""
    rng = random.Random(seed)
    pick = []
    for lv in LEVELS:
        pool = [r for r in rows if not r["answerable"] and r["level"] == lv]
        rng.shuffle(pool)
        pool.sort(key=lambda r: r["label"] != "made_up")          # show made-up ones first if any
        pick += pool[:3]
    pool = [r for r in rows if r["answerable"]]
    rng.shuffle(pool)
    pick += pool[:n - len(pick)]
    L = ["# 20 answers to read together", "",
         "Check each PROVISIONAL label. Write your own label in the last column if you disagree.", ""]
    for i, r in enumerate(pick, 1):
        resp = (r.get("response") or "").strip().replace("\n", " ")
        L += [f"### {i}. {r['ladder']} ladder, level {r['level']}, {'HAS an answer' if r['answerable'] else 'NO answer'}",
              f"- **Question:** {r['question']}",
              f"- **Gold:** {r.get('gold') or '(none: not in the document)'}"
              + (f"  |  **look-alike value:** {', '.join(r['lookalike_values'])}" if r.get("lookalike_values") else ""),
              f"- **Model:** {resp[:400]}",
              f"- **Provisional label:** {r['label']}{' (copied look-alike)' if r.get('captured') else ''}"
              "  |  **Your label:** ____", ""]
    (out / "sample_answers.md").write_text("\n".join(L), encoding="utf-8")


def figures(rows: list[dict], out: Path, title: str, dpi: int) -> None:
    import matplotlib.pyplot as plt
    from make_figures import BLUE, GRID, INK, INK2, MUTED, ORANGE, SURFACE, FULL_W, save
    un = [r for r in rows if not r["answerable"]]
    an = [r for r in rows if r["answerable"]]

    # ---- fig5: made-up rate by level, two ladders; and answerable accuracy
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULL_W, 2.5), gridspec_kw={"width_ratios": [1.7, 1], "wspace": 0.45})
    x = list(range(len(LEVELS)))
    for off, lad, col, mk in ((-0.09, "name", BLUE, "o"), (0.09, "role", ORANGE, "s")):
        ps, lo, hi, ns = [], [], [], []
        for lv in LEVELS:
            s = [r for r in un if r["ladder"] == lad and r["level"] == lv]
            p, l_, h_ = wilson(sum(r["label"] == "made_up" for r in s), len(s))
            ps.append(100 * p), lo.append(100 * (p - l_)), hi.append(100 * (h_ - p)), ns.append(len(s))
        xs = [i + off for i in x]
        a.errorbar(xs, ps, yerr=[lo, hi], color=col, marker=mk, ms=5, lw=2, capsize=2.5, elinewidth=1,
                   label=f"{lad} ladder", zorder=3, mec=SURFACE, mew=1)
    a.set_xticks(x, LEVELS)
    a.set_xlabel("look-alike level in the document")
    a.set_ylabel("made-up answers (%)")
    a.set_ylim(0, 100)
    a.yaxis.grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
    a.legend(loc="upper left", handlelength=1.6)
    n_per = Counter((r["ladder"], r["level"]) for r in un)
    a.set_title("(a) Questions with no answer", loc="left")
    a.text(0.99, 0.97, f"n per point ≈ {min(n_per.values()) if n_per else 0}–{max(n_per.values()) if n_per else 0}"
           "\nbars: 95% Wilson interval", transform=a.transAxes, ha="right", va="top", fontsize=6.4, color=INK2)

    cats = [("correct", "correct", BLUE), ("wrong_refusal", "wrongly refused", MUTED), ("wrong", "wrong value", ORANGE)]
    lads = ["name", "role"]
    left = [0.0, 0.0]
    for key, lab, col in cats:
        vals = []
        for lad in lads:
            s = [r for r in an if r["ladder"] == lad]
            vals.append(100 * sum(r["label"] == key for r in s) / len(s) if s else 0)
        b.barh(range(2), vals, left=left, height=0.55, color=col, edgecolor=SURFACE, linewidth=1.5, label=lab, zorder=2)
        for i, v in enumerate(vals):
            if v >= 12:
                b.text(left[i] + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=7,
                       color="#ffffff" if col != MUTED else INK)
        left = [l_ + v for l_, v in zip(left, vals)]
    b.set_yticks(range(2), [f"{l} ladder" for l in lads])
    b.tick_params(axis="y", length=0)
    b.spines["left"].set_visible(False)
    b.set_xlim(0, 100)
    b.set_xlabel("% of questions with an answer")
    b.legend(loc="upper center", bbox_to_anchor=(0.45, -0.24), ncol=3, fontsize=6.4, handlelength=1.0, columnspacing=0.8)
    b.set_title("(b) Questions with an answer", loc="left")
    fig.text(0.01, 1.02, title, fontsize=7.2, color=INK2)
    save(fig, out, "fig5_first_run", dpi)

    # ---- fig6: made-up answers by source
    fig, ax = plt.subplots(figsize=(FULL_W * 0.55, 2.3))
    cap = [sum(1 for r in un if r["level"] == lv and r["label"] == "made_up" and r["captured"]) for lv in LEVELS]
    oth = [sum(1 for r in un if r["level"] == lv and r["label"] == "made_up" and not r["captured"]) for lv in LEVELS]
    ax.bar(x, cap, width=0.6, color=BLUE, edgecolor=SURFACE, linewidth=1.5, label="copied the look-alike's value", zorder=2)
    ax.bar(x, oth, bottom=cap, width=0.6, color=ORANGE, edgecolor=SURFACE, linewidth=1.5, label="other made-up value", zorder=2)
    for i, (c_, o_) in enumerate(zip(cap, oth)):
        ax.text(i, c_ + o_, str(c_ + o_), ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_xticks(x, LEVELS)
    ax.set_xlabel("look-alike level")
    ax.set_ylabel("made-up answers")
    ax.set_ylim(0, max([c + o for c, o in zip(cap, oth)] + [1]) * 1.3)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=6.6, handlelength=1.0)
    ax.set_title("Where made-up answers came from", loc="left")
    save(fig, out, "fig6_capture", dpi)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="qwen3_4b")
    ap.add_argument("--exp", default="exp2")
    ap.add_argument("--prompt", default="normal")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--answers", default=None, help="answers .jsonl (default: from paths.yaml and the options above)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dpi", type=int, default=900)
    a = ap.parse_args()
    if a.answers:
        path = Path(a.answers)
    else:
        from nullscale.config import load_paths
        path = (Path(load_paths()["outputs"]["answers"]) / a.exp / a.model /
                f"{a.prompt}_t{a.temperature:g}_s{a.seed}.jsonl")
    if not path.exists():
        sys.exit(f"no answers at {path}. Run run/run_vllm.py first.")
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    for r in rows:
        r.update(label(r))
    out = Path(a.out) if a.out else PROJECT_ROOT / "outputs" / "first_run" / f"{rows[0]['exp']}_{rows[0]['model']}_{rows[0]['prompt_style']}"
    out.mkdir(parents=True, exist_ok=True)
    keys = ["qid", "ladder", "level", "copies", "filler", "length_k", "answerable", "field", "question", "gold",
            "lookalike_values", "response", "label", "captured", "mentions_lookalike", "refusal", "truncated", "n_prompt_tokens",
            "cached_prompt_tokens"]
    with open(out / "scored.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "lookalike_values": "; ".join(r.get("lookalike_values") or [])})
    title = (f"{rows[0]['model']} ({rows[0]['quantization']}), {rows[0]['exp']}, {rows[0]['prompt_style']} prompt, "
             f"T={rows[0]['temperature']:g}, {len({r['doc_id'] for r in rows})} documents at "
             f"{'/'.join(sorted({str(r['length_k']) + 'K' for r in rows}))}. Provisional scoring.")
    write_summary(rows, out, title)
    write_samples(rows, out)
    figures(rows, out, title, a.dpi)
    print(f"\nsaved to {out}: summary.md, sample_answers.md, scored.csv, fig5_first_run, fig6_capture")


if __name__ == "__main__":
    main()
