"""run/timing_test.py  (owner: Monirul)

Times one test cell and turns it into a GPU-hour plan.

What it measures (one model, this GPU)
  * model load time
  * for each document: time for the FIRST question (reads and caches the whole document) and for
    the OTHER 11 (reuse the cached document), at every length asked for (PC: 8K and 32K)
  * how many prompt tokens the other 11 questions got from the cache

What it projects
  seconds per document t(L) = b*L + c*L^2 fitted through the measured lengths, then summed over every
  document of every experiment in configs/experiments.yaml (plus the three T=0.7 repeats of Exp 2).
  Lengths the PC cannot run (64K, 128K) are extrapolated and marked as such; re-run this script on the
  cluster, per model, for real numbers there.

Output (outputs/timing/ in the project folder):
  timing_<model>_<profile>.json   all measurements and the projection
  timing_<model>_<profile>.md     readable summary table
  fig7_timing_<model>_<profile>.png/.pdf

Usage (Ubuntu, nullscale env, project folder, GPU):
  python -m run.timing_test --model qwen3_4b                       # 3 documents at 8K and at 32K
  python -m run.timing_test --model qwen3_4b --n-docs 10 --lengths 8,32
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def projection(sec_per_doc: dict[int, float], first_per_doc: dict[int, float]) -> dict:
    """Fit t(L) through the origin (b*L + c*L^2) and apply it to every experiment's documents."""
    from nullscale.build_dataset import experiment_specs
    from nullscale.config import load_experiments
    Ls = sorted(sec_per_doc)
    if len(Ls) >= 2:                      # least squares for b, c through the origin
        import numpy as np
        X = np.array([[L, L * L] for L in Ls], float)
        y = np.array([sec_per_doc[L] for L in Ls], float)
        b, c = np.linalg.lstsq(X, y, rcond=None)[0]
        if c < 0:                         # never let attention cost shrink with length
            b, c = float(np.dot(X[:, 0], y) / np.dot(X[:, 0], X[:, 0])), 0.0
    else:
        b, c = sec_per_doc[Ls[0]] / Ls[0], 0.0
    t = lambda L: float(b * L + c * L * L)            # noqa: E731
    first = lambda L: t(L) * (first_per_doc[Ls[-1]] / sec_per_doc[Ls[-1]])   # document-reading share  # noqa: E731

    ecfg = load_experiments()
    d, rows = ecfg["defaults"], []
    measured = set(Ls)
    for name, exp in ecfg["experiments"].items():
        if exp["type"] in ("nullscale", "batching"):
            specs = experiment_specs(name, exp, d)
            if exp["type"] == "batching":            # two modes: one per call, and one call of 12
                parts = {s.length_k: 0.0 for s in specs}
                for s in specs:
                    parts[s.length_k] += t(s.length_k) + first(s.length_k)
            else:
                parts = {}
                for s in specs:
                    parts[s.length_k] = parts.get(s.length_k, 0.0) + t(s.length_k)
            reps = len(exp.get("repeats", {}).get("seeds", [])) if name == "exp2" else 0
            rows.append({"exp": name, "what": exp["title"], "seconds": sum(parts.values()),
                         "extrapolated_seconds": sum(v for L, v in parts.items() if L not in measured),
                         "lengths": sorted(parts)})
            if reps:
                rows.append({"exp": "exp2 repeats", "what": f"{reps} repeats at T={exp['repeats']['temperature']}",
                             "seconds": reps * sum(parts.values()), "extrapolated_seconds": 0.0, "lengths": sorted(parts)})
        elif exp["type"] == "fixes":
            n_docs = exp["contexts"]
            L = exp["lengths"][0]
            full = 2 * n_docs * t(L)                  # full_context and strict_prompt read the whole document
            short = 4 * n_docs * t(2)                  # retrieval versions: ~2K-token prompts
            rows.append({"exp": name, "what": exp["title"], "seconds": full + short,
                         "extrapolated_seconds": 0.0 if L in measured else full, "lengths": [L]})
        elif exp["type"] == "realdata":
            n = exp["n_questions"]
            secs = sum(first(8 if "8k" in s else 32) for s in exp["settings"]) * n
            rows.append({"exp": name, "what": exp["title"], "seconds": secs,
                         "extrapolated_seconds": 0.0, "lengths": exp["lengths"]})
    total = sum(r["seconds"] for r in rows)
    return {"fit": {"b_per_k": b, "c_per_k2": c, "formula": "seconds per document = b*L + c*L^2 (L in K tokens)"},
            "per_experiment": rows, "total_hours": total / 3600,
            "extrapolated_hours": sum(r["extrapolated_seconds"] for r in rows) / 3600,
            "t_of_L": {L: t(L) for L in (8, 32, 64, 128)}}


def write_outputs(res: dict, out_dir: Path, dpi: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"timing_{res['model']}_{res['profile']}"
    (out_dir / f"{stem}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    p = res["projection"]
    lines = [f"# Timing test: {res['model']} on {res['gpu']} ({res['profile']})", "",
             f"Model load: {res['load_seconds']:.0f} s. Prompt: {res['prompt']}. vLLM {res['vllm_version']}.", "",
             "| length | documents | first question (reads document) | other 11 (cached) | per document | cached tokens per later question |",
             "|---|---|---|---|---|---|"]
    for L, m in sorted(res["measured"].items(), key=lambda kv: int(kv[0])):
        cached = f"{m['mean_cached_tokens']:,.0f} of {m['mean_prompt_tokens']:,.0f}" if m["mean_cached_tokens"] else "n/a"
        lines.append(f"| {L}K | {m['n_docs']} | {m['first_seconds']:.1f} s | {m['rest_seconds']:.1f} s | "
                     f"{m['doc_seconds']:.1f} s | {cached} |")
    lines += ["", f"Fit: {p['fit']['formula']}, b = {p['fit']['b_per_k']:.4f}, c = {p['fit']['c_per_k2']:.6f}",
              "", "## Projected GPU time for the whole plan (this model, this GPU)", "",
              "| experiment | hours | of which extrapolated (64K/128K) |", "|---|---|---|"]
    for r in p["per_experiment"]:
        lines.append(f"| {r['exp']}: {r['what']} | {r['seconds'] / 3600:.2f} | {r['extrapolated_seconds'] / 3600:.2f} |")
    lines += [f"| **total** | **{p['total_hours']:.2f}** | {p['extrapolated_hours']:.2f} |", "",
              "Extrapolated rows use lengths this GPU could not run; re-run timing_test.py on the cluster for them."]
    (out_dir / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        _figure(res, out_dir, dpi)
    except Exception as e:                       # a figure problem must never lose the measurements
        print(f"[timing_test] figure skipped: {e}")
    print("\n".join(lines))
    print(f"\nsaved: {out_dir / (stem + '.json')}, .md and fig7 figure")


def _figure(res: dict, out_dir: Path, dpi: int) -> None:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import matplotlib.pyplot as plt
    from make_figures import BLUE, GRID, INK, INK2, ORANGE, SURFACE, FULL_W, save   # shared style
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULL_W, 2.4), gridspec_kw={"width_ratios": [1, 1.6], "wspace": 0.55})
    Ls = sorted(res["measured"], key=int)
    first = [res["measured"][L]["first_seconds"] for L in Ls]
    rest = [res["measured"][L]["rest_seconds"] for L in Ls]
    x = range(len(Ls))
    a.bar(x, first, width=0.55, color=BLUE, edgecolor=SURFACE, linewidth=1.5, label="question 1: reads document", zorder=2)
    a.bar(x, rest, bottom=first, width=0.55, color=ORANGE, edgecolor=SURFACE, linewidth=1.5,
          label="questions 2–12: cached", zorder=2)
    for i, (f_, r_) in enumerate(zip(first, rest)):
        a.text(i, f_ + r_, f"{f_ + r_:.1f}s", ha="center", va="bottom", fontsize=7, color=INK)
    a.set_xticks(list(x), [f"{L}K" for L in Ls])
    a.set_ylabel("seconds per document")
    a.set_ylim(0, max(f + r for f, r in zip(first, rest)) * 1.35)
    a.yaxis.grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
    a.legend(loc="upper left", handlelength=1.0, fontsize=6.6)
    a.set_title("(a) Seconds per document", loc="left")

    rows = [r for r in res["projection"]["per_experiment"]]
    names = [r["exp"] for r in rows][::-1]
    meas = [(r["seconds"] - r["extrapolated_seconds"]) / 3600 for r in rows][::-1]
    extr = [r["extrapolated_seconds"] / 3600 for r in rows][::-1]
    y = range(len(rows))
    b.barh(y, meas, height=0.6, color=BLUE, edgecolor=SURFACE, linewidth=1.2, label="measured lengths", zorder=2)
    b.barh(y, extr, left=meas, height=0.6, color=SURFACE, edgecolor=BLUE, hatch="////", linewidth=0.8,
           label="extrapolated (64K, 128K)", zorder=2)
    def hfmt(h):
        return f"{h * 60:.0f} min" if h < 1 else f"{h:.1f} h"
    for i, (m_, e_) in enumerate(zip(meas, extr)):
        b.text(m_ + e_ + max(m + e for m, e in zip(meas, extr)) * 0.02, i, hfmt(m_ + e_), va="center",
               fontsize=7, color=INK)
    b.set_yticks(list(y), names)
    b.tick_params(axis="y", length=0)
    b.spines["left"].set_visible(False)
    b.set_xlabel("GPU hours on this GPU (projected)")
    b.set_xlim(0, max(m + e for m, e in zip(meas, extr)) * 1.25)
    b.xaxis.grid(True, color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.legend(loc="lower right", fontsize=6.6, handlelength=1.2)
    tot = res['projection']['total_hours']
    b.set_title(f"(b) Projected time, whole plan: {hfmt(tot)}", loc="left")
    fig.text(0.01, -0.14, f"{res['model']} ({res['quantization']}) on {res['gpu']}. Per-document time fitted as "
             f"bL + cL² from the measured lengths.", fontsize=6.4, color=INK2)
    save(fig, out_dir, f"fig7_timing_{res['model']}_{res['profile']}", dpi)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="qwen3_4b")
    ap.add_argument("--exp", default="exp3", help="where the test documents come from (exp3 has every length)")
    ap.add_argument("--lengths", default=None, help="default 8,32 on the PC, 8,32,64,128 on the cluster")
    ap.add_argument("--n-docs", type=int, default=3, help="documents per length")
    ap.add_argument("--prompt", default="normal", choices=["normal", "strict"])
    ap.add_argument("--gpu-mem", type=float, default=None)
    ap.add_argument("--profile", choices=["pc", "cluster"], default=None)
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "timing"))
    ap.add_argument("--dpi", type=int, default=900)
    a = ap.parse_args(argv)

    from nullscale.config import load_models, load_paths
    from run import run_vllm as R
    from run.prompts import build_messages
    paths = load_paths(a.profile)
    profile = paths["profile"]
    lengths = [int(x) for x in (a.lengths or ("8,32" if profile == "pc" else "8,32,64,128")).split(",")]
    data_root = Path(a.data or paths["data"]["nullscale"])
    qs_all = R.load_questions(data_root, a.exp)
    # one test cell per length: the first (ladder, level, filler, copies) cell of the experiment
    cells = {}
    for L in lengths:
        docs = R.select_documents(qs_all, None, False, {L}, None)
        if not docs:
            sys.exit(f"{a.exp} has no {L}K documents")
        first_q = next(iter(docs.values()))[0]
        key = (first_q["ladder"], first_q["level"], first_q["filler"], first_q["copies"])
        same = [(d, qs) for d, qs in docs.items()
                if (qs[0]["ladder"], qs[0]["level"], qs[0]["filler"], qs[0]["copies"]) == key]
        cells[L] = {"cell": key, "docs": same[:a.n_docs]}
        print(f"{L}K test cell {key}: {len(cells[L]['docs'])} documents")

    import vllm
    from transformers import AutoTokenizer
    from vllm import SamplingParams
    m_cfg = load_models()["open_models"][a.model]
    chat_kwargs = m_cfg.get("chat_template_kwargs") or {}
    tok = AutoTokenizer.from_pretrained(m_cfg["hf_id"])
    need = max(R.count_prompt_tokens(tok, build_messages(R.read_document(data_root, qs[0]), qs[0]["question"], a.prompt),
                                     chat_kwargs) for c in cells.values() for _, qs in c["docs"])
    max_len = min(need + 256 + 128, m_cfg["max_model_len"])
    if profile == "pc" and max_len > m_cfg["pc"]["max_len"]:
        sys.exit(f"the longest test prompt needs {max_len:,} tokens but the PC limit for {a.model} is "
                 f"{m_cfg['pc']['max_len']:,} (configs/models.yaml, pc.max_len). Use --lengths 8 or raise the limit.")
    print(f"longest test prompt {need:,} tokens -> max_model_len {max_len:,}")
    kw, info = R.engine_settings(a.model, profile, max_len, a.gpu_mem, None)
    t0 = time.perf_counter()
    llm = R.make_llm(kw)
    load_s = time.perf_counter() - t0
    params = SamplingParams(temperature=0.0, max_tokens=256, seed=0)
    R.run_chat(llm, [[{"role": "user", "content": "Say OK."}]], params, chat_kwargs)       # warm-up

    base = {"run_id": "timing", "model": a.model, "hf_id": info["hf_id"], "profile": profile,
            "quantization": info["quantization"], "prompt_style": a.prompt, "prompt_version": "timing",
            "temperature": 0.0, "top_p": 1.0, "seed": 0, "max_tokens": 256,
            "vllm_version": getattr(vllm, "__version__", "?")}
    measured, calls, answers = {}, [0], []
    for L, c in cells.items():
        firsts, rests, cached, ptoks = [], [], [], []
        for doc_id, qs in c["docs"]:
            rows, tm = R.answer_document(llm, R.read_document(data_root, qs[0]), qs, a.prompt, params,
                                         chat_kwargs, base, calls)
            answers += rows
            firsts.append(tm["first_seconds"])
            rests.append(tm["rest_seconds"])
            ptoks.append(rows[0]["n_prompt_tokens"])
            cached += [r["cached_prompt_tokens"] for r in rows[1:] if r["cached_prompt_tokens"] is not None]
            print(f"  {L}K {doc_id}: first {tm['first_seconds']:.2f}s, other {len(qs) - 1} {tm['rest_seconds']:.2f}s")
        n = len(firsts)
        measured[str(L)] = {"cell": list(c["cell"]), "n_docs": n, "first_seconds": sum(firsts) / n,
                            "rest_seconds": sum(rests) / n, "doc_seconds": (sum(firsts) + sum(rests)) / n,
                            "mean_prompt_tokens": sum(ptoks) / n,
                            "mean_cached_tokens": (sum(cached) / len(cached)) if cached else None,
                            "questions_per_doc": len(c["docs"][0][1])}
    try:
        import torch
        gpu = torch.cuda.get_device_name(0)
    except Exception:
        gpu = "unknown GPU"
    res = {"model": a.model, "profile": profile, "gpu": gpu, "quantization": info["quantization"],
           "vllm_version": base["vllm_version"], "prompt": a.prompt, "load_seconds": load_s,
           "max_model_len": max_len, "measured": measured,
           "projection": projection({int(L): m["doc_seconds"] for L, m in measured.items()},
                                    {int(L): m["first_seconds"] for L, m in measured.items()}),
           "finished": time.strftime("%Y-%m-%d %H:%M:%S")}
    out = Path(a.out)
    write_outputs(res, out, a.dpi)
    with open(out / f"timing_{a.model}_{profile}_answers.jsonl", "w", encoding="utf-8") as f:
        for r in answers:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":        # required: vLLM on WSL starts workers that re-import this file
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
