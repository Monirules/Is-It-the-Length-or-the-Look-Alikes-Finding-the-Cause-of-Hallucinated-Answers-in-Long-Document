"""analysis/main_results.py  (owner: Monirul)

Main results for the paper from the official scores of every model: Exp 2 (look-alike ladder),
Exp 3 (length with and without a strong look-alike), Exp 4 (copies), sibling filler, temperature
stability, and a logistic regression that gives the exchange rate (doublings of length that equal one
strong look-alike).

Input   the per-run folders written by score/score_all.py, each with a scored.csv:
            <results>/<exp>_<model>_normal_t<T>_s<seed>/scored.csv
        (on the cluster: outputs/results; on the PC after copying: outputs/results_cluster)
Output  outputs/figures_main/   fig8_exp2_ladder, fig9_exp3_length, fig10_exp4_copies, fig11_filler
                                (900 dpi .png + .pdf), main_results.md (all numbers), main_results.csv

Usage (any machine, no GPU; seconds)
  python -m analysis.main_results --results outputs/results_cluster
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

MODELS = ["qwen3_4b", "llama31_8b", "gemma3_27b", "qwen3_30b_a3b", "llama33_70b", "qwen3_next_80b", "glm45_air"]
NAMES = {"qwen3_4b": "Qwen3 4B", "llama31_8b": "Llama 3.1 8B", "gemma3_27b": "Gemma 3 27B",
         "qwen3_30b_a3b": "Qwen3 30B-A3B", "llama33_70b": "Llama 3.3 70B", "qwen3_next_80b": "Qwen3-Next 80B",
         "glm45_air": "GLM-4.5-Air"}
# reference categorical palette, slots 1-7 in fixed order (validated: scripts/validate_palette.js, light mode)
COLORS = dict(zip(MODELS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"]))
MARKERS = dict(zip(MODELS, ["o", "s", "^", "D", "v", "P", "X"]))
LEVELS = ["none", "weak", "medium", "strong"]
LENGTHS = [8, 32, 64, 128]
COPIES = [1, 2, 4, 8]


# ----------------------------------------------------------------------------- data

def load(results: Path) -> list[dict]:
    rows = []
    for f in sorted(results.glob("*/scored.csv")):
        name = f.parent.name
        exp = name.split("_")[0]
        rest = name[len(exp) + 1:]
        if "_normal_" not in rest:
            continue
        model, run = rest.split("_normal_")
        if model not in MODELS:
            continue
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                r.update(exp=exp, model=model, run=run, answerable=r["answerable"] == "True",
                         made_up=r["label"] == "made_up", captured=r.get("captured") == "True",
                         length=int(r["length_k"]), copies_n=int(r["copies"] or 0))
                rows.append(r)
    return rows


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)


def rate(rs):
    rs = [r for r in rs if not r["answerable"]]
    return wilson(sum(r["made_up"] for r in rs), len(rs)) + (len(rs),)


def pct(rs):
    p, lo, hi, n = rate(rs)
    return "-" if n == 0 else f"{100 * p:.1f} [{100 * lo:.0f}-{100 * hi:.0f}]"


# ----------------------------------------------------------------------------- logistic regression (IRLS)

def logit(X, y, w=None, iters=50):
    """Weighted logistic regression by IRLS. Returns (coef, standard errors)."""
    import numpy as np
    X, y = np.asarray(X, float), np.asarray(y, float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    b = np.zeros(X.shape[1])
    ridge = 1e-6 * np.eye(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ b, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        W = w * p * (1 - p)
        H = X.T @ (X * W[:, None]) + ridge
        g = X.T @ (w * (y - p))
        step = np.linalg.solve(H, g)
        b += step
        if np.abs(step).max() < 1e-8:
            break
    eta = np.clip(X @ b, -30, 30)
    p = 1 / (1 + np.exp(-eta))
    H = X.T @ (X * (w * p * (1 - p))[:, None]) + ridge
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    return b, se


def exchange_rate(rows, models, exclude=lambda r: False):
    """Exp 3, questions with no answer: made_up ~ log2(length/8) + strong + model + ladder.
    Exchange rate = coef(strong) / coef(log2 length): doublings of length worth one strong look-alike."""
    import numpy as np
    rs = [r for r in rows if r["exp"] == "exp3" and not r["answerable"] and r["model"] in models and not exclude(r)]
    if not rs:
        return None
    ms = [m for m in models if any(r["model"] == m for r in rs)]
    X, y = [], []
    for r in rs:
        x = [1.0, math.log2(r["length"] / 8), 1.0 if r["level"] == "strong" else 0.0,
             1.0 if r["ladder"] == "role" else 0.0, 1.0 if r["filler"] == "sibling" else 0.0]
        x += [1.0 if r["model"] == m else 0.0 for m in ms[1:]]
        X.append(x)
        y.append(1.0 if r["made_up"] else 0.0)
    b, se = logit(X, y)
    out = {"n": len(y), "b_len": b[1], "se_len": se[1], "b_strong": b[2], "se_strong": se[2],
           "b_role": b[3], "b_sibling": b[4], "se_sibling": se[4]}
    # interaction model: length can matter differently with and without a look-alike
    Xi = [x[:5] + [x[1] * x[2]] + x[5:] for x in X]
    bi, sei = logit(Xi, y)
    out.update(b_len_none=bi[1], se_len_none=sei[1], b_strong_8k=bi[2], se_strong_8k=sei[2],
               b_len_strong=bi[1] + bi[5], b_inter=bi[5], se_inter=sei[5])
    # exchange rate: how many doublings of length (with no look-alike) add as much log-odds as one strong
    # look-alike adds at 8K. Defined only when length has a clearly positive effect (lower 95% bound > 0).
    out["exchange"] = (bi[2] / bi[1]) if bi[1] - 1.96 * sei[1] > 0 else float("nan")
    return out


# ----------------------------------------------------------------------------- figures

def _style():
    import matplotlib
    matplotlib.use("Agg")
    import make_figures  # noqa: F401  (sets rcParams)
    from make_figures import FULL_W, GRID, INK2, SURFACE, save
    return FULL_W, GRID, INK2, SURFACE, save


def _line(ax, xs, rs_by_x, m, SURFACE, off=0.0):
    pts = [(x, rate(rs_by_x[x])) for x in xs]
    pts = [(x, v) for x, v in pts if v[3] > 0]
    if not pts:
        return
    xi = [xs.index(x) + off for x, _ in pts]
    ys = [100 * v[0] for _, v in pts]
    lo = [100 * (v[0] - v[1]) for _, v in pts]
    hi = [100 * (v[2] - v[0]) for _, v in pts]
    ax.errorbar(xi, ys, yerr=[lo, hi], color=COLORS[m], marker=MARKERS[m], ms=4.5, lw=1.6, capsize=1.8,
                elinewidth=0.8, mec=SURFACE, mew=0.8, label=NAMES[m], zorder=3)


def fig_exp2(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.6), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, lad in zip(axes, ["name", "role"]):
        for i, m in enumerate(models):
            by = {lv: [r for r in rows if r["exp"] == "exp2" and r["run"] == "t0_s0" and r["model"] == m
                       and r["ladder"] == lad and r["level"] == lv] for lv in LEVELS}
            _line(ax, LEVELS, by, m, SURFACE, off=(i - (len(models) - 1) / 2) * 0.04)
        ax.set_xticks(range(4), LEVELS)
        ax.set_xlabel("look-alike level (length fixed at 32K)")
        ax.set_title(f"({'a' if lad == 'name' else 'b'}) {lad} ladder", loc="left")
        ax.set_ylim(0, 100)
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("made-up answers (%)")
    axes[1].legend(loc="upper left", fontsize=6.4, handlelength=1.6, ncol=1)
    fig.text(0.01, 1.0, "Exp 2: questions with no answer; 120 documents (960 no-answer questions) per model; "
             "bars: 95% Wilson interval; T = 0", fontsize=6.4, color=INK2)
    save(fig, out, "fig8_exp2_ladder", dpi)


def fig_exp3(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.6), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, lv, title in zip(axes, ["none", "strong"], ["(a) no look-alike", "(b) one strong look-alike"]):
        for i, m in enumerate(models):
            by = {L: [r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["level"] == lv
                      and r["length"] == L] for L in LENGTHS}
            _line(ax, LENGTHS, by, m, SURFACE, off=(i - (len(models) - 1) / 2) * 0.04)
        ax.set_xticks(range(4), [f"{L}K" for L in LENGTHS])
        ax.set_xlabel("document length (tokens)")
        ax.set_title(title, loc="left")
        ax.set_ylim(0, 100)
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("made-up answers (%)")
    axes[1].legend(loc="lower left", fontsize=6.2, handlelength=1.6, ncol=2)
    if "llama33_70b" in models:
        axes[0].annotate("Llama 3.3 70B at 128K:\nanswer accuracy also\ncollapses (see text)",
                         xy=(2.95, 74), xytext=(0.9, 60), fontsize=6, color=INK2,
                         arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.6})
    fig.text(0.01, 1.0, "Exp 3: fillers pooled; 640 no-answer questions per point; Gemma 3 27B and GLM-4.5-Air "
             "cannot read 128K", fontsize=6.4, color=INK2)
    save(fig, out, "fig9_exp3_length", dpi)


def fig_exp4(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    fig, ax = plt.subplots(figsize=(FULL_W * 0.55, 2.5))
    for i, m in enumerate(models):
        by = {c: [r for r in rows if r["exp"] == "exp4" and r["model"] == m and r["copies_n"] == c] for c in COPIES}
        _line(ax, COPIES, by, m, SURFACE, off=(i - (len(models) - 1) / 2) * 0.04)
    ax.set_xticks(range(4), [str(c) for c in COPIES])
    ax.set_xlabel("copies of the strong look-alike (32K)")
    ax.set_ylabel("made-up answers (%)")
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=6, handlelength=1.4, ncol=2)
    ax.set_title("Exp 4: more copies of the same look-alike", loc="left")
    save(fig, out, "fig10_exp4_copies", dpi)


def fig_filler(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    from make_figures import BLUE, ORANGE
    fig, ax = plt.subplots(figsize=(FULL_W * 0.6, 2.4))
    x = list(range(len(models)))
    for off, fil, col, lab in ((-0.19, "unrelated", ORANGE, "unrelated filler"), (0.19, "sibling", BLUE, "sibling filler")):
        vals, lo, hi = [], [], []
        for m in models:
            p, l_, h_, n = rate([r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["level"] == "strong"
                                 and r["filler"] == fil])
            vals.append(100 * p), lo.append(100 * (p - l_)), hi.append(100 * (h_ - p))
        ax.bar([i + off for i in x], vals, width=0.36, color=col, edgecolor=SURFACE, linewidth=1, label=lab, zorder=2)
        ax.errorbar([i + off for i in x], vals, yerr=[lo, hi], fmt="none", ecolor=INK2, elinewidth=0.7, capsize=1.5, zorder=3)
    ax.set_xticks(x, [NAMES[m].replace(" ", "\n", 1) for m in models], fontsize=6.4)
    ax.set_ylabel("made-up answers (%)")
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.4, ncol=2)
    ax.set_title("Strong look-alike: filler type (Exp 3, all lengths)", loc="left", pad=16)
    save(fig, out, "fig11_filler", dpi)


# ----------------------------------------------------------------------------- report

def report(rows, models, out):
    L = ["# Main results (official scoring)", "",
         f"Models with results: {', '.join(NAMES[m] for m in models)}.", "",
         "Made-up rate = share of questions with no answer where the model gave a value; 95% Wilson interval in brackets.", "",
         "## Exp 2: look-alike ladder at 32K (T = 0)", "",
         "| model | none | weak | medium | strong | copied look-alike | correct (with answer) |", "|---|---|---|---|---|---|---|"]
    table = []
    for m in models:
        e2 = [r for r in rows if r["exp"] == "exp2" and r["model"] == m and r["run"] == "t0_s0"]
        mu = [r for r in e2 if r["made_up"]]
        an = [r for r in e2 if r["answerable"]]
        cells = [pct([r for r in e2 if r["level"] == lv]) for lv in LEVELS]
        cap = f"{100 * sum(r['captured'] for r in mu) / len(mu):.0f}%" if mu else "-"
        acc = f"{100 * sum(r['label'] == 'correct' for r in an) / len(an):.1f}%" if an else "-"
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + f" | {cap} | {acc} |")
        for lv in LEVELS:
            p, lo, hi, n = rate([r for r in e2 if r["level"] == lv])
            table.append({"exp": "exp2", "model": m, "condition": lv, "made_up": round(p, 4), "lo": round(lo, 4),
                          "hi": round(hi, 4), "n": n})
    L += ["", "## Exp 2 stability: strong look-alike at T = 0.7, three seeds", "",
          "| model | T=0 | seed 1 | seed 2 | seed 3 |", "|---|---|---|---|---|"]
    for m in models:
        cells = [pct([r for r in rows if r["exp"] == "exp2" and r["model"] == m and r["run"] == run and r["level"] == "strong"])
                 for run in ("t0_s0", "t0.7_s1", "t0.7_s2", "t0.7_s3")]
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
    L += ["", "## Exp 3: length, with and without a strong look-alike (fillers pooled)", "",
          "| model | " + " | ".join(f"none {x}K" for x in LENGTHS) + " | " + " | ".join(f"strong {x}K" for x in LENGTHS) + " |",
          "|---|" + "---|" * 8]
    for m in models:
        e3 = [r for r in rows if r["exp"] == "exp3" and r["model"] == m]
        cells = [pct([r for r in e3 if r["level"] == lv and r["length"] == Lk]) for lv in ("none", "strong") for Lk in LENGTHS]
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
        for lv in ("none", "strong"):
            for Lk in LENGTHS:
                p, lo, hi, n = rate([r for r in e3 if r["level"] == lv and r["length"] == Lk])
                if n:
                    table.append({"exp": "exp3", "model": m, "condition": f"{lv}_{Lk}k", "made_up": round(p, 4),
                                  "lo": round(lo, 4), "hi": round(hi, 4), "n": n})
    L += ["", "Answer accuracy on questions WITH an answer, Exp 3 (checks that a model can still read at that length):", "",
          "| model | " + " | ".join(f"{x}K" for x in LENGTHS) + " |", "|---|" + "---|" * 4]
    for m in models:
        cells = []
        for Lk in LENGTHS:
            an = [r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["length"] == Lk and r["answerable"]]
            cells.append(f"{100 * sum(r['label'] == 'correct' for r in an) / len(an):.1f}%" if an else "-")
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
    L += ["", "## Exp 3: filler type with a strong look-alike (all lengths)", "",
          "| model | unrelated filler | sibling filler |", "|---|---|---|"]
    for m in models:
        e3 = [r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["level"] == "strong"]
        L.append(f"| {NAMES[m]} | {pct([r for r in e3 if r['filler'] == 'unrelated'])} | {pct([r for r in e3 if r['filler'] == 'sibling'])} |")
    L += ["", "## Exp 4: copies of the same strong look-alike (32K)", "",
          "| model | " + " | ".join(f"{c} cop{'y' if c == 1 else 'ies'}" for c in COPIES) + " |", "|---|" + "---|" * 4]
    for m in models:
        e4 = [r for r in rows if r["exp"] == "exp4" and r["model"] == m]
        L.append(f"| {NAMES[m]} | " + " | ".join(pct([r for r in e4 if r["copies_n"] == c]) for c in COPIES) + " |")

    try:
        reg = exchange_rate(rows, models)
        reg_x = exchange_rate(rows, models, exclude=lambda r: r["model"] == "llama33_70b" and r["length"] == 128)
    except Exception as e:                  # numpy missing
        reg = reg_x = None
        L += ["", f"(regression skipped: {e})"]
    for title, rg in (("all Exp 3 answers", reg), ("without Llama 3.3 70B at 128K (its reading collapses there)", reg_x)):
        if not rg:
            continue
        L += ["", f"## Logistic regression, Exp 3 ({title}), {rg['n']:,} no-answer questions", "",
              "made_up ~ log2(length / 8K) + strong look-alike + ladder + filler + model", "",
              "| term | log-odds | SE | odds ratio |", "|---|---|---|---|",
              f"| one doubling of length | {rg['b_len']:.3f} | {rg['se_len']:.3f} | {math.exp(rg['b_len']):.2f} |",
              f"| strong look-alike | {rg['b_strong']:.3f} | {rg['se_strong']:.3f} | {math.exp(rg['b_strong']):.1f} |",
              f"| sibling filler | {rg['b_sibling']:.3f} | {rg['se_sibling']:.3f} | {math.exp(rg['b_sibling']):.2f} |", "",
              (f"**Exchange rate:** one strong look-alike adds as much as **{rg['exchange']:.1f} doublings of length** "
               f"(log-odds {rg['b_strong_8k']:.2f} for the look-alike at 8K / {rg['b_len_none']:.2f} per doubling without a "
               f"look-alike); i.e. a document {2 ** rg['exchange']:,.0f}x longer." if math.isfinite(rg["exchange"]) else
               "**Exchange rate:** not defined, because length has no clearly positive effect."),
              f"With an interaction term: one doubling raises the log-odds by {rg['b_len_none']:.3f} (SE {rg['se_len_none']:.3f}) "
              f"without a look-alike and by {rg['b_len_strong']:.3f} with a strong one."]
    (out / "main_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(out / "main_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)
    print("\n".join(L))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(PROJECT_ROOT / "outputs" / "results"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "figures_main"))
    ap.add_argument("--dpi", type=int, default=900)
    a = ap.parse_args(argv)
    rows = load(Path(a.results))
    if not rows:
        sys.exit(f"no scored.csv files under {a.results}")
    models = [m for m in MODELS if any(r["model"] == m for r in rows)]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(rows):,} scored answers from {len(models)} models\n")
    report(rows, models, out)
    fig_exp2(rows, models, out, a.dpi)
    fig_exp3(rows, models, out, a.dpi)
    fig_exp4(rows, models, out, a.dpi)
    fig_filler(rows, models, out, a.dpi)
    print(f"\nsaved to {out}")


if __name__ == "__main__":
    main()
