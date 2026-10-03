"""score/score_all.py  (owner: Jayden; written for the team by M. I. Mahmud)

Runs all scoring rules (refusal_rules, match_answer, capture_tag) on saved answers and makes ONE
results table. This is the official scoring; it replaces the provisional rules in scripts/first_look.py.

Input   every answers file in the agreed format, by default all of
        <paths.outputs.answers>/<exp>/<model>/<prompt>_t<temp>_s<seed>.jsonl
Output  per answers file (large, in the work folder):
          <paths.outputs.scores>/<exp>/<model>/<prompt>_t<temp>_s<seed>.scored.jsonl
        shared and small (project folder, goes to git):
          outputs/results/results_table.md / .csv   one row per condition, all files together
          outputs/results/<exp>_<model>_<prompt>_t<temp>_s<seed>/
              summary.md, scored.csv, fig5_first_run.png/.pdf, fig6_capture.png/.pdf,
              changed_vs_provisional.md  (answers whose label differs from scripts/first_look.py)

Rates come with 95% Wilson intervals. "made up" = share of no-answer questions with label made_up.

Usage (Ubuntu, nullscale env, project folder; no GPU needed)
  python -m score.score_all                                   # every answers file found
  python -m score.score_all --exp exp2 --model qwen3_4b       # only these
  python -m score.score_all --answers path/to/answers.jsonl   # one file
  python -m score.score_all --no-figures                      # faster
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from score.capture_tag import capture_tags  # noqa: E402
from score.match_answer import label_row  # noqa: E402

LEVELS = ("none", "weak", "medium", "strong")
SCORING_VERSION = "score-v1"
GROUP_KEYS = ("exp", "model", "prompt_style", "temperature", "seed", "length_k", "ladder", "level", "copies", "filler")


# ----------------------------------------------------------------------------- statistics

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)


def pct(k: int, n: int) -> str:
    p, lo, hi = wilson(k, n)
    return "n/a" if n == 0 else f"{100 * p:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] ({k}/{n})"


# ----------------------------------------------------------------------------- scoring

class DocumentCache:
    """Reads each NullScale document once (for the capture 'source' tag)."""

    def __init__(self, data_root: Path | None):
        self.data_root = data_root
        self.doc_path: dict[str, str] = {}
        self.cache: dict[str, str | None] = {}
        self.loaded_exps: set[str] = set()

    def _load_exp(self, exp: str) -> None:
        self.loaded_exps.add(exp)
        if not self.data_root:
            return
        qf = self.data_root / exp / "questions.jsonl"
        if qf.exists():
            with open(qf, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        q = json.loads(line)
                        self.doc_path[q["qid"]] = q.get("doc_path")

    def text(self, row: dict) -> str | None:
        exp = row.get("exp")
        if exp and exp not in self.loaded_exps:
            self._load_exp(exp)
        rel = self.doc_path.get(row.get("qid"))
        if not rel:
            return None
        if rel not in self.cache:
            p = self.data_root / rel
            self.cache[rel] = p.read_text(encoding="utf-8") if p.exists() else None
        return self.cache[rel]


def score_rows(rows: list[dict], docs: DocumentCache | None = None) -> list[dict]:
    out = []
    for r in rows:
        lab = label_row(r)
        doc = docs.text(r) if (docs and lab["label"] == "made_up") else None
        tags = capture_tags(r, lab["label"], lab.get("values"), doc)
        s = dict(r)
        s.update({k: lab[k] for k in ("label", "outcome", "refusal", "hedged", "answer_part", "answer_source",
                                      "first_refuses", "values")})
        s.update(tags)
        s["scoring_version"] = SCORING_VERSION
        out.append(s)
    return out


# ----------------------------------------------------------------------------- tables

def condition_table(scored: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in scored:
        groups[tuple(r.get(k) for k in GROUP_KEYS)].append(r)
    table = []
    def order(kv):
        return tuple(f"{LEVELS.index(x):02d}" if k == "level" and x in LEVELS else
                     (f"{float(x):012.3f}" if isinstance(x, (int, float)) else str(x)) for k, x in zip(GROUP_KEYS, kv[0]))
    for key, rs in sorted(groups.items(), key=order):
        un = [r for r in rs if not r["answerable"]]
        an = [r for r in rs if r["answerable"]]
        mu = [r for r in un if r["label"] == "made_up"]
        row = dict(zip(GROUP_KEYS, key))
        p, lo, hi = wilson(len(mu), len(un))
        row.update({
            "n_no_answer": len(un), "made_up": len(mu), "made_up_pct": _r(p), "made_up_lo": _r(lo), "made_up_hi": _r(hi),
            "refused": sum(r["label"] == "refused" for r in un), "other_no_answer": sum(r["label"] == "other" for r in un),
            "refused_but_mentions_lookalike": sum(r["label"] == "refused" and r["mentions_lookalike"] for r in un),
            "captured": sum(r["captured"] for r in mu),
            "capture_pct": _r(len([r for r in mu if r["captured"]]) / len(mu)) if mu else "",
            "n_with_answer": len(an), "correct": sum(r["label"] == "correct" for r in an),
            "wrong_refusal": sum(r["label"] == "wrong_refusal" for r in an), "wrong": sum(r["label"] == "wrong" for r in an),
            "truncated": sum(bool(r.get("truncated")) for r in rs),
        })
        table.append(row)
    return table


def _r(x: float) -> float | str:
    return "" if x != x else round(100 * x, 2)


def write_results_table(table: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "results_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)
    vary = [k for k in GROUP_KEYS if len({str(r[k]) for r in table}) > 1] or ["exp", "model"]
    L = ["# Results table (official scoring, " + SCORING_VERSION + ")", "",
         "One row per condition. **Made up** = share of questions with no answer where the model committed to a value "
         "(95% Wilson interval). **Copied** = made-up answers that copied the look-alike record's value. "
         "**Mentions** = refusals that still quoted the look-alike's value (a strict reading would count them as made up). "
         "**Correct** = questions with an answer answered correctly.", "",
         "| " + " | ".join(vary) + " | made up | copied | mentions | correct (with answer) | wrongly refused |",
         "|" + "---|" * (len(vary) + 5)]
    for r in table:
        mu = r["made_up"]
        L.append("| " + " | ".join(str(r[k]) for k in vary) +
                 f" | {pct(mu, r['n_no_answer'])} | {r['captured']}/{mu} | {r['refused_but_mentions_lookalike']}"
                 f" | {pct(r['correct'], r['n_with_answer'])} | {r['wrong_refusal']}/{r['n_with_answer']} |")
    (out_dir / "results_table.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def write_file_summary(scored: list[dict], out: Path, title: str) -> None:
    un = [r for r in scored if not r["answerable"]]
    an = [r for r in scored if r["answerable"]]
    L = [f"# Official scoring: {title}", "",
         f"Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py ({SCORING_VERSION}).", "",
         f"{len(scored)} answers from {len({r['doc_id'] for r in scored})} documents: "
         f"{len(un)} with no answer, {len(an)} with an answer.", "",
         "## Questions with no answer: made-up answer rate (95% Wilson interval)", "",
         ]
    present = {r.get("level") for r in scored}
    levels = [lv for lv in LEVELS if lv in present] + sorted(x for x in present - set(LEVELS) if x)
    if present <= set(LEVELS):
        L += ["| level | name ladder | role ladder | both |", "|---|---|---|---|"]
        for lv in levels:
            cells = []
            for lad in ("name", "role", None):
                s = [r for r in un if r.get("level") == lv and (lad is None or r.get("ladder") == lad)]
                cells.append(pct(sum(r["label"] == "made_up" for r in s), len(s)))
            L.append(f"| {lv} | " + " | ".join(cells) + " |")
    else:                                     # e.g. Exp 6: filler kind x length
        lens = sorted({r.get("length_k") for r in scored})
        L += ["| filler | " + " | ".join(f"{k}K" for k in lens) + " |", "|---|" + "---|" * len(lens)]
        for lv in levels:
            if not any(r.get("level") == lv for r in un):
                continue
            cells = []
            for k in lens:
                s = [r for r in un if r.get("level") == lv and r.get("length_k") == k]
                cells.append(pct(sum(r["label"] == "made_up" for r in s), len(s)) if s else "-")
            L.append(f"| {lv} | " + " | ".join(cells) + " |")
    strict = [r for r in un if r["label"] == "made_up" or (r["label"] == "refused" and r["mentions_lookalike"])]
    L += ["", "Strict reading (made up, or refused but quoted the look-alike's value): " +
          ", ".join(f"{lv} {pct(sum(r in strict for r in un if r.get('level') == lv), sum(r.get('level') == lv for r in un))}"
                    for lv in levels if any(r.get('level') == lv for r in un))]
    mu = [r for r in un if r["label"] == "made_up"]
    L += ["", "## Where the made-up answers came from", "",
          f"Copied the look-alike record's value: {pct(sum(r['captured'] for r in mu), len(mu))}", "",
          "| source | count |", "|---|---|"]
    for k, v in Counter(r["source"] for r in mu).most_common():
        L.append(f"| {k} | {v} |")
    L += ["", "## Questions with an answer", "",
          f"Correct: {pct(sum(r['label'] == 'correct' for r in an), len(an))}  ",
          f"Wrongly refused: {pct(sum(r['label'] == 'wrong_refusal' for r in an), len(an))}  ",
          f"Wrong value: {pct(sum(r['label'] == 'wrong' for r in an), len(an))}  ",
          f"Other: {pct(sum(r['label'] == 'other' for r in an), len(an))}", "",
          "## Health checks", "",
          f"- labels: {dict(Counter(r['label'] for r in scored))}",
          f"- three-way outcome (plan): {dict(Counter(r['outcome'] for r in scored))}",
          f"- answer part taken from: {dict(Counter(r['answer_source'] for r in scored))}",
          f"- refused first, then gave a value anyway: {sum(r['first_refuses'] and r['label'] == 'made_up' for r in un)}",
          f"- truncated at max_tokens: {sum(bool(r.get('truncated')) for r in scored)}",
          f"- empty responses: {sum(not (r.get('response') or '').strip() for r in scored)}"]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def compare_with_provisional(scored: list[dict], out: Path) -> None:
    """List answers whose official label differs from the provisional first_look label."""
    try:
        from first_look import label as provisional
    except Exception:                                   # first_look not available: skip quietly
        return
    diff = []
    for r in scored:
        old = provisional(r)["label"]
        if old != r["label"]:
            diff.append((old, r))
    L = ["# Answers whose label changed (provisional scripts/first_look.py -> official score/)", "",
         f"{len(diff)} of {len(scored)} answers changed: "
         + ", ".join(f"{a}->{b} {n}" for (a, b), n in Counter((o, r['label']) for o, r in diff).most_common()), ""]
    for old, r in diff:
        L += [f"### {r['qid']} ({r['ladder']}, {r['level']}, {'has answer' if r['answerable'] else 'no answer'}): "
              f"{old} -> **{r['label']}**",
              f"- question: {r['question']}",
              f"- look-alike value: {', '.join(r.get('lookalike_values') or []) or '-'}",
              f"- answer part ({r['answer_source']}): {r['answer_part'][:300]}",
              f"- reply: {(r.get('response') or '').strip().replace(chr(10), ' ')[:500]}", ""]
    (out / "changed_vs_provisional.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nchanged vs provisional scoring: {len(diff)} of {len(scored)} (see changed_vs_provisional.md)")


# ----------------------------------------------------------------------------- main

def find_answer_files(root: Path, exp: str | None, model: str | None) -> list[Path]:
    pat = f"{exp or '*'}/{model or '*'}/*.jsonl"
    return sorted(p for p in root.glob(pat)
                  if not p.name.endswith(".scored.jsonl") and not re.search(r"\.part\d+of\d+\.jsonl$", p.name))


def main(argv=None) -> list[dict]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", nargs="*", help="answers .jsonl file(s); default: all under paths.yaml outputs.answers")
    ap.add_argument("--exp")
    ap.add_argument("--model")
    ap.add_argument("--data", help="NullScale data root (default: paths.yaml data.nullscale)")
    ap.add_argument("--scores-out", help="where .scored.jsonl go (default: paths.yaml outputs.scores)")
    ap.add_argument("--results-out", default=str(PROJECT_ROOT / "outputs" / "results"))
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--dpi", type=int, default=900)
    a = ap.parse_args(argv)

    paths = None
    try:
        from nullscale.config import load_paths
        paths = load_paths()
    except Exception as e:                              # configs missing: only explicit paths work
        print(f"(paths.yaml not loaded: {e})")
    if a.answers:
        files = [Path(p) for p in a.answers]
    else:
        if not paths:
            sys.exit("give --answers")
        files = find_answer_files(Path(paths["outputs"]["answers"]), a.exp, a.model)
    if not files:
        sys.exit("no answers files found. Run run/run_vllm.py (or scripts/run_5070.sh) first.")
    data_root = Path(a.data) if a.data else (Path(paths["data"]["nullscale"]) if paths else None)
    scores_root = Path(a.scores_out) if a.scores_out else (Path(paths["outputs"]["scores"]) if paths else None)
    results_root = Path(a.results_out)
    docs = DocumentCache(data_root)

    all_scored = []
    for f in files:
        rows = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        if not rows:
            continue
        scored = score_rows(rows, docs)
        all_scored += scored
        r0 = scored[0]
        tag = f"{r0['exp']}_{r0['model']}_{r0['prompt_style']}_t{float(r0['temperature']):g}_s{r0['seed']}"
        print(f"\n=== {f}  ({len(rows)} answers) ===")
        if scores_root:
            sp = scores_root / r0["exp"] / r0["model"] / (f.stem + ".scored.jsonl")
            sp.parent.mkdir(parents=True, exist_ok=True)
            with open(sp, "w", encoding="utf-8") as fo:
                for r in scored:
                    fo.write(json.dumps(r, ensure_ascii=False) + "\n")
        out = results_root / tag
        out.mkdir(parents=True, exist_ok=True)
        keys = ["qid", "ladder", "level", "copies", "filler", "length_k", "answerable", "field", "question", "gold",
                "lookalike_values", "response", "answer_part", "label", "outcome", "captured", "mentions_lookalike",
                "source", "refusal", "hedged", "truncated", "n_prompt_tokens", "cached_prompt_tokens"]
        with open(out / "scored.csv", "w", newline="", encoding="utf-8") as fo:
            w = csv.DictWriter(fo, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in scored:
                w.writerow({**r, "lookalike_values": "; ".join(r.get("lookalike_values") or [])})
        title = (f"{r0['model']} ({r0.get('quantization')}), {r0['exp']}, {r0['prompt_style']} prompt, "
                 f"T={float(r0['temperature']):g}, {len({r['doc_id'] for r in scored})} documents at "
                 f"{'/'.join(sorted({str(r.get('length_k')) + 'K' for r in scored}))}. Official scoring.")
        write_file_summary(scored, out, title)
        compare_with_provisional(scored, out)
        if not a.no_figures and all(r.get("level") in LEVELS for r in scored):
            try:
                from first_look import figures
                figures(scored, out, title, a.dpi)
            except Exception as e:
                print(f"(figures skipped: {e})")
    table = condition_table(all_scored)
    write_results_table(table, results_root)
    print(f"\nresults table -> {results_root / 'results_table.md'} (+ .csv); per-file folders in {results_root}")
    return all_scored


if __name__ == "__main__":
    main()
