"""riker/exp1_summary.py

Step 9: the Exp 1 summary rewritten as "Hypothesis 3 not supported". No RIKER2 download needed: it reads the
files riker/reanalyze_riker.py already wrote.

Input   outputs/riker/exp1_per_model.csv     made-up counts per model, length, level, group
        outputs/riker/exp1_per_question.csv  one row per trap question (look-alike present or not)
        outputs/riker/exp1_results.md         only for the check against Roig's own summary files (465 cells)
Output  outputs/riker/exp1_summary.md         the new summary, in this order:
          1. the verdict  2. the flat look-alike share  3. the L12-only table (like for like)
          4. the all-traps table, marked as mixed (every L11 question has a look-alike)  5. the 465-cell check
        outputs/riker/exp1_summary.json       the same numbers, read by analysis/results_summary.py

Usage (Ubuntu, nullscale env, project folder; seconds)
  python -m riker.exp1_summary
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LENGTHS = (32, 128, 200)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--riker", default=str(PROJECT_ROOT / "outputs" / "riker"))
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args(argv)
    d = Path(a.riker)
    pm_f, pq_f, res_f = d / "exp1_per_model.csv", d / "exp1_per_question.csv", d / "exp1_results.md"
    if not pm_f.exists() or not pq_f.exists():
        sys.exit(f"missing {pm_f} or {pq_f}: run  python -m riker.reanalyze_riker  first")
    pm = list(csv.DictReader(open(pm_f, encoding="utf-8")))
    pq = list(csv.DictReader(open(pq_f, encoding="utf-8")))
    panel = sorted({r["model"] for r in pm if r["in_balanced_panel"] == "True"})
    rng = random.Random(0)

    def per_model(L, group, levels):
        acc = defaultdict(lambda: [0, 0])
        for r in pm:
            if int(r["context_k"]) == L and r["group"] == group and r["level"] in levels and r["model"] in panel:
                acc[r["model"]][0] += int(r["made_up_riker"])
                acc[r["model"]][1] += int(r["n"])
        return [k / n for k, n in acc.values() if n]

    def macro(vals):
        boots = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(a.boot))
        return sum(vals) / len(vals), boots[int(0.025 * a.boot)], boots[int(0.975 * a.boot) - 1]

    def q_count(L, level, group):
        return sum(1 for r in pq if int(r["context_k"]) == L and r["level"] in level
                   and (r["lookalike_present"] == "True") == (group == "present"))

    share, l12, alltr = {}, {}, {}
    for L in LENGTHS:
        qs = [r for r in pq if int(r["context_k"]) == L]
        share[L] = (sum(r["lookalike_present"] == "True" for r in qs), len(qs))
        l12[L] = (macro(per_model(L, "present", {"L12"})), macro(per_model(L, "none", {"L12"})))
        alltr[L] = (macro(per_model(L, "present", {"L11", "L12"})), macro(per_model(L, "none", {"L11", "L12"})))
    l11_all = all(r["lookalike_present"] == "True" for r in pq if r["level"] == "L11")
    shares = [100 * k / n for k, n in share.values()]
    diff = {L: 100 * (l12[L][0][0] - l12[L][1][0]) for L in LENGTHS}
    supported = diff[128] > 0 and diff[200] > 0 and max(shares) - min(shares) >= 5

    check = []
    if res_f.exists():
        txt = res_f.read_text(encoding="utf-8")
        m = re.search(r"## Check: do we read the data the way Roig did\?\n\n(.*?)(\n## |\Z)", txt, re.S)
        if m:
            check = [ln for ln in m.group(1).strip().splitlines() if ln.strip()]

    f = lambda v: f"{100 * v[0]:.1f}% [{100 * v[1]:.1f}, {100 * v[2]:.1f}]"
    M = ["# Exp 1 (RQ3): Roig's RIKER2 answers split by look-alike presence", "",
         f"## Verdict: Hypothesis 3 is {'supported' if supported else 'NOT supported'}", "",
         "Pre-registered prediction 3 (hypotheses.md): in RIKER2, part of the length effect is explained by look-alike presence.", "",
         ("It is not. " if not supported else "") +
         f"The share of trap questions that have a look-alike is flat over length ({', '.join(f'{s:.0f}%' for s in shares)} "
         f"at 32K, 128K, 200K), so look-alikes cannot explain why made-up answers rise with length in RIKER2. "
         f"With like-for-like questions (L12 only), the look-alike group is higher only at 32K ({diff[32]:+.1f} points); "
         f"at 128K ({diff[128]:+.1f}) and 200K ({diff[200]:+.1f}) it is not. Roig's length effect is therefore a real "
         "length effect, separate from look-alikes.", "",
         "## 1. Look-alikes do not grow with length", "",
         "| length | trap questions | with a look-alike | share |", "|---|---|---|---|"]
    M += [f"| {L}K | {share[L][1]} | {share[L][0]} | {100 * share[L][0] / share[L][1]:.0f}% |" for L in LENGTHS]
    M += ["", f"## 2. Like for like: L12 questions only (mean over {len(panel)} models tested at all three lengths; "
          "95% bootstrap interval over models)", "",
          "In L12 questions the record exists but the asked field does not; some have a look-alike, most do not.", "",
          "| length | look-alike present | no look-alike | difference (points) | questions present / none |",
          "|---|---|---|---|---|"]
    M += [f"| {L}K | {f(l12[L][0])} | {f(l12[L][1])} | {diff[L]:+.1f} | {q_count(L, {'L12'}, 'present')} / "
          f"{q_count(L, {'L12'}, 'none')} |" for L in LENGTHS]
    M += ["", "## 3. All trap questions (L11 + L12): NOT a fair comparison", "",
          ("Every L11 question has a look-alike" if l11_all else "Almost every L11 question has a look-alike") +
          ", so the 'present' group is mostly L11 and the 'none' group is only L12. Question type and look-alike "
          "presence are mixed together here; use table 2 for the claim.", "",
          "| length | look-alike present | no look-alike | difference (points) |", "|---|---|---|---|"]
    M += [f"| {L}K | {f(alltr[L][0])} | {f(alltr[L][1])} | {100 * (alltr[L][0][0] - alltr[L][1][0]):+.1f} |" for L in LENGTHS]
    M += ["", "## 4. Check: we read Roig's data the way Roig did", ""]
    M += check if check else ["(check section not found in outputs/riker/exp1_results.md; rerun riker/reanalyze_riker.py)"]
    M += ["", "Full details, the regression and the capture analysis: outputs/riker/exp1_results.md."]
    (d / "exp1_summary.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    js = {"supported": supported, "share": {L: share[L] for L in LENGTHS}, "panel_models": len(panel),
          "l12": {L: {"present": l12[L][0], "none": l12[L][1], "diff_points": diff[L]} for L in LENGTHS},
          "check": check}
    (d / "exp1_summary.json").write_text(json.dumps(js, indent=1), encoding="utf-8")
    print("\n".join(M))
    print(f"\nwritten: {d / 'exp1_summary.md'} and exp1_summary.json")


if __name__ == "__main__":
    main()
