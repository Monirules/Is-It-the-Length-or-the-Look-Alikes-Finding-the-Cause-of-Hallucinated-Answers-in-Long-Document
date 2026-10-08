"""analysis/readme_figures.py

Figures for the repository README, computed from the released scored files. Experiment numbers follow
the paper (code folder names in brackets):

  Exp 1 [exp2]  look-alike level at 32K          -> docs/figures/exp1_ladder.png
  Exp 2 [exp3]  length x {none, strong} x filler -> docs/figures/exp2_length.png, exp2_sibling.png
  Exp 3 [exp4]  1, 2, 4, 8 copies at 32K         -> docs/figures/exp3_copies.png
  Exp 4 [exp6]  real Wikipedia text              -> docs/figures/exp4_wikipedia.png
  Table 2                                         -> docs/figures/headline.png

Usage (any machine, no GPU, a few seconds)
  python -m analysis.readme_figures --results outputs/results_cluster --out docs/figures
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from analysis.main_results import (COLORS, LENGTHS, LEVELS, MARKERS, MODELS, accuracy, load,  # noqa: E402
                                   rate)

NAMES = {"qwen3_4b": "Qwen3 4B", "llama31_8b": "Llama 3.1 8B", "gemma3_27b": "Gemma 3 27B",
         "qwen3_30b_a3b": "Qwen3 30B A3B", "llama33_70b": "Llama 3.3 70B", "qwen3_next_80b": "Qwen3 Next 80B",
         "glm45_air": "GLM 4.5 Air 106B"}
SHORT = {"qwen3_4b": "Qwen3\n4B", "llama31_8b": "Llama 3.1\n8B", "gemma3_27b": "Gemma 3\n27B",
         "qwen3_30b_a3b": "Qwen3\n30B A3B", "llama33_70b": "Llama 3.3\n70B", "qwen3_next_80b": "Qwen3 Next\n80B",
         "glm45_air": "GLM 4.5\nAir"}
INK, INK2, GRID = "#1f2328", "#59636e", "#e5e7eb"
NONE_C, STRONG_C = "#9aa4b2", "#c2410c"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5, "axes.titlesize": 10.5, "axes.titleweight": "bold",
    "axes.labelsize": 9.5, "axes.edgecolor": "#c9ced6", "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
})


def pct(v):
    return 100 * v[0]


def err(v):
    return [[100 * (v[0] - v[1])], [100 * (v[2] - v[0])]]


def save(fig, out: Path, name: str):
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=220, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print("saved", out / f"{name}.png")


def sel(rows, **kw):
    return [r for r in rows if all(r[k] == v for k, v in kw.items())]


# --------------------------------------------------------------------------- headline (Table 2)

def fig_headline(rows, out):
    data = []
    for m in MODELS:
        strong = rate(sel(rows, exp="exp2", run="t0_s0", model=m, level="strong"))
        e3 = sel(rows, exp="exp3", model=m, level="none")
        longest = max(L for L in LENGTHS if any(r["length"] == L for r in e3))
        none = rate([r for r in e3 if r["length"] == longest])
        data.append((m, strong, none, longest))
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    ys = list(range(len(data)))[::-1]
    for y, (m, s, n, L) in zip(ys, data):
        ax.plot([pct(n), pct(s)], [y, y], color="#d0d5dc", lw=5, solid_capstyle="round", zorder=1)
        ax.scatter(pct(n), y, s=70, color=NONE_C, zorder=3, edgecolor="white", lw=1)
        ax.scatter(pct(s), y, s=70, color=STRONG_C, zorder=3, edgecolor="white", lw=1)
        ax.text(pct(s) + 2.2, y, f"+{round(pct(s), 1) - round(pct(n), 1):.1f}", va="center", fontsize=8.5, color=INK, weight="bold")
        ax.text(pct(n) - 2.2, y, f"{L}K", va="center", ha="right", fontsize=7.5, color=INK2)
    ax.set_yticks(ys, [NAMES[d[0]] for d in data])
    ax.set_xlim(-12, 108)
    ax.set_xlabel("made-up answers on unanswerable questions (%)")
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.scatter([], [], s=60, color=NONE_C, label="no look-alike, longest length tested")
    ax.scatter([], [], s=60, color=STRONG_C, label="one strong look-alike, 32K")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, 1.16), ncol=2, fontsize=8.5, handletextpad=0.3)
    save(fig, out, "headline")


# --------------------------------------------------------------------------- Exp 1 [exp2]

def fig_exp1(rows, out):
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.4), sharey=True)
    for ax, ladder, title in zip(axes, ["name", "role"], ["(a) Name ladder", "(b) Role ladder"]):
        for i, m in enumerate(MODELS):
            off = (i - 3) * 0.045
            vs = [rate(sel(rows, exp="exp2", run="t0_s0", model=m, ladder=ladder, level=lv)) for lv in LEVELS]
            xs = [j + off for j in range(4)]
            ax.errorbar(xs, [pct(v) for v in vs], yerr=[[100 * (v[0] - v[1]) for v in vs],
                                                        [100 * (v[2] - v[0]) for v in vs]],
                        color=COLORS[m], marker=MARKERS[m], ms=4.5, lw=1.6, capsize=1.6, elinewidth=0.7,
                        mec="white", mew=0.6, label=NAMES[m])
        ax.set_xticks(range(4), LEVELS)
        ax.set_title(title, loc="left")
        ax.set_xlabel("look-alike level (length fixed at 32K)")
        ax.set_ylim(-3, 103)
    axes[0].set_ylabel("made-up answers (%)")
    axes[0].legend(loc="upper left", fontsize=7.8, handlelength=1.6)
    fig.tight_layout()
    save(fig, out, "exp1_ladder")


# --------------------------------------------------------------------------- Exp 2 [exp3]

def fig_exp2(rows, out):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    titles = ["(a) No look-alike", "(b) One strong look-alike", "(c) Accuracy, answerable questions"]
    for ax, title in zip(axes, titles):
        ax.set_title(title, loc="left")
        ax.set_xticks(range(4), [f"{L}K" for L in LENGTHS])
        ax.set_xlabel("document length (tokens)")
    for m in MODELS:
        e3 = sel(rows, exp="exp3", model=m)
        Ls = [L for L in LENGTHS if any(r["length"] == L for r in e3)]
        xs = [LENGTHS.index(L) for L in Ls]
        kw = dict(color=COLORS[m], marker=MARKERS[m], ms=4.5, lw=1.6, mec="white", mew=0.6, label=NAMES[m])
        for ax, lv in zip(axes[:2], ["none", "strong"]):
            ax.plot(xs, [pct(rate([r for r in e3 if r["level"] == lv and r["length"] == L])) for L in Ls], **kw)
        axes[2].plot(xs, [pct(accuracy([r for r in e3 if r["length"] == L])) for L in Ls], **kw)
    axes[0].set_ylabel("made-up answers (%)")
    axes[0].set_ylim(-3, 103)
    axes[1].set_ylim(-3, 103)
    axes[2].set_ylim(38, 102)
    axes[2].set_ylabel("correct (%)")
    axes[0].annotate("Llama 3.3 70B at 128K\n(accuracy also falls, panel c)", xy=(3, 74.4), xytext=(0.15, 55),
                     fontsize=7.8, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    h, l = axes[2].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=7, fontsize=8, bbox_to_anchor=(0.5, -0.07), handlelength=1.6)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, out, "exp2_length")


def fig_sibling(rows, out):
    fig, ax = plt.subplots(figsize=(5.0, 3.9))
    pts = []
    for m in MODELS:
        e3 = sel(rows, exp="exp3", model=m)
        gain = pct(rate([r for r in e3 if r["level"] == "strong" and r["filler"] == "unrelated"])) - \
            pct(rate([r for r in e3 if r["level"] == "strong" and r["filler"] == "sibling"]))
        cost = pct(accuracy([r for r in e3 if r["filler"] == "unrelated"])) - \
            pct(accuracy([r for r in e3 if r["filler"] == "sibling"]))
        pts.append((m, cost, gain))
        print(f"  sibling filler, {NAMES[m]}: gain {gain:.1f}, cost {cost:.1f} points")
    lim = max(max(c, g) for _, c, g in pts) + 4
    ax.fill_between([0, lim], [0, lim], lim, color="#e7f5ec", zorder=0)
    ax.fill_between([0, lim], 0, [0, lim], color="#fdecec", zorder=0)
    ax.plot([0, lim], [0, lim], ls="--", color=INK2, lw=0.9)
    for m, c, g in pts:
        ax.scatter(c, g, s=60, color=COLORS[m], marker=MARKERS[m], edgecolor="white", lw=0.8, zorder=3)
        ax.annotate(NAMES[m], (c, g), xytext=(5, 4), textcoords="offset points", fontsize=7.6, color=INK)
    ax.text(0.8, lim - 2, "gain larger than cost", fontsize=8, color="#1a7f37", va="top")
    ax.text(lim - 0.8, 1.2, "cost larger than gain", fontsize=8, color="#b42318", ha="right")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.grid(axis="both", color=GRID)
    ax.set_xlabel("answer accuracy lost (points)")
    ax.set_ylabel("made-up answers removed (points)")
    save(fig, out, "exp2_sibling")


# --------------------------------------------------------------------------- Exp 3 [exp4]

def fig_exp3(rows, out):
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for i, m in enumerate(MODELS):
        e4 = sel(rows, exp="exp4", model=m)
        ax.plot(range(4), [pct(rate([r for r in e4 if r["copies_n"] == c])) for c in [1, 2, 4, 8]],
                color=COLORS[m], marker=MARKERS[m], ms=4.5, lw=1.6, mec="white", mew=0.6, label=NAMES[m])
    ax.set_xticks(range(4), ["1", "2", "4", "8"])
    ax.set_xlabel("copies of the same strong look-alike (32K)")
    ax.set_ylabel("made-up answers (%)")
    ax.set_ylim(35, 102)
    ax.legend(fontsize=7.4, ncol=2, loc="lower left", handlelength=1.5)
    save(fig, out, "exp3_copies")


# --------------------------------------------------------------------------- Exp 4 [exp6]

def fig_exp4(rows, out):
    import numpy as np
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.2), sharey=True)
    x = np.arange(len(MODELS))
    for ax, L in zip(axes, [8, 32]):
        sim = [pct(rate(sel(rows, exp="exp6", model=m, level="lookalike", length=L))) for m in MODELS]
        rnd = [pct(rate(sel(rows, exp="exp6", model=m, level="random", length=L))) for m in MODELS]
        ax.bar(x - 0.2, sim, 0.38, color=STRONG_C, label="similar (BM25) passages")
        ax.bar(x + 0.2, rnd, 0.38, color=NONE_C, label="random passages")
        for xi, v in zip(x, rnd):
            ax.text(xi + 0.2, v + 1.2, f"{v:.0f}", ha="center", fontsize=6.8, color=INK2)
        ax.set_xticks(x, [SHORT[m] for m in MODELS], fontsize=7.3)
        ax.set_title(f"({'ab'[[8, 32].index(L)]}) {L}K tokens", loc="left")
    axes[0].set_ylabel("made-up answers (%)")
    axes[0].set_ylim(0, 100)
    axes[0].legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    save(fig, out, "exp4_wikipedia")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(PROJECT_ROOT / "outputs" / "results_cluster"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "docs" / "figures"))
    a = ap.parse_args(argv)
    rows = [r for r in load(Path(a.results)) if r["prompt"] == "normal"]
    rows = [r for r in rows if not (r["exp"] == "exp3" and r["model"] == "llama33_70b" and "bf16" in r["run"])]
    out = Path(a.out)
    fig_headline(rows, out)
    fig_exp1(rows, out)
    fig_exp2(rows, out)
    fig_sibling(rows, out)
    fig_exp3(rows, out)
    fig_exp4(rows, out)


if __name__ == "__main__":
    main()
