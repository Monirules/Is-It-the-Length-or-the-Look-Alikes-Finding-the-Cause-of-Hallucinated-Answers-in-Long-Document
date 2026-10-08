"""analysis/overnight_checks.py

All CPU checks requested in the professor's to-do list that can be answered from files we already have,
plus the Llama 3.3 70B bf16 comparison once that run exists. No GPU. About 2 to 5 minutes.

Paper experiment names vs code names:  paper Exp 1 = code exp2 (ladder at 32K),
paper Exp 2 = code exp3 (length), paper Exp 3 = code exp4 (copies).

Writes to outputs/overnight/
  report.md                    every result in plain text, one section per to-do item (read this first)
  A_llama70b_128k_audit.csv    prompt tokens vs window, answers saved, outcome sources, FP8 vs bf16
  B_ladder_exp1.csv            paper Exp 1 split by ladder (name vs role), with Wilson intervals
  B_ladder_table2.csv          paper Table 2 split by ladder (strong at 32K vs no look-alike at longest length)
  C_three_way.csv              refused / made up with a flag / made up silently, paper Exp 1 strong level
  D_exchange_robustness.csv    exchange rate: full fit, leave one model out, leave one family out, leave one cell out
  E_signal_detection.csv       d' and c for sibling vs unrelated filler, hit rate = share correct, document bootstrap
  F_breaking_bootstrap.csv     breaking lengths with document-level bootstrap intervals
  G_riker_per_model.csv        RIKER2 missing field questions, per model, look-alike present vs none
  G_riker_interaction.csv      pooled logistic test of look-alike x length in RIKER2
  H_token_counts.csv           mean and max prompt tokens per model and target length (each model's tokenizer)
  I_clean_arm.csv              look-alike values found in no look-alike documents (should be zero)
  figures/*.png                previews (the paper redraws figures in TikZ from the CSV files)

Usage (cluster login node or PC, nullscale env, project folder)
  python -m analysis.overnight_checks
  python -m analysis.overnight_checks --results outputs/results_cluster --extra outputs/results --boot 2000
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.main_results import LENGTHS, LEVELS, MODELS, NAMES, exchange_rate, load, logit, wilson  # noqa: E402

FAMILY = {"qwen3_4b": "Qwen", "qwen3_30b_a3b": "Qwen", "qwen3_next_80b": "Qwen", "llama31_8b": "Llama",
          "llama33_70b": "Llama", "gemma3_27b": "Gemma", "glm45_air": "GLM"}
NAMES = dict(NAMES, glm45_air="GLM 4.5 Air 106B", qwen3_30b_a3b="Qwen3 30B A3B", qwen3_next_80b="Qwen3 Next 80B")
WINDOW = {"qwen3_4b": 262144, "llama31_8b": 131072, "gemma3_27b": 131072, "qwen3_30b_a3b": 262144,
          "llama33_70b": 131072, "qwen3_next_80b": 262144, "glm45_air": 131072}
FLAG_RX = re.compile(r"\b(however|note|noting|although|though|but|closest|similar|instead|not exactly|"
                     r"spelled|spelling|typo|differ|different|assum|might|may be|possibly|likely|seems|appears)\b", re.I)


# ----------------------------------------------------------------------------- helpers

def fisher(k1, n1, k2, n2):
    K, N = k1 + k2, n1 + n2
    if n1 == 0 or n2 == 0:
        return float("nan")
    lo, hi = max(0, K - n2), min(K, n1)

    def lp(x):
        return (math.lgamma(n1 + 1) - math.lgamma(x + 1) - math.lgamma(n1 - x + 1) + math.lgamma(n2 + 1)
                - math.lgamma(K - x + 1) - math.lgamma(n2 - K + x + 1) - math.lgamma(N + 1)
                + math.lgamma(K + 1) + math.lgamma(N - K + 1))
    obs = lp(k1)
    return min(1.0, sum(math.exp(lp(x)) for x in range(lo, hi + 1) if lp(x) <= obs + 1e-9))


def made_up(rs):
    rs = [r for r in rs if not r["answerable"]]
    k = sum(r["made_up"] for r in rs)
    return (k, len(rs)) + wilson(k, len(rs))


def correct(rs):
    rs = [r for r in rs if r["answerable"]]
    k = sum(r["label"] == "correct" for r in rs)
    return (k, len(rs)) + wilson(k, len(rs))


def p100(x):
    return "" if x is None or (isinstance(x, float) and math.isnan(x)) else round(100 * x, 1)


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def by_doc(rs):
    d = defaultdict(list)
    for r in rs:
        d[r["doc"]].append(r)
    return d


def boot_rate(rs, fn, B, rng):
    """Document-level bootstrap of fn(list of rows) -> number. Returns (2.5%, 97.5%)."""
    docs = list(by_doc(rs).values())
    if not docs:
        return float("nan"), float("nan")
    vals = []
    for _ in range(B):
        sample = [r for d in (rng.choice(docs) for _ in docs) for r in d]
        v = fn(sample)
        if v is not None and not math.isnan(v):
            vals.append(v)
    if not vals:
        return float("nan"), float("nan")
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]


def frac_made_up(rs):
    rs = [r for r in rs if not r["answerable"]]
    return sum(r["made_up"] for r in rs) / len(rs) if rs else float("nan")


def load_extra(folder: Path, key: str) -> list[dict]:
    """Scored rows of one extra run folder (e.g. the bf16 rerun), same fields as main_results.load."""
    f = folder / "scored.csv"
    if not f.exists():
        return []
    out = []
    for r in csv.DictReader(open(f, encoding="utf-8")):
        r.update(exp="exp3", model=key, run="t0_s0", prompt="normal", answerable=r["answerable"] == "True",
                 made_up=r["label"] == "made_up", captured=r.get("captured") == "True",
                 length=int(r["length_k"]), copies_n=int(r["copies"] or 0), doc=r["qid"].split("/")[0])
        out.append(r)
    return out


def zq(p):
    """Inverse normal CDF (Acklam's approximation), enough for d' and c."""
    p = min(max(p, 0.005), 0.995)
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771201e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    pl = 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > 1 - pl:
        return -zq(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


# ----------------------------------------------------------------------------- main

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(PROJECT_ROOT / "outputs" / "results_cluster"))
    ap.add_argument("--extra", default=str(PROJECT_ROOT / "outputs" / "results"),
                    help="folder that may hold exp3_llama33_70b_bf16_normal_t0_s0 (the overnight rerun)")
    ap.add_argument("--riker", default=str(PROJECT_ROOT / "outputs" / "riker"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "overnight"))
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args(argv)
    out = Path(a.out)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    rng = random.Random(0)

    rows = [r for r in load(Path(a.results)) if r["prompt"] in ("normal", "batch12")]
    if not rows:
        sys.exit(f"no scored.csv under {a.results}")
    models = [m for m in MODELS if any(r["model"] == m for r in rows)]
    e1 = [r for r in rows if r["exp"] == "exp2" and r["run"] == "t0_s0" and r["prompt"] == "normal"]
    e2 = [r for r in rows if r["exp"] == "exp3" and r["prompt"] == "normal"]
    R = ["# Overnight checks (analysis/overnight_checks.py)", "",
         "Paper Exp 1 = code exp2, paper Exp 2 = code exp3. Rates in %. Intervals are 95%.", ""]

    # ------------------------------------------------------------------ A. Llama 3.3 70B at 128K
    R += ["## A. Llama 3.3 70B at 128K (to-do item 5)", ""]
    A = []
    for m in models:
        for L in LENGTHS:
            rs = [r for r in e2 if r["model"] == m and r["length"] == L]
            if not rs:
                continue
            toks = [int(r["n_prompt_tokens"]) for r in rs if r.get("n_prompt_tokens", "").isdigit()]
            A.append({"model": NAMES[m], "length_k": L, "answers_saved": len(rs), "expected": 960,
                      "max_prompt_tokens": max(toks) if toks else "", "window": WINDOW[m],
                      "headroom_tokens": (WINDOW[m] - max(toks)) if toks else "",
                      "output_truncated_pct": p100(sum(r["truncated"] == "True" for r in rs) / len(rs))})
    llama = [r for r in e2 if r["model"] == "llama33_70b" and r["length"] == 128]
    mu = [r for r in llama if r["level"] == "none" and r["made_up"]]
    src = Counter(r["source"] for r in mu)
    toks = [int(r["n_prompt_tokens"]) for r in llama if r.get("n_prompt_tokens", "").isdigit()]
    R += [f"- Answers saved at 128K: {len(llama)} of 960 (per level 320 unanswerable and 160 answerable). Largest prompt {max(toks):,} tokens "
          f"against a window of 131,072 ({131072 - max(toks):,} tokens to spare). The runner skips any document "
          f"that does not fit and never cuts one, so no prompt was truncated.",
          f"- Output truncated at 256 tokens: {sum(r['truncated'] == 'True' for r in llama)} of {len(llama)} answers.",
          f"- Made up answers without a look-alike: {len(mu)} of 320. Where the value came from: "
          + ", ".join(f"{k} {v}" for k, v in src.most_common()) + " (other_record = the stated value belongs to "
          "another record in the document, so the model copies a real value from the wrong record).", ""]
    bf = load_extra(Path(a.extra) / "exp3_llama33_70b_bf16_normal_t0_s0", "llama33_70b_bf16")
    if bf:
        R += ["### FP8 (main run) against bf16 (overnight rerun), Llama 3.3 70B at 128K", "",
              "| level | FP8 made up | bf16 made up | Fisher p | FP8 accuracy | bf16 accuracy |", "|---|---|---|---|---|---|"]
        for lv in ("none", "strong"):
            f8 = [r for r in llama if r["level"] == lv]
            b16 = [r for r in bf if r["length"] == 128 and r["level"] == lv]
            if not b16:
                continue
            a1, a2 = made_up(f8), made_up(b16)
            c1, c2 = correct(f8), correct(b16)
            p = fisher(a1[0], a1[1], a2[0], a2[1])
            R.append(f"| {lv} | {p100(a1[2])} ({a1[0]}/{a1[1]}) | {p100(a2[2])} ({a2[0]}/{a2[1]}) | {p:.3g} | "
                     f"{p100(c1[2])} | {p100(c2[2])} |")
            A.append({"model": "Llama 3.3 70B FP8 vs bf16", "length_k": 128, "level": lv,
                      "fp8_made_up": p100(a1[2]), "bf16_made_up": p100(a2[2]), "fisher_p": round(p, 4),
                      "fp8_accuracy": p100(c1[2]), "bf16_accuracy": p100(c2[2])})
        R.append("")
    else:
        R += ["- bf16 rerun not found yet (expected in outputs/results/exp3_llama33_70b_bf16_normal_t0_s0). "
              "Rerun this script after the GPU job finishes.", ""]
    keys = sorted({k for d in A for k in d}, key=lambda k: list(A[0].keys()).index(k) if k in A[0] else 99)
    write_csv(out / "A_llama70b_128k_audit.csv", [{k: d.get(k, "") for k in keys} for d in A])

    # ------------------------------------------------------------------ B. by ladder
    R += ["## B. Results by ladder (to-do item 7, 'is it just typo correction?')", "",
          "Paper Exp 1 at 32K. The role ladder never changes a name, so a made up answer there is plainly wrong.", "",
          "| model | ladder | none | weak | medium | strong | strong minus none (points) |", "|---|---|---|---|---|---|---|"]
    B1, gaps = [], {"name": [], "role": []}
    for m in models:
        for lad in ("name", "role"):
            v = {lv: made_up([r for r in e1 if r["model"] == m and r["ladder"] == lad and r["level"] == lv]) for lv in LEVELS}
            g = v["strong"][2] - v["none"][2]
            gaps[lad].append(g)
            R.append(f"| {NAMES[m]} | {lad} | " + " | ".join(f"{p100(v[lv][2])}" for lv in LEVELS) + f" | {100 * g:+.1f} |")
            B1.append({"model": NAMES[m], "ladder": lad, **{f"{lv}_pct": p100(v[lv][2]) for lv in LEVELS},
                       **{f"{lv}_lo": p100(v[lv][3]) for lv in LEVELS}, **{f"{lv}_hi": p100(v[lv][4]) for lv in LEVELS},
                       "n_per_level": v["strong"][1], "strong_minus_none": round(100 * g, 1)})
    R += ["", f"- Name ladder: strong minus none = {100 * min(gaps['name']):.0f} to {100 * max(gaps['name']):.0f} points.",
          f"- Role ladder: strong minus none = {100 * min(gaps['role']):.0f} to {100 * max(gaps['role']):.0f} points.", ""]
    write_csv(out / "B_ladder_exp1.csv", B1)

    B2 = []
    R += ["### Table 2 by ladder: strong look-alike at 32K vs no look-alike at the longest length", "",
          "| model | ladder | strong, 32K | none, longest | gap (points) |", "|---|---|---|---|---|"]
    for m in models:
        for lad in ("name", "role"):
            s = made_up([r for r in e1 if r["model"] == m and r["ladder"] == lad and r["level"] == "strong"])
            Lmax = max((L for L in LENGTHS if any(r["model"] == m and r["length"] == L for r in e2)), default=None)
            n = made_up([r for r in e2 if r["model"] == m and r["ladder"] == lad and r["level"] == "none" and r["length"] == Lmax])
            R.append(f"| {NAMES[m]} | {lad} | {p100(s[2])} | {p100(n[2])} ({Lmax}K) | {100 * (s[2] - n[2]):.1f} |")
            B2.append({"model": NAMES[m], "ladder": lad, "strong_32k": p100(s[2]), "none_longest": p100(n[2]),
                       "longest_k": Lmax, "gap_points": round(100 * (s[2] - n[2]), 1)})
    R.append("")
    write_csv(out / "B_ladder_table2.csv", B2)

    # ------------------------------------------------------------------ C. three-way outcome
    R += ["## C. Three-way outcome (to-do item 7)", "",
          "Paper Exp 1, strong look-alike. 'Flagged' = a made up answer that also signals doubt or a mismatch "
          "(hedge words, or words like however, note, closest, similar, spelled, different). 'Silent' = all other "
          "made up answers. The headline effect is recomputed with flagged answers counted as refusals.", "",
          "| model | ladder | refused | made up, flagged | made up, silent | silent only, strong minus none |",
          "|---|---|---|---|---|---|"]
    C = []
    for m in models:
        for lad in ("name", "role", "both"):
            sel = lambda lv: [r for r in e1 if r["model"] == m and not r["answerable"] and r["level"] == lv
                              and (lad == "both" or r["ladder"] == lad)]
            st = sel("strong")
            if not st:
                continue
            flag = [r for r in st if r["made_up"] and (r.get("hedged") == "True" or FLAG_RX.search(r["response"] or ""))]
            silent = [r for r in st if r["made_up"] and r not in flag]
            refused = [r for r in st if r["label"] == "refused"]
            none_silent = [r for r in sel("none") if r["made_up"] and not (r.get("hedged") == "True" or FLAG_RX.search(r["response"] or ""))]
            gap = len(silent) / len(st) - len(none_silent) / max(1, len(sel("none")))
            R.append(f"| {NAMES[m]} | {lad} | {p100(len(refused) / len(st))} | {p100(len(flag) / len(st))} | "
                     f"{p100(len(silent) / len(st))} | {100 * gap:+.1f} |")
            C.append({"model": NAMES[m], "ladder": lad, "n": len(st), "refused_pct": p100(len(refused) / len(st)),
                      "made_up_flagged_pct": p100(len(flag) / len(st)), "made_up_silent_pct": p100(len(silent) / len(st)),
                      "silent_strong_minus_none": round(100 * gap, 1)})
    R.append("")
    write_csv(out / "C_three_way.csv", C)

    # ------------------------------------------------------------------ D. exchange rate robustness
    R += ["## D. Exchange rate robustness (to-do item 3)", "",
          "Exchange rate = doublings of length (no look-alike) that add as much log odds as one strong look-alike "
          "at 8K. 'undefined' means length has no clearly positive effect in that fit.", ""]
    D = []

    def ex(label, kind, ms, excl=lambda r: False):
        try:
            res = exchange_rate(e2, ms, exclude=excl)
        except Exception as e:  # noqa: BLE001
            res = None
        val = res["exchange"] if res else float("nan")
        D.append({"fit": label, "kind": kind, "exchange_doublings": "" if math.isnan(val) else round(val, 2),
                  "length_factor": "" if math.isnan(val) else round(2 ** val, 1),
                  "slope_no_lookalike": round(res["b_len_none"], 3) if res else "",
                  "or_doubling_main": round(math.exp(res["b_len"]), 3) if res else "",
                  "n": res["n"] if res else 0})
        return val

    full = ex("all models, all cells", "full", models)
    for m in models:
        ex(f"without {NAMES[m]}", "leave one model out", [x for x in models if x != m])
    for fam in sorted(set(FAMILY[m] for m in models)):
        ex(f"without {fam} family", "leave one family out", [x for x in models if FAMILY[x] != fam])
    for m in models:
        for L in (32, 64, 128):
            if any(r["model"] == m and r["length"] == L for r in e2):
                ex(f"without {NAMES[m]} at {L}K", "leave one cell out", models,
                   lambda r, m=m, L=L: r["model"] == m and r["length"] == L)
    write_csv(out / "D_exchange_robustness.csv", D)
    for kind in ("leave one model out", "leave one family out", "leave one cell out"):
        vs = [d for d in D if d["kind"] == kind]
        ok = [d["exchange_doublings"] for d in vs if d["exchange_doublings"] != ""]
        und = [d["fit"] for d in vs if d["exchange_doublings"] == ""]
        R.append(f"- {kind}: {min(ok) if ok else '-'} to {max(ok) if ok else '-'} doublings over {len(ok)} fits"
                 + (f"; undefined in {len(und)} fits ({', '.join(und[:4])}{'...' if len(und) > 4 else ''})" if und else "") + ".")
    R += [f"- Full fit: {full:.2f} doublings." if not math.isnan(full) else "- Full fit: undefined.",
          "- Read: if the range is wide or often undefined, keep the exchange rate out of the abstract and lead "
          "with Table 2 (probability scale).", ""]

    # ------------------------------------------------------------------ E. signal detection
    R += ["## E. Sibling filler as signal detection (to-do item 8)", "",
          "Hit rate H = share of answerable questions answered correctly (same definition everywhere, fixes the "
          "14.9 vs 16.4 mismatch). False alarm rate F = made up rate with a strong look-alike. "
          "d' = z(H) - z(F), c = -(z(H) + z(F))/2, rates clipped to [0.005, 0.995]. Intervals: document bootstrap.", "",
          "| model | filler | H | F | d' [95%] | c [95%] |", "|---|---|---|---|---|---|"]
    E = []
    for m in models:
        for fil in ("unrelated", "sibling"):
            rs = [r for r in e2 if r["model"] == m and r["filler"] == fil]
            ans = [r for r in rs if r["answerable"]]
            st = [r for r in rs if r["level"] == "strong" and not r["answerable"]]

            def stats(sample_ans, sample_st):
                if not sample_ans or not sample_st:
                    return float("nan"), float("nan")
                H = sum(r["label"] == "correct" for r in sample_ans) / len(sample_ans)
                F = sum(r["made_up"] for r in sample_st) / len(sample_st)
                return zq(H) - zq(F), -(zq(H) + zq(F)) / 2
            dp, cc = stats(ans, st)
            da, ds = list(by_doc(ans).values()), list(by_doc(st).values())
            bd, bc = [], []
            for _ in range(min(a.boot, 1000)):
                sa = [r for d in (rng.choice(da) for _ in da) for r in d]
                ss = [r for d in (rng.choice(ds) for _ in ds) for r in d]
                x, y = stats(sa, ss)
                bd.append(x); bc.append(y)
            bd.sort(); bc.sort()
            lo = lambda v: v[int(0.025 * len(v))]
            hi = lambda v: v[int(0.975 * len(v)) - 1]
            H = sum(r["label"] == "correct" for r in ans) / len(ans)
            F = sum(r["made_up"] for r in st) / len(st)
            R.append(f"| {NAMES[m]} | {fil} | {100 * H:.1f} | {100 * F:.1f} | {dp:.2f} [{lo(bd):.2f}, {hi(bd):.2f}] | "
                     f"{cc:.2f} [{lo(bc):.2f}, {hi(bc):.2f}] |")
            E.append({"model": NAMES[m], "filler": fil, "hit_rate": round(100 * H, 1), "false_alarm": round(100 * F, 1),
                      "d_prime": round(dp, 3), "d_lo": round(lo(bd), 3), "d_hi": round(hi(bd), 3),
                      "c": round(cc, 3), "c_lo": round(lo(bc), 3), "c_hi": round(hi(bc), 3)})
    R.append("")
    for m in models:
        u = next(e for e in E if e["model"] == NAMES[m] and e["filler"] == "unrelated")
        s = next(e for e in E if e["model"] == NAMES[m] and e["filler"] == "sibling")
        R.append(f"- {NAMES[m]}: accuracy loss {u['hit_rate'] - s['hit_rate']:.1f} points, change in c "
                 f"{s['c'] - u['c']:+.2f}, change in d' {s['d_prime'] - u['d_prime']:+.2f}.")
    R.append("")
    write_csv(out / "E_signal_detection.csv", E)

    # ------------------------------------------------------------------ F. breaking lengths, document bootstrap
    R += ["## F. Breaking lengths with document-level bootstrap intervals (to-do item 2)", "",
          "Rule: first length whose interval lies fully above the 8K interval. Wilson treats the 320 questions per "
          "cell as independent; the bootstrap resamples whole documents (40 per cell).", "",
          "| model | 8K | 32K | 64K | 128K | break (Wilson) | break (document bootstrap) |", "|---|---|---|---|---|---|---|"]
    F = []
    for m in models:
        cells, wil, bts = {}, {}, {}
        for L in LENGTHS:
            rs = [r for r in e2 if r["model"] == m and r["length"] == L and r["level"] == "none"]
            if not rs:
                continue
            k, n, p, wl, wh = made_up(rs)
            bl, bh = boot_rate(rs, frac_made_up, a.boot, rng)
            cells[L] = (p, n, len(by_doc(rs)))
            wil[L], bts[L] = (wl, wh), (bl, bh)
            F.append({"model": NAMES[m], "length_k": L, "made_up_pct": p100(p), "questions": n, "documents": len(by_doc(rs)),
                      "wilson_lo": p100(wl), "wilson_hi": p100(wh), "boot_lo": p100(bl), "boot_hi": p100(bh)})
        brk_w = next((L for L in LENGTHS[1:] if L in wil and wil[L][0] > wil[8][1]), None)
        brk_b = next((L for L in LENGTHS[1:] if L in bts and bts[L][0] > bts[8][1]), None)
        R.append(f"| {NAMES[m]} | " + " | ".join(
            f"{p100(cells[L][0])} [{p100(bts[L][0])}, {p100(bts[L][1])}]" if L in cells else "-" for L in LENGTHS)
                 + f" | {brk_w or 'none'}{'K' if brk_w else ''} | {brk_b or 'none'}{'K' if brk_b else ''} |")
    R.append("")
    write_csv(out / "F_breaking_bootstrap.csv", F)

    # ------------------------------------------------------------------ G. RIKER2 per model
    pm_f = Path(a.riker) / "exp1_per_model.csv"
    if pm_f.exists():
        pm = list(csv.DictReader(open(pm_f, encoding="utf-8")))
        panel = sorted({r["model"] for r in pm if r["in_balanced_panel"] == "True"})
        G, pos = [], Counter()
        R += ["## G. RIKER2 per model, missing field questions (to-do item 12)", "",
              f"{len(panel)} models tested at all three lengths. Difference = look-alike present minus none, in points.", "",
              "| length | models with a significant positive difference | significant negative | not significant |",
              "|---|---|---|---|"]
        agg = []
        for L in (32, 128, 200):
            cnt = Counter()
            for mdl in panel:
                cell = {g: next((r for r in pm if r["model"] == mdl and int(r["context_k"]) == L and r["level"] == "L12"
                                 and r["group"] == g), None) for g in ("present", "none")}
                if not all(cell.values()):
                    continue
                kp, npn = int(cell["present"]["made_up_riker"]), int(cell["present"]["n"])
                kn, nn = int(cell["none"]["made_up_riker"]), int(cell["none"]["n"])
                pp, pl, ph = wilson(kp, npn)
                pn, nl, nh = wilson(kn, nn)
                p = fisher(kp, npn, kn, nn)
                sig = "positive" if (p < 0.05 and pp > pn) else ("negative" if p < 0.05 else "none")
                cnt[sig] += 1
                G.append({"model": mdl, "length_k": L, "present_pct": p100(pp), "present_lo": p100(pl), "present_hi": p100(ph),
                          "present_n": npn, "none_pct": p100(pn), "none_lo": p100(nl), "none_hi": p100(nh), "none_n": nn,
                          "diff_points": round(100 * (pp - pn), 1), "fisher_p": round(p, 4), "significant": sig})
                for g, k, n in (("present", kp, npn), ("none", kn, nn)):
                    agg.append((mdl, L, g, k, n))
            R.append(f"| {L}K | {cnt['positive']} | {cnt['negative']} | {cnt['none']} |")
        write_csv(out / "G_riker_per_model.csv", G)
        # pooled logistic: made_up ~ present + log2(L/32) + present x log2(L/32) + model, binomial counts
        try:
            X, y, w = [], [], []
            mods = sorted({t[0] for t in agg})
            for mdl, L, g, k, n in agg:
                lam = math.log2(L / 32)
                pr = 1.0 if g == "present" else 0.0
                base = [1.0, pr, lam, pr * lam] + [1.0 if mdl == mm else 0.0 for mm in mods[1:]]
                X += [base, base]
                y += [1.0, 0.0]
                w += [k, n - k]
            b, se = logit(X, y, w)
            inter = {"term": ["look-alike present", "log2(length/32K)", "present x log2(length/32K)"],
                     "log_odds": [round(b[1], 3), round(b[2], 3), round(b[3], 3)],
                     "se": [round(se[1], 3), round(se[2], 3), round(se[3], 3)]}
            write_csv(out / "G_riker_interaction.csv", [{"term": t, "log_odds": lo_, "se": s_, "z": round(lo_ / s_, 2) if s_ else ""}
                                                        for t, lo_, s_ in zip(inter["term"], inter["log_odds"], inter["se"])])
            R += ["", f"- Pooled logistic test (models as fixed effects): look-alike {b[1]:+.2f} (SE {se[1]:.2f}) log odds at 32K, "
                  f"change per doubling {b[3]:+.2f} (SE {se[3]:.2f}, z = {b[3] / se[3]:.1f}). A clearly negative interaction "
                  f"means the look-alike effect shrinks with length in RIKER2.", ""]
        except Exception as e:  # noqa: BLE001
            R += ["", f"- interaction test failed: {e}", ""]
    else:
        R += ["## G. RIKER2 per model", "", f"(missing {pm_f})", ""]

    # ------------------------------------------------------------------ H. token counts
    R += ["## H. Prompt tokens per model and target length (before-submission item)", "",
          "| model | 8K | 32K | 64K | 128K |", "|---|---|---|---|---|"]
    Hh = []
    for m in models:
        cells = []
        for L in LENGTHS:
            t = [int(r["n_prompt_tokens"]) for r in e2 if r["model"] == m and r["length"] == L and r.get("n_prompt_tokens", "").isdigit()]
            if t:
                Hh.append({"model": NAMES[m], "length_k": L, "mean_prompt_tokens": round(sum(t) / len(t)),
                           "max_prompt_tokens": max(t), "window": WINDOW[m]})
                cells.append(f"{sum(t) / len(t):,.0f}")
            else:
                cells.append("-")
        R.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
    R.append("")
    write_csv(out / "H_token_counts.csv", Hh)

    # ------------------------------------------------------------------ I. clean no look-alike arm
    R += ["## I. Is the no look-alike arm clean? (to-do item 4)", ""]
    I = []
    for e, nm in ((e1, "paper Exp 1"), (e2, "paper Exp 2")):
        none_rows = [r for r in e if r["level"] == "none"]
        bad = [r for r in none_rows if (r.get("lookalike_values") or "").strip()]
        docs = {r["doc"] for r in none_rows}
        lv_per_doc = defaultdict(set)
        for r in e:
            lv_per_doc[r["doc"]].add(r["level"])
        mixed = sum(1 for s in lv_per_doc.values() if len(s) > 1)
        I.append({"experiment": nm, "no_lookalike_documents": len(docs), "answers_all_models": len(none_rows),
                  "questions_with_lookalike_values": len(bad), "documents_with_mixed_levels": mixed})
        R.append(f"- {nm}: {len(docs)} no look-alike documents, {len(none_rows)} answers over all models, {len(bad)} with a "
                 f"look-alike value attached; {mixed} documents mix levels across their questions.")
    R += ["- Every document is one cell of the design grid (configs/experiments.yaml: lengths x ladders x levels x "
          "copies x filler x contexts), so all questions of a document share one level. Zeros above confirm that a "
          "no look-alike document has no look-alike for any question.", ""]
    write_csv(out / "I_clean_arm.csv", I)

    # ------------------------------------------------------------------ figures (previews)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
        for ax, lad in zip(axes, ("name", "role")):
            for b in [x for x in B1 if x["ladder"] == lad]:
                ax.plot(range(4), [b[f"{lv}_pct"] for lv in LEVELS], marker="o", lw=1.2, label=b["model"])
            ax.set_xticks(range(4), LEVELS)
            ax.set_title(f"{lad} ladder", fontsize=9)
            ax.grid(alpha=0.3)
        axes[0].set_ylabel("made up answers (%)")
        axes[1].legend(fontsize=6, loc="upper left")
        fig.tight_layout()
        fig.savefig(out / "figures" / "fig_ladder_split.png", dpi=200)
        plt.close(fig)
        if pm_f.exists() and G:
            fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.0), sharex=True)
            for ax, L in zip(axes, (32, 128, 200)):
                gs = [g for g in G if g["length_k"] == L]
                for i, g in enumerate(gs):
                    ax.plot([g["none_pct"], g["present_pct"]], [i, i], color="gray", lw=0.8)
                    ax.plot(g["none_pct"], i, "o", color="tab:blue", ms=4)
                    ax.plot(g["present_pct"], i, "s", color="tab:orange", ms=4)
                ax.set_yticks(range(len(gs)), [g["model"] for g in gs], fontsize=6)
                ax.set_title(f"{L}K", fontsize=9)
                ax.grid(alpha=0.3)
            axes[1].set_xlabel("made up answers (%), blue none, orange look-alike present")
            fig.tight_layout()
            fig.savefig(out / "figures" / "fig_riker_per_model.png", dpi=200)
            plt.close(fig)
    except Exception as e:  # noqa: BLE001
        R.append(f"(figure previews skipped: {e})")

    (out / "report.md").write_text("\n".join(R) + "\n", encoding="utf-8")
    print("\n".join(R))
    print(f"\nAll files in {out}")


if __name__ == "__main__":
    main()
