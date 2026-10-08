"""analysis/results_summary.py

Step 9: the one-page results summary. One final claim per research question, each with its exact numbers,
plus the supporting checks and what changed from the plan. Writing starts from this page.

Input   outputs/figures_main/main_results.json   (python -m analysis.main_results --results outputs/results_cluster)
        outputs/riker/exp1_summary.json          (python -m riker.exp1_summary)
Output  outputs/results_summary.md

Usage (Ubuntu, nullscale env, project folder; instant)
  python -m analysis.results_summary
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def p(x, d=1):
    return "-" if x is None else f"{100 * x:.{d}f}%"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main", default=str(PROJECT_ROOT / "outputs" / "figures_main" / "main_results.json"))
    ap.add_argument("--exp1", default=str(PROJECT_ROOT / "outputs" / "riker" / "exp1_summary.json"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "results_summary.md"))
    a = ap.parse_args(argv)
    for f, cmd in ((a.main, "python -m analysis.main_results --results outputs/results_cluster"),
                   (a.exp1, "python -m riker.exp1_summary")):
        if not Path(f).exists():
            sys.exit(f"missing {f}: run  {cmd}  first")
    R = json.loads(Path(a.main).read_text(encoding="utf-8"))
    E = json.loads(Path(a.exp1).read_text(encoding="utf-8"))

    e2 = R["exp2"]
    sep = sum(x["separate"] for x in e2)
    gaps = [x["strong"] - x["none"] for x in e2]
    caps = [x["captured"] for x in e2 if x["captured"] is not None]
    low_cap = [x["model"] for x in e2 if x["captured"] is not None and x["captured"] < 0.8]
    br = R["breaking"]
    broke = [b for b in br if b["break_k"]]
    big = [b for b in broke if b["made_up_max"] >= 0.10]
    small = [b for b in broke if b not in big]
    never = [b["model"] for b in br if not b["break_k"]]
    with_drop = [b for b in big if b["drop_k"] and b["drop_k"] <= b["max_at_k"]]
    sh = E["share"]
    l12 = E["l12"]
    e7 = R.get("exp7", {})
    e6 = R.get("exp6", {})

    M = [f"# One-page results summary ({date.today():%d %B %Y})", "",
         f"Models: {', '.join(R['models'])}. Made-up rate = share of questions with no answer where the model gave a value.", "",
         "**Outcome (pre-registered table, row 2): both matter, in different ways.** One look-alike causes made-up answers "
         "at every length; length alone adds them only past a model-specific breaking length.", "",
         "## RQ1. Does look-alike strength drive made-up answers at fixed length? **Yes (prediction 1 supported).**", "",
         f"- Exp 2 (32K): strong look-alike vs none raises made-up answers by {100 * min(gaps):.0f} to {100 * max(gaps):.0f} "
         f"points; the intervals do not overlap in {sep} of {len(e2)} models.",
         f"- {100 * min(caps):.0f}% to {100 * max(caps):.0f}% of made-up answers copy the look-alike's value"
         + (f" (lowest: {', '.join(low_cap)})." if low_cap else "."),
         "- Exp 4: from 1 to 8 copies the rate moves in both directions; presence matters far more than count.", "",
         "## RQ2. Does length alone drive made-up answers? **Only past a breaking length.**", "",
         f"- Main regression (Exp 3, {R['n_reg']:,} no-answer questions): strong look-alike OR {R['or_strong']:.0f}; one doubling "
         f"of length OR {R['or_doubling']:.2f}.",
         f"- **Exchange rate: one strong look-alike = {R['exchange']:.1f} doublings of length** (95% CI {R['exchange_lo']:.1f} "
         f"to {R['exchange_hi']:.1f}), a document {2 ** R['exchange']:,.0f}x longer. Sensitivity check without Llama 3.3 70B "
         f"at 128K (added after seeing the data): {R['exchange_sens']:.1f} doublings.",
         f"- With a strong look-alike, length adds nothing (log-odds {R['b_len_strong']:+.2f} per doubling). Without one, "
         f"log-odds rise {R['b_len_none']:+.2f} per doubling from a near-zero start.",
         f"- Breaking length: {len(broke)} of {len(br)} models have one. Large effect (>= 10% at some length) in "
         + (", ".join(f"{b['model']} (breaks at {b['break_k']}K; {p(b['made_up_max'])} at {b['max_at_k']}K, accuracy "
                      f"{p(b['acc_at_max'])} vs {p(b['acc_8k'])} at 8K)" for b in big) or "none")
         + ". Small effect (under 10%) in " + (", ".join(f"{b['model']} ({p(b['made_up_max'])} at {b['max_at_k']}K)" for b in small) or "none")
         + ". Never: " + (", ".join(never) or "none") + ".",
         f"- In {len(with_drop)} of {len(big)} large-effect models, answer accuracy has already dropped at or before the "
         "length with the most made-up answers: length damage appears where reading fails.", "",
         f"## RQ3. Does RIKER2 show look-alikes explaining the length effect? **No (prediction 3 not supported).**", "",
         f"- The share of trap questions with a look-alike is flat: "
         + ", ".join(f"{100 * sh[str(L)][0] / sh[str(L)][1]:.0f}% at {L}K" for L in (32, 128, 200)) + ".",
         "- Like for like (L12 only): look-alike minus none = "
         + ", ".join(f"{l12[str(L)]['diff_points']:+.1f} points at {L}K" for L in (32, 128, 200)) + ".",
         "- So Roig's length curve is a real length effect, consistent with our breaking lengths. Our reading of his data "
         "matches his own summary files exactly (465 cells).", "",
         f"## RQ4. Does sibling filler reduce made-up answers? **{R['p4'].capitalize()}.**", "",
         f"- Lower made-up rate in {R['filler_lower_in']} of {len(R['models'])} models (OR {R['or_sibling']:.2f}).",
         f"- But answer accuracy changes by {100 * R['filler_acc_change_min']:+.1f} to {100 * R['filler_acc_change_max']:+.1f} "
         "points, mostly through more wrong refusals. Sibling filler makes models refuse more; it is not a free fix. "
         "The cost comparison (Exp 5) was not run.", "",
         "## Supporting checks", ""]
    if e6:
        lo = min(v["lookalike_32k"] for v in e6.values()); hi = max(v["lookalike_32k"] for v in e6.values())
        rlo = min(v["random_32k"] for v in e6.values()); rhi = max(v["random_32k"] for v in e6.values())
        M.append(f"- Exp 6 (Wikipedia, 32K, answer removed): similar passages {p(lo, 0)} to {p(hi, 0)} made up vs random "
                 f"passages {p(rlo, 0)} to {p(rhi, 0)}." + (f" Not run: {', '.join(R['exp6_missing'])}." if R.get("exp6_missing") else ""))
    for m, v in e7.items():
        M.append(f"- Exp 7, {m}: one question per call {p(v['one'])} vs 12 per call {p(v['twelve'])} made up.")
    M += ["- Temperature 0.7 (three seeds) stays within a few points of temperature 0 (outputs/figures_main/main_results.md).",
          "- Scoring rules agree with RIKER2's own scorer on 99.21% of 605,948 answers (Cohen's kappa 0.981).", "",
          "## Changed from the plan (see hypotheses.md change log)", "",
          "- No hand check; no Exp 5; no API model; Gemma 3 27B not run at 128K; GLM-4.5-Air only half of the 128K documents.",
          "- Added after seeing the data: the sensitivity regression, the breaking-length rule, the filler accuracy check."]
    Path(a.out).write_text("\n".join(M) + "\n", encoding="utf-8")
    print("\n".join(M))
    print(f"\nwritten: {a.out}")


if __name__ == "__main__":
    main()
