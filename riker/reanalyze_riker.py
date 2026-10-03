"""riker/reanalyze_riker.py  (owner: Jayden; written for the team by M. I. Mahmud)

Exp 1 (RQ3): Roig's made-up answer rate, computed SEPARATELY for trap questions with a look-alike
record and without one, at 32K, 128K and 200K. No new model runs: only RIKER2's released answers.

Made-up answer (fabrication), as in Roig (2026): on a trap question (L11, L12), the model did not give
the expected N/A / Unknown / NONE, by RIKER2's own scorer (riker_correct is false). Replies that failed
(empty or an error, e.g. the context did not fit) are left out and counted separately.
A second label from OUR refusal rules (score/refusal_rules.py) is reported next to it.

How models are combined
  Rates are first computed per model (all its runs and temperatures pooled), then averaged over models
  that have answers at all three lengths, so that a model with many runs does not dominate.
  95% intervals: bootstrap over models (2,000 resamples). Pooled Wilson intervals are in the CSV.

Output (project folder)
  outputs/riker/fig_exp1_riker.png (900 dpi) + .pdf    THE Exp 1 chart
  outputs/riker/exp1_results.md                        tables, regression, checks against Roig's numbers
  outputs/riker/exp1_per_model.csv                     every model x length x group
  outputs/riker/exp1_per_question.csv                  every trap question x length

Usage (Ubuntu/WSL, nullscale env, project folder; after find_lookalikes.py; 3-10 minutes)
  python -m riker.reanalyze_riker
  python -m riker.reanalyze_riker --temps 0.0       # only temperature-0 runs
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

from riker.common import CONTEXTS, OUT_DIR, TRAP_LEVELS, iter_cache, riker_root  # noqa: E402
from score.refusal_rules import is_abstain_token, is_refusal  # noqa: E402

GROUPS = ("present", "none")


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)


def load_lookalikes(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"{path} missing. Run: python -m riker.find_lookalikes")
    out = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["parse_ok"] != "True":
                continue
            r["present"] = r["lookalike_present"] == "True"
            r["values"] = json.loads(r.get("lookalike_values") or "[]")
            out[(int(r["context_k"]), r["question_id"])] = r
    return out


def _num(s: str):
    m = re.fullmatch(r"\$?\s*(-?\d[\d,]*(?:\.\d+)?)", s.strip())
    return float(m.group(1).replace(",", "")) if m else None


def same_answer(a: str | None, b: str | None) -> bool:
    """Does a model's extracted answer equal a look-alike record's value? Numbers by value, text by words."""
    if not a or not b:
        return False
    a, b = a.strip().strip(".\"' "), b.strip().strip(".\"' ")
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return abs(na - nb) < 0.5
    ca, cb = re.sub(r"\W+", " ", a.lower()).strip(), re.sub(r"\W+", " ", b.lower()).strip()
    if not ca or not cb:
        return False
    return ca == cb or (min(len(ca), len(cb)) >= 4 and (ca in cb or cb in ca))


# ----------------------------------------------------------------------------- collecting

def collect(root: Path, la: dict, temps: set | None, platforms: set | None):
    cells = defaultdict(lambda: [0, 0, 0])            # (model, ctx, level, group) -> [riker_fab, ours_fab, n]
    perq = defaultdict(lambda: [0, 0])                # (ctx, qid) -> [riker_fab, n]
    capture = defaultdict(lambda: [0, 0])             # (ctx, yes_no) -> [copied, fabricated with a look-alike value]
    roig_cells = defaultdict(lambda: [0, 0, 0])       # (platform, temp, model, ctx) -> [wrong, n_all, failed]
    stats = Counter()
    for r in iter_cache(root, levels=TRAP_LEVELS):
        if temps and r["temperature"] not in temps:
            continue
        if platforms and r["platform"] not in platforms:
            continue
        rc = roig_cells[(r["platform"], r["temperature"], r["model"], r["context_k"])]
        rc[0] += not r["riker_correct"]
        rc[1] += 1
        rc[2] += r["failed"]
        stats["answers"] += 1
        if r["failed"]:
            stats["failed"] += 1
            continue
        q = la.get((r["context_k"], r["question_id"]))
        if q is None:
            stats["no look-alike row (unparsed or unknown question)"] += 1
            continue
        g = "present" if q["present"] else "none"
        fab_r = not r["riker_correct"]
        ours_ref = is_refusal(r.get("response") or "") or is_abstain_token(r.get("riker_extracted") or "")
        c = cells[(r["model"], r["context_k"], r["level"], g)]
        c[0] += fab_r
        c[1] += not ours_ref
        c[2] += 1
        p = perq[(r["context_k"], r["question_id"])]
        p[0] += fab_r
        p[1] += 1
        if fab_r and q["values"]:
            yn = q["yes_no"] == "True"
            cap = capture[(r["context_k"], yn)]
            cap[1] += 1
            cap[0] += any(same_answer(r.get("riker_extracted"), v) for v in q["values"])
        stats["used"] += 1
    return cells, perq, capture, roig_cells, stats


def per_model(cells, levels=TRAP_LEVELS, use="riker"):
    """(model, ctx, group) -> (k, n)"""
    idx = 0 if use == "riker" else 1
    out = defaultdict(lambda: [0, 0])
    for (m, k, lv, g), c in cells.items():
        if lv in levels:
            out[(m, k, g)][0] += c[idx]
            out[(m, k, g)][1] += c[2]
    return out


def macro(pm, models, k, g, B=2000, seed=0):
    rates = [pm[(m, k, g)][0] / pm[(m, k, g)][1] for m in models if pm[(m, k, g)][1] > 0]
    if not rates:
        return float("nan"), float("nan"), float("nan"), 0
    mean = sum(rates) / len(rates)
    rng = random.Random(seed)
    boots = sorted(sum(rng.choice(rates) for _ in rates) / len(rates) for _ in range(B))
    return mean, boots[int(0.025 * B)], boots[int(0.975 * B) - 1], len(rates)


def balanced_models(pm, groups=GROUPS):
    models = {m for m, _, _ in pm}
    return sorted(m for m in models if all(any(pm[(m, k, g)][1] for g in groups) for k in CONTEXTS))


# ----------------------------------------------------------------------------- regression

def regression(cells, L):
    """Binomial GLM on counts: made up ~ log2(length/32K) + look-alike present + level + model."""
    try:
        import numpy as np
        import pandas as pd
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except Exception as e:
        L += ["", f"(regression skipped: {e})"]
        return
    rows = [{"model": m, "ctx": k, "level": lv, "present": int(g == "present"), "fab": c[0], "n": c[2]}
            for (m, k, lv, g), c in cells.items() if c[2] > 0]
    df = pd.DataFrame(rows)
    df["log2len"] = np.log2(df["ctx"] / 32.0)
    df["ok"] = df["n"] - df["fab"]
    try:
        fit = smf.glm("fab + ok ~ log2len + present + C(level) + C(model)", data=df,
                      family=sm.families.Binomial()).fit()
    except Exception as e:
        L += ["", f"(regression failed: {e})"]
        return
    b_len, b_pre = fit.params["log2len"], fit.params["present"]
    ci = fit.conf_int()
    L += ["", "## Regression (binomial GLM; each model and question level has its own baseline)", "",
          "| term | log-odds | 95% CI | odds ratio | p |", "|---|---|---|---|---|"]
    for t, lab in (("log2len", "one doubling of length"), ("present", "look-alike present")):
        L.append(f"| {lab} | {fit.params[t]:.3f} | [{ci.loc[t, 0]:.3f}, {ci.loc[t, 1]:.3f}] | "
                 f"{math.exp(fit.params[t]):.2f} | {fit.pvalues[t]:.2g} |")
    if b_len > 0:
        L += ["", f"**Exchange rate (preview):** one look-alike record has the same effect as "
              f"**{b_pre / b_len:.1f} doublings** of length (log-odds ratio {b_pre:.3f} / {b_len:.3f}). "
              "In RIKER2 look-alikes are not placed on purpose, so this is only a first estimate; Exp 3 measures it properly."]
    else:
        L += ["", "Length has no positive effect once look-alikes are accounted for, so the exchange rate is not defined here."]


# ----------------------------------------------------------------------------- Roig's own numbers

def check_against_roig(root: Path, roig_cells, L):
    """Our fabrication per (platform, temperature, model, length) vs Roig's <ctx>k_summary.csv."""
    diffs, diffs_nf = [], []
    for k in CONTEXTS:
        p = root / "raw" / "riker" / f"{k}k_summary.csv"
        if not p.exists():
            continue
        with open(p, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                try:
                    key = (r["platform"], float(r["temperature"]), r["model"], k)
                    roig = float(r["fabrication_pct"])
                except (KeyError, ValueError):
                    continue
                c = roig_cells.get(key)
                if not c or not c[1]:
                    continue
                diffs.append(abs(100 * c[0] / c[1] - roig))
                if c[1] > c[2]:
                    diffs_nf.append(abs(100 * (c[0] - c[2]) / (c[1] - c[2]) - roig))
    L += ["", "## Check: do we read the data the way Roig did?", ""]
    if diffs:
        L += [f"Compared {len(diffs)} (hardware, temperature, model, length) cells with Roig's `<length>k_summary.csv`.",
              f"Mean absolute difference in fabrication %: **{sum(diffs) / len(diffs):.2f} points** counting failed replies "
              f"as wrong; {sum(diffs_nf) / max(1, len(diffs_nf)):.2f} points leaving them out. "
              f"Share of cells within 1 point: {100 * sum(d <= 1 for d in diffs) / len(diffs):.0f}%."]
    else:
        L.append("Roig's summary CSVs were not found or did not match; skipped.")


# ----------------------------------------------------------------------------- figure

def figure(pm_all, pm_l12, models_all, models_l12, out: Path, dpi: int, n_q: dict, note: str):
    import matplotlib.pyplot as plt
    from make_figures import BLUE, FULL_W, GRID, INK2, ORANGE, SURFACE, save
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.55), sharey=True, gridspec_kw={"wspace": 0.12})
    x = list(range(len(CONTEXTS)))
    ymax = 0
    for ax, pm, models, title, nkey in ((axes[0], pm_all, models_all, "(a) All trap questions (L11 + L12)", "all"),
                                        (axes[1], pm_l12, models_l12, "(b) Same question type only (L12)", "L12")):
        for off, g, col, mk, lab in ((-0.06, "present", ORANGE, "s", "look-alike present"),
                                     (0.06, "none", BLUE, "o", "no look-alike")):
            vals = [macro(pm, models, k, g) for k in CONTEXTS]
            ys = [100 * v[0] for v in vals]
            lo = [100 * (v[0] - v[1]) if v[3] else 0 for v in vals]
            hi = [100 * (v[2] - v[0]) if v[3] else 0 for v in vals]
            ok = [i for i, v in enumerate(vals) if v[3]]
            if not ok:
                continue
            ax.errorbar([x[i] + off for i in ok], [ys[i] for i in ok], yerr=[[lo[i] for i in ok], [hi[i] for i in ok]],
                        color=col, marker=mk, ms=5, lw=2, capsize=2.5, elinewidth=1, label=lab, zorder=3,
                        mec=SURFACE, mew=1)
            ymax = max(ymax, max(ys[i] + hi[i] for i in ok))
            for i in ok:
                nq = n_q.get((nkey, CONTEXTS[i], g), 0)
                ax.annotate(f"{nq} q", (x[i] + off, ys[i]), textcoords="offset points",
                            xytext=(9 if off > 0 else -9, -2), ha="left" if off > 0 else "right", fontsize=5.6, color=INK2)
        ax.set_xticks(x, [f"{k}K" for k in CONTEXTS])
        ax.set_xlim(-0.4, len(CONTEXTS) - 0.6)
        ax.set_xlabel("context length")
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left")
        ax.text(0.99, 0.03, f"{len(models)} models", transform=ax.transAxes, ha="right", va="bottom", fontsize=6, color=INK2)
    axes[0].set_ylabel("made-up answers (%)")
    axes[0].set_ylim(0, min(100, max(10, ymax * 1.15)))
    axes[0].legend(loc="upper left", handlelength=1.6)
    fig.text(0.01, 1.01, note, fontsize=6.4, color=INK2)
    save(fig, out, "fig_exp1_riker", dpi)


# ----------------------------------------------------------------------------- main

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="RIKER2 folder (default: paths.yaml data.riker2)")
    ap.add_argument("--temps", nargs="*", type=float, help="only these temperatures (default: all)")
    ap.add_argument("--platforms", nargs="*", help="only these hardware folders (default: all)")
    ap.add_argument("--dpi", type=int, default=900)
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else riker_root()
    la = load_lookalikes(OUT_DIR / "lookalikes.csv")
    print("reading the answers cache ...")
    cells, perq, capture, roig_cells, stats = collect(root, la, set(a.temps) if a.temps else None,
                                                      set(a.platforms) if a.platforms else None)
    if not stats["used"]:
        sys.exit(f"no usable answers ({dict(stats)}). Check download_riker.py and find_lookalikes.py.")
    pm_all = per_model(cells)
    pm_l12 = per_model(cells, levels=("L12",))
    pm_ours = per_model(cells, use="ours")
    models_all = balanced_models(pm_all)
    models_l12 = balanced_models(pm_l12)
    all_models = sorted({m for m, _, _ in pm_all})

    # number of questions behind each point
    n_q = Counter()
    for (k, qid), q in la.items():
        g = "present" if q["present"] else "none"
        n_q[("all", k, g)] += 1
        if q["level"] == "L12":
            n_q[("L12", k, g)] += 1

    temps_note = "all temperatures" if not a.temps else "temperature " + ", ".join(f"{t:g}" for t in a.temps)
    L = ["# Exp 1 (RQ3): Roig's made-up answers split by look-alike presence", "",
         f"RIKER2 released answers, {temps_note}. {stats['used']:,} trap answers used; {stats['failed']:,} failed "
         f"replies left out; {stats['no look-alike row (unparsed or unknown question)']:,} answers to questions we could not read.", "",
         f"{len(all_models)} models; {len(models_all)} have answers at all three lengths and are used for the averages.", "",
         "Made-up rate = mean over models of each model's rate; [95% bootstrap interval over models]; (questions).", ""]
    for title, pm, models, key in (("All trap questions (L11 + L12)", pm_all, models_all, "all"),
                                   ("L12 only (same question type: the record exists, the field does not)", pm_l12, models_l12, "L12"),
                                   ("All trap questions, scored with OUR refusal rules", pm_ours, models_all, "all")):
        L += [f"## {title}", "", "| length | look-alike present | no look-alike | difference |", "|---|---|---|---|"]
        for k in CONTEXTS:
            cell = []
            vals = {}
            for g in GROUPS:
                m_, lo, hi, nm = macro(pm, models, k, g)
                vals[g] = m_
                cell.append("n/a" if not nm else f"{100 * m_:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] ({n_q[(key, k, g)]} q)")
            d = vals["present"] - vals["none"]
            L.append(f"| {k}K | " + " | ".join(cell) + f" | {'n/a' if d != d else f'{100 * d:+.1f} points'} |")
        L.append("")

    # by level and look-alike kind (pooled over models)
    L += ["## By level and kind of the closest look-alike (pooled over models and runs)", "",
          "| length | level | closest look-alike | questions | answers | made up (pooled, Wilson 95%) |", "|---|---|---|---|---|---|"]
    kind_cells = defaultdict(lambda: [0, 0, set()])
    for (k, qid), (f_, n_) in perq.items():
        q = la[(k, qid)]
        kc = kind_cells[(k, q["level"], q["best_kind"] or "none")]
        kc[0] += f_
        kc[1] += n_
        kc[2].add(qid)
    for (k, lv, kind), (f_, n_, qs) in sorted(kind_cells.items()):
        p, lo, hi = wilson(f_, n_)
        L.append(f"| {k}K | {lv} | {kind} | {len(qs)} | {n_:,} | {100 * p:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] |")

    # exposure: do look-alikes grow with length?
    L += ["", "## Do look-alikes grow with length? (the confound Exp 1 is about)", "",
          "| length | trap questions | with a look-alike | mean look-alike records per question |", "|---|---|---|---|"]
    for k in CONTEXTS:
        qs = [q for (kk, _), q in la.items() if kk == k]
        if qs:
            L.append(f"| {k}K | {len(qs)} | {sum(q['present'] for q in qs)} ({100 * sum(q['present'] for q in qs) / len(qs):.0f}%) | "
                     f"{sum(int(q['n_lookalikes']) for q in qs) / len(qs):.2f} |")

    L += ["", "## Did made-up answers copy the look-alike's value? (look-alike capture)", "",
          "| length | question kind | made-up answers with a look-alike value | copied it |", "|---|---|---|---|"]
    for (k, yn), (cp, n_) in sorted(capture.items()):
        L.append(f"| {k}K | {'yes/no' if yn else 'value (amount, date, name, ...)'} | {n_:,} | "
                 f"{100 * cp / n_:.1f}% |" if n_ else f"| {k}K | {yn} | 0 | n/a |")
    L += ["", "For yes/no questions half of all answers match by chance, so only the value questions show capture clearly."]

    regression(cells, L)
    check_against_roig(root, roig_cells, L)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "exp1_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(OUT_DIR / "exp1_per_model.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "context_k", "level", "group", "made_up_riker", "made_up_ours", "n", "rate_riker",
                    "wilson_lo", "wilson_hi", "in_balanced_panel"])
        for (m, k, lv, g), c in sorted(cells.items()):
            p, lo, hi = wilson(c[0], c[2])
            w.writerow([m, k, lv, g, c[0], c[1], c[2], round(p, 4), round(lo, 4), round(hi, 4), m in models_all])
    with open(OUT_DIR / "exp1_per_question.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["context_k", "question_id", "level", "doc_type", "lookalike_present", "best_kind", "n_lookalikes",
                    "answers", "made_up", "rate"])
        for (k, qid), (f_, n_) in sorted(perq.items()):
            q = la[(k, qid)]
            w.writerow([k, qid, q["level"], q["doc_type"], q["present"], q["best_kind"], q["n_lookalikes"], n_, f_,
                        round(f_ / n_, 4) if n_ else ""])
    note = (f"RIKER2 (Roig, 2026) released answers, {temps_note}. Mean over models; bars: 95% bootstrap interval "
            "over models; labels: trap questions per point.")
    figure(pm_all, pm_l12, models_all, models_l12, OUT_DIR, a.dpi, n_q, note)
    print("\n".join(L))
    print(f"\nsaved to {OUT_DIR}: fig_exp1_riker.png/.pdf, exp1_results.md, exp1_per_model.csv, exp1_per_question.csv")


if __name__ == "__main__":
    main()
