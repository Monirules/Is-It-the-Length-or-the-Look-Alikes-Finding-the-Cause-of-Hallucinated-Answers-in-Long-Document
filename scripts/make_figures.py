"""scripts/make_figures.py

Figures that can be made before any model runs, from the generator and the built dataset.

  fig1_pipeline         how a NullScale document is made and proven
  fig2_ladders          the two look-alike ladders, with real generated examples
  fig3_dataset_checks   (a) length error of every document, (b) where look-alikes sit
  fig4_composition      (a) questions per experiment, (b) unanswerable questions by fact type

Each figure is saved as PDF (vector, for the paper) and PNG (for slides) in outputs/figures/.
Figures 3 and 4 read the dataset, so run build_dataset.py first.

Run (Ubuntu, nullscale env, project folder):
  python scripts/make_figures.py                 # all four, PNG at 900 dpi
  python scripts/make_figures.py --dpi 300       # smaller PNGs
  python scripts/make_figures.py --only 2        # just one figure
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nullscale.config import load_paths  # noqa: E402
from nullscale.lookalike import LEVELS, make_case  # noqa: E402
from nullscale.records import World, edit_distance  # noqa: E402

# ----------------------------------------------------------------------------- style
# Reference palette (dataviz skill): categorical slots 1-3 validate all-pairs; blue ramp for order.
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE, PANEL = "#e1e0d9", "#c3c2b7", "#ffffff", "#f4f3f0"
BLUE, ORANGE = "#2a78d6", "#eb6834"
GOOD, CRITICAL = "#0ca30c", "#d03b3b"                   # status colors, always with a text label
RAMP = {"none": "#c3c2b7", "weak": "#86b6ef", "medium": "#3987e5", "strong": "#184f95"}   # ordinal blue
FULL_W = 6.75                                           # ACL two-column width, inches

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9, "axes.titleweight": "bold",
    "axes.labelsize": 8, "axes.labelcolor": INK2, "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": False, "legend.frameon": False, "legend.fontsize": 7.5, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "pdf.fonttype": 42, "ps.fonttype": 42,
})


def save(fig, out: Path, name: str, dpi: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(out / f"{name}.png", dpi=dpi, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print(f"  saved {name}.pdf and {name}.png ({dpi} dpi)")


# ----------------------------------------------------------------------------- figure 1

def fig1_pipeline(out: Path, dpi: int, counts: dict | None) -> None:
    fig, ax = plt.subplots(figsize=(FULL_W, 2.55))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.axis("off")
    w, h = 21.5, 12.5
    xs = [1, 26, 51, 76.5]
    y_top, y_bot = 25, 3
    n_docs = f"{counts['docs']:,} documents,\n{counts['questions']:,} questions" if counts else "documents +\nquestions.jsonl"
    top = [("schema.py", "business world +\nunrelated records"),
           ("records.py", "invented names,\n≥3 edits apart"),
           ("render.py", "3–4 templates\nper record type"),
           ("questions.py\n+ lookalike.py", "12 questions per doc\n+ their look-alikes")]
    bottom = [("build_dataset.py", n_docs),
              ("absence_check.py", "proof for every\nquestion"),
              ("assemble.py", "exact length (±0.1%),\nlook-alikes at 35–65%"),
              ("filler.py", "unrelated or sibling,\nsame record count")]

    def box(x, y, title, body, edge=AXIS, lw=0.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                                    fc=PANEL, ec=edge, lw=lw))
        ax.text(x + w / 2, y + h - 1.4, title, ha="center", va="top", fontsize=7.6, fontweight="bold",
                color=INK, family="DejaVu Sans Mono", linespacing=1.0)
        ax.text(x + w / 2, y + 1.3, body, ha="center", va="bottom", fontsize=6.8, color=INK2, linespacing=1.15)

    def arrow(p, q, color=INK2, style="-|>", rad=0.0, lw=0.9):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=8, color=color, lw=lw,
                                     connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1))

    for x, (t, b) in zip(xs, top):
        box(x, y_top, t, b)
    for x, (t, b) in zip(xs, bottom):
        box(x, y_bot, t, b, edge=BLUE if t == "absence_check.py" else AXIS, lw=1.3 if t == "absence_check.py" else 0.8)
    for i in range(3):
        arrow((xs[i] + w + 0.6, y_top + h / 2), (xs[i + 1] - 0.6, y_top + h / 2))
    arrow((xs[3] + w / 2, y_top - 0.6), (xs[3] + w / 2, y_bot + h + 0.6))          # down the right side
    arrow((xs[3] - 0.6, y_bot + h / 2), (xs[2] + w + 0.6, y_bot + h / 2))          # filler -> assemble
    arrow((xs[2] - 0.6, y_bot + h / 2), (xs[1] + w + 0.6, y_bot + h / 2))          # assemble -> check
    arrow((xs[1] - 0.6, y_bot + h / 2 - 2.2), (xs[0] + w + 0.6, y_bot + h / 2 - 2.2), color=GOOD)
    ax.text((xs[0] + w + xs[1]) / 2, y_bot + h / 2 - 3.6, "pass", ha="center", va="top", fontsize=6.6, color=INK2)
    arrow((xs[1] + w * 0.72, y_bot + h + 0.8), (xs[2] + w * 0.28, y_bot + h + 0.8), color=CRITICAL, rad=-0.45)
    ax.text((xs[1] + xs[2] + w) / 2, y_bot + h + 5.4, "fail → rebuild with a new seed",
            ha="center", va="bottom", fontsize=6.6, color=INK2)
    save(fig, out, "fig1_pipeline", dpi)


# ----------------------------------------------------------------------------- figure 2

def _letter_diff(w: str, ref: str):
    """Letter-level segments of w against ref (handles one insertion/deletion)."""
    import difflib
    segs = []
    for op, i1, i2, _, _ in difflib.SequenceMatcher(a=w, b=ref, autojunk=False).get_opcodes():
        segs.append((w[i1:i2], INK if op == "equal" else ORANGE))
    return segs


def _name_segments(asked: str, la: str):
    segs = []
    aw = asked.split()
    for i, w in enumerate(la.split()):
        ref = aw[i] if i < len(aw) else ""
        if i:
            segs.append((" ", INK))
        if w == ref:
            segs.append((w, INK))
        elif ref and edit_distance(w, ref) <= 2:
            segs += _letter_diff(w, ref)
        else:
            segs.append((w, ORANGE))
    return segs


def _draw_segments(ax, fig, x, y, segs, size=7.4, weight="normal"):
    r = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    for s, c in segs:
        if not s:
            continue
        t = ax.text(x, y, s, color=c, fontsize=size, va="center", ha="left",
                    fontweight="bold" if c == ORANGE else weight)
        bb = t.get_window_extent(renderer=r)
        x = inv.transform((bb.x1, bb.y0))[0]
    return x


def fig2_ladders(out: Path, dpi: int, seed: int = 20) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.55), gridspec_kw={"wspace": 0.04})
    rows = {}
    for ladder in ("name", "role"):
        rows[ladder] = [make_case(World(seed=seed), ladder, lvl, 1, "monthly_rent") for lvl in LEVELS]

    for ax, ladder in zip(axes, ("name", "role")):
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.3, 5.9)
        ax.axis("off")
        cases = rows[ladder]
        t = cases[0].target
        title, sub = (("(a) Name ladder", "the asked company does not exist") if ladder == "name" else
                      ("(b) Role ladder", "company and building exist; that lease does not"))
        ax.text(0, 5.75, title, fontsize=8.6, fontweight="bold", color=INK, va="center")
        ax.text(0, 5.25, sub, fontsize=7.2, color=INK2, va="center")
        if ladder == "name":
            asked = [("Asked:  ", INK2), (t["tenant"], INK)]
        else:
            asked = [("Asked:  ", INK2), (f"{t['tenant']} · {t['building']} · started {t['start_year']}", INK)]
        _draw_segments(ax, fig, 0, 4.55, asked, size=7.4)
        for i, (lvl, case) in enumerate(zip(LEVELS, cases)):
            y = 3.7 - i * 1.05
            ax.add_patch(FancyBboxPatch((0, y - 0.36), 0.19, 0.72, boxstyle="round,pad=0,rounding_size=0.02",
                                        fc=RAMP[lvl], ec="none", mutation_aspect=12))
            ax.text(0.095, y, lvl, ha="center", va="center", fontsize=7.2, fontweight="bold",
                    color=INK if lvl in ("none", "weak") else "#ffffff")
            if not case.lookalikes:
                ax.text(0.22, y, "no look-alike record in the document", fontsize=7.2, color=MUTED,
                        style="italic", va="center")
                continue
            f = case.lookalikes[0].fields
            if ladder == "name":
                segs = _name_segments(t["tenant"], f["tenant"])
            else:
                segs = [(f["tenant"], INK if f["tenant"] == t["tenant"] else ORANGE), (" · ", MUTED),
                        (f["building"], INK if f["building"] == t["building"] else ORANGE), (" · started ", MUTED),
                        (str(f["start_date"].year), INK if f["start_date"].year == t["start_year"] else ORANGE)]
            _draw_segments(ax, fig, 0.22, y, segs, size=7.2)
    fig.text(0.5, -0.02, "Each row is a separate document built from the same seed. Bold orange = where the "
             "look-alike differs from what is asked.", ha="center", fontsize=6.8, color=INK2)
    save(fig, out, "fig2_ladders", dpi)


# ----------------------------------------------------------------------------- data for 3 and 4

def load_dataset(root: Path):
    docs, questions = [], []
    for exp_dir in sorted(p for p in root.iterdir() if p.is_dir() and (p / "questions.jsonl").exists()):
        for jp in sorted((exp_dir / "docs").glob("*.json")):
            m = json.loads(jp.read_text(encoding="utf-8"))
            docs.append({"exp": exp_dir.name, "length_k": m["spec"]["length_k"], "deviation": m["deviation"],
                         "positions": m.get("lookalike_positions", []), "level": m["spec"]["level"]})
        with open(exp_dir / "questions.jsonl", encoding="utf-8") as f:
            questions += [json.loads(line) for line in f]
    return docs, questions


# ----------------------------------------------------------------------------- figure 3

def fig3_dataset_checks(out: Path, dpi: int, docs: list) -> None:
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULL_W, 2.35), gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.3})
    lengths = [8, 32, 64, 128]
    rng = random.Random(0)
    for i, L in enumerate(lengths):
        d = [x["deviation"] * 100 for x in docs if x["length_k"] == L]
        xs = [i + rng.uniform(-0.28, 0.28) for _ in d]
        a.scatter(xs, d, s=9, color=BLUE, alpha=0.55, linewidths=0, zorder=3)
        a.text(i, 1.12, f"n={len(d)}", ha="center", va="bottom", fontsize=6.6, color=INK2)
    for yv in (-1, 1):
        a.axhline(yv, color=MUTED, lw=0.8, ls=(0, (3, 2)), zorder=1)
    a.axhline(0, color=GRID, lw=0.8, zorder=0)
    a.text(3.45, 1.0, "allowed ±1%", ha="right", va="top", fontsize=6.6, color=INK2)
    worst = max(abs(x["deviation"]) for x in docs) * 100
    a.text(3.45, -0.96, f"largest error {worst:.2f}%", ha="right", va="bottom", fontsize=6.6, color=INK2)
    a.set_xticks(range(4), [f"{L}K" for L in lengths])
    a.set_xlim(-0.55, 3.55)
    a.set_ylim(-1.3, 1.45)
    a.set_ylabel("length error (% of target)")
    a.set_xlabel("target length (tokens)")
    a.set_title("(a) Every document hits its length", loc="left")

    pos = [p for x in docs for p in x["positions"]]
    b.axvspan(35, 65, color=PANEL, zorder=0)
    b.text(33, 0.97, "target zone\n35–65%", transform=b.get_xaxis_transform(), ha="right", va="top",
           fontsize=6.6, color=INK2)
    step = 30 / 7                                  # the 8 slots are 35%, 35+30/7%, ..., 65%: one bin per slot
    first = 35 - step / 2
    lo = first - step * int(first // step + 1)
    bins = [lo + k * step for k in range(int((100 - lo) / step) + 2)]
    b.hist([p * 100 for p in pos], bins=bins, color=BLUE, edgecolor=SURFACE, linewidth=0.6, zorder=2)
    b.set_xlim(0, 100)
    b.set_xlabel("position in the document (% of tokens)")
    b.set_ylabel("look-alike records")
    b.set_title(f"(b) All {len(pos):,} look-alikes sit in the middle", loc="left")
    b.yaxis.grid(True, color=GRID, lw=0.6)
    b.set_axisbelow(True)
    save(fig, out, "fig3_dataset_checks", dpi)


# ----------------------------------------------------------------------------- figure 4

def fig4_composition(out: Path, dpi: int, questions: list) -> None:
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULL_W, 2.2), gridspec_kw={"width_ratios": [1.35, 1], "wspace": 0.55})
    exps = sorted({q["exp"] for q in questions}, key=lambda e: int(e[3:]))
    names = {"exp2": "Exp 2  ladder", "exp3": "Exp 3  length", "exp4": "Exp 4  copies",
             "exp5": "Exp 5  fixes", "exp7": "Exp 7  batching"}
    un = [sum(1 for q in questions if q["exp"] == e and not q["answerable"]) for e in exps]
    an = [sum(1 for q in questions if q["exp"] == e and q["answerable"]) for e in exps]
    ys = list(range(len(exps)))[::-1]
    a.barh(ys, un, height=0.62, color=BLUE, edgecolor=SURFACE, linewidth=1.5, label="no answer", zorder=2)
    a.barh(ys, an, left=un, height=0.62, color=ORANGE, edgecolor=SURFACE, linewidth=1.5, label="has an answer",
           zorder=2)
    for y, u, n in zip(ys, un, an):
        a.text(u + n + max(un) * 0.02, y, f"{u + n:,}", va="center", fontsize=7, color=INK)
    a.set_yticks(ys, [names.get(e, e) for e in exps])
    a.tick_params(axis="y", length=0)
    a.spines["left"].set_visible(False)
    a.set_xlabel("questions (per model)")
    a.set_xlim(0, max(u + n for u, n in zip(un, an)) * 1.16)
    a.xaxis.grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
    a.legend(loc="lower right", handlelength=1.0, handleheight=0.8, borderaxespad=0.2)
    a.set_title(f"(a) {sum(un) + sum(an):,} questions, 2 : 1 no-answer to answer", loc="left")

    labels = {"monthly_rent": "monthly rent", "deposit": "deposit", "floor": "floor", "end_date": "end date",
              "start_date": "start date\n(name ladder only)"}
    c = collections.Counter(q["field"] for q in questions if not q["answerable"])
    order = sorted(c, key=lambda k: c[k])
    b.barh(range(len(order)), [c[k] for k in order], height=0.62, color=BLUE, zorder=2)
    for i, k in enumerate(order):
        b.text(c[k] + max(c.values()) * 0.02, i, f"{c[k]:,}", va="center", fontsize=7, color=INK)
    b.set_yticks(range(len(order)), [labels.get(k, k) for k in order])
    b.tick_params(axis="y", length=0)
    b.spines["left"].set_visible(False)
    b.set_xlim(0, max(c.values()) * 1.2)
    b.xaxis.grid(True, color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.set_xlabel("no-answer questions")
    b.set_title("(b) Asked fact", loc="left")
    save(fig, out, "fig4_composition", dpi)


# ----------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dpi", type=int, default=900)
    ap.add_argument("--only", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--data", default=None, help="dataset root (default: paths.yaml data.nullscale)")
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "figures"))
    a = ap.parse_args()
    out = Path(a.out)
    root = Path(a.data) if a.data else Path(load_paths()["data"]["nullscale"])
    want = [a.only] if a.only else [1, 2, 3, 4]

    docs, questions = ([], [])
    if root.exists() and any(want_i in want for want_i in (1, 3, 4)):
        docs, questions = load_dataset(root)
    have_data = bool(docs)
    print(f"dataset: {root}  ({len(docs)} documents, {len(questions)} questions)")
    print(f"output:  {out}")

    if 1 in want:
        fig1_pipeline(out, a.dpi, {"docs": len(docs), "questions": len(questions)} if have_data else None)
    if 2 in want:
        fig2_ladders(out, a.dpi)
    for i, fn, arg in ((3, fig3_dataset_checks, docs), (4, fig4_composition, questions)):
        if i in want:
            if have_data:
                fn(out, a.dpi, arg)
            else:
                print(f"  skipped figure {i}: no dataset yet. Run  python -m nullscale.build_dataset --exp all")


if __name__ == "__main__":
    main()
