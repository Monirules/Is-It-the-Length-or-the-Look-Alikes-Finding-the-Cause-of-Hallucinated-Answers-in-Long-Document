"""nullscale/assemble.py  (owner: Monirul)

Joins records into one document of exactly 8K, 32K, 64K or 128K tokens (within 1%), with the
look-alike record(s) placed in the middle.

A document contains
  * entity records       (role ladder: profiles of the asked company and building)
  * witness records      (4 leases that answer the 4 answerable questions; questions.py uses them)
  * look-alike record(s) (from lookalike.py; none for level "none"), centred on 50% of the tokens
  * filler records       (unrelated or sibling, from filler.py), N of them, N fixed per length and seed

Token counts use the reference tokenizer in configs/experiments.yaml (Llama 3.1 8B). If it cannot be
loaded it falls back to the Qwen3 tokenizer, and as a last resort to an approximate counter; the
tokenizer used is saved in every document's metadata.

Examples (run inside the nullscale conda env, from the project folder):
  python -m nullscale.assemble --length 32 --ladder name --level strong --filler unrelated --seed 1
  python -m nullscale.assemble --demo --length 32        # 2 ladders x 4 levels x 2 fillers = 16 documents
"""
from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict, dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

from nullscale import filler as F
from nullscale.lookalike import LADDERS, LEVELS, make_case
from nullscale.records import World
from nullscale.render import render

SEP = "\n\n"
N_WITNESSES = 4


# ----------------------------------------------------------------------------- tokenizer

@dataclass
class TokenCounter:
    name: str
    _fn: object
    sep: int = 1

    def count(self, text: str) -> int:
        return self._fn([text])[0]

    def count_many(self, texts: list[str]) -> list[int]:
        return self._fn(texts) if texts else []


def _approx(texts):
    return [len(re.findall(r"[A-Za-z]{1,6}|\d{1,3}|[^\sA-Za-z\d]", t)) for t in texts]


@lru_cache(maxsize=4)
def load_tokenizer(name: str | None = None) -> TokenCounter:
    names = [name] if name else []
    try:
        from nullscale.config import load_experiments
        names.append(load_experiments()["defaults"]["reference_tokenizer"])
    except Exception:
        pass
    names.append("Qwen/Qwen3-4B-Instruct-2507")
    try:
        from transformers import AutoTokenizer
        for n in dict.fromkeys(names):
            try:
                t = AutoTokenizer.from_pretrained(n)
                t.model_max_length = 10 ** 9          # counting only; silences the 'too long' warning
                fn = lambda xs, t=t: [len(ids) for ids in t(list(xs), add_special_tokens=False)["input_ids"]]
                tc = TokenCounter(n, fn)
                tc.sep = max(0, tc.count("a" + SEP + "b") - tc.count("a") - tc.count("b"))
                return tc
            except Exception as e:
                print(f"[assemble] could not load tokenizer {n}: {type(e).__name__}")
    except ImportError:
        pass
    print("[assemble] WARNING: using the APPROXIMATE token counter. Fine for testing, not for real data.")
    tc = TokenCounter("approx-regex", _approx)
    tc.sep = max(0, tc.count("a" + SEP + "b") - tc.count("a") - tc.count("b"))
    return tc


@lru_cache(maxsize=4)
def ref_record_cost(tok_name: str) -> float:
    """Average tokens per filler record (both kinds, fixed calibration seed). Sets N per budget,
    so both filler kinds get the same record count."""
    tok = load_tokenizer(tok_name if tok_name != "approx-regex" else None)
    means = []
    for kind in F.FILLER_KINDS:
        pool = F.make_pool(World(seed=0), kind, 600)
        rrng = random.Random(0)
        costs = tok.count_many([render(r, rrng) for r in pool])
        means.append(sum(costs) / len(costs) + tok.sep)
    return sum(means) / len(means)


# ----------------------------------------------------------------------------- building

@dataclass
class DocSpec:
    length_k: int
    ladder: str
    level: str
    filler: str = "unrelated"
    copies: int = 1
    seed: int = 0
    field: str = "monthly_rent"
    unit: int = 1000
    tolerance: float = 0.01

    @property
    def doc_id(self) -> str:
        return (f"{self.ladder}-{self.level}-c{self.copies}-{self.filler}-{self.length_k}k-"
                f"{self.field}-s{self.seed}")

    @property
    def target_tokens(self) -> int:
        return self.length_k * self.unit


def _jsonable(v):
    return v.isoformat() if isinstance(v, date) else v


def _positions(k: int) -> list[float]:
    if k <= 1:
        return [0.5]
    return [0.4 + 0.2 * i / (k - 1) for i in range(k)]


def build_document(spec: DocSpec, tok: TokenCounter | None = None) -> dict:
    tok = tok or load_tokenizer()
    world = World(seed=spec.seed * 1000 + 17)
    rrng = random.Random(spec.seed * 1000 + 29)       # template choices
    prng = random.Random(spec.seed * 1000 + 31)       # placement and selection

    case = make_case(world, spec.ladder, spec.level, spec.copies, spec.field)
    witnesses = [world.lease() for _ in range(N_WITNESSES)]
    for r in witnesses:
        r.role = "witness"
    core = case.entities + witnesses
    las = case.lookalikes

    core_txt = [render(r, rrng) for r in core]
    la_txt = [render(r, rrng) for r in las]
    fixed = sum(c + tok.sep for c in tok.count_many(core_txt + la_txt))
    target = spec.target_tokens
    budget = target - fixed
    n_fill = max(1, round(budget / ref_record_cost(tok.name)))

    pool = F.make_pool(world, spec.filler, int(n_fill * 2.5) + 40)
    pool_txt = [render(r, rrng) for r in pool]
    costs = [c + tok.sep for c in tok.count_many(pool_txt)]
    core_costs = [c + tok.sep for c in tok.count_many(core_txt)]
    la_costs = [c + tok.sep for c in tok.count_many(la_txt)]

    def layout(idx: list[int], shuffle_seed: int) -> list:
        """Random order of filler + core, then look-alikes inserted at the middle of the token stream."""
        items = [(pool[i], pool_txt[i], costs[i]) for i in idx]
        items += list(zip(core, core_txt, core_costs))
        random.Random(shuffle_seed).shuffle(items)
        base_total = sum(c for _, _, c in items)
        for frac, r, t, c in sorted(zip(_positions(len(las)), las, la_txt, la_costs), key=lambda z: -z[0]):
            cum, at = 0, len(items)
            for i, (_, _, ci) in enumerate(items):
                if cum >= frac * base_total:
                    at = i
                    break
                cum += ci
            items.insert(at, (r, t, c))
        return items

    def join(items) -> str:
        return SEP.join(t for _, t, _ in items)

    # Per-record counts do not add up exactly to the count of the joined text. Build, measure
    # the drift, correct the filler budget by it, and rebuild (a few rounds at most).
    tight = max(2, target // 1000)                      # aim for +/-0.1%; the hard limit is 1%
    correction = 0
    for attempt in range(4):
        idx = F.select_to_budget(costs, n_fill, budget - correction,
                                 random.Random(spec.seed * 1000 + 37 + attempt), tol=tight)
        items = layout(idx, spec.seed * 1000 + 41)
        text = join(items)
        n_tok = tok.count(text)
        if abs(n_tok - target) <= tight:
            break
        correction += n_tok - target

    # last small fixes: swap single filler records (record count stays the same)
    used = set(idx)
    unused = [i for i in range(len(pool)) if i not in used]
    for _ in range(50):
        gap = target - n_tok
        if abs(gap) <= tight or not unused:
            break
        fill_pos = [p for p, (r, _, _) in enumerate(items) if r.role == "filler"]
        p = prng.choice(fill_pos)
        want = items[p][2] + gap
        j = min(unused, key=lambda u: abs(costs[u] - want))
        unused.remove(j)
        items[p] = (pool[j], pool_txt[j], costs[j])
        text = join(items)
        n_tok = tok.count(text)

    # metadata
    records, offset = [], 0
    for r, t, _ in items:
        records.append({"rid": r.rid, "type": r.type, "role": r.role, "char_start": offset,
                        "char_end": offset + len(t), "tags": r.tags,
                        "fields": {k: _jsonable(v) for k, v in r.fields.items()}})
        offset += len(t) + len(SEP)
    la_pos = [round(tok.count(text[:rec["char_start"]]) / n_tok, 3) for rec in records if rec["role"] == "lookalike"]
    dev = (n_tok - target) / target
    return {
        "doc_id": spec.doc_id,
        "spec": asdict(spec),
        "tokenizer": tok.name,
        "n_tokens": n_tok,
        "target_tokens": target,
        "deviation": round(dev, 5),
        "within_tolerance": abs(dev) <= spec.tolerance,
        "n_words": len(text.split()),
        "n_records": len(records),
        "n_filler": sum(r["role"] == "filler" for r in records),
        "question": case.question,
        "target": case.target,
        "lookalike_values": [_jsonable(v) for v in case.lookalike_values()],
        "lookalike_positions": la_pos,
        "records": records,
        "text": text,
    }


def save_document(doc: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{doc['doc_id']}.txt").write_text(doc["text"], encoding="utf-8")
    meta = {k: v for k, v in doc.items() if k != "text"}
    (out_dir / f"{doc['doc_id']}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return out_dir / f"{doc['doc_id']}.txt"


def _out_dir(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    try:
        from nullscale.config import load_paths
        return Path(load_paths()["data"]["nullscale"]) / "demo"
    except Exception:
        return Path("data/nullscale/demo")


def _summary_row(d: dict) -> str:
    s = d["spec"]
    pos = ",".join(f"{p:.0%}" for p in d["lookalike_positions"]) or "-"
    return (f"{s['ladder']:<5} {s['level']:<7} {s['filler']:<10} {d['n_tokens']:>8,} {d['deviation']:>+8.2%} "
            f"{'yes' if d['within_tolerance'] else 'NO':>4} {d['n_records']:>6} {d['n_filler']:>6} {d['n_words']:>7,}  {pos}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--length", type=int, default=32, choices=[8, 32, 64, 128])
    ap.add_argument("--ladder", default="name", choices=LADDERS)
    ap.add_argument("--level", default="strong", choices=LEVELS)
    ap.add_argument("--filler", default="unrelated", choices=F.FILLER_KINDS)
    ap.add_argument("--copies", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--field", default="monthly_rent")
    ap.add_argument("--demo", action="store_true", help="build all ladders x levels x fillers at --length")
    ap.add_argument("--out", default=None, help="output folder (default: <data.nullscale>/demo)")
    a = ap.parse_args()

    tok = load_tokenizer()
    out = _out_dir(a.out)
    print(f"tokenizer: {tok.name}    output: {out}")
    header = (f"{'ladder':<5} {'level':<7} {'filler':<10} {'tokens':>8} {'dev':>8} {'ok':>4} "
              f"{'recs':>6} {'filler':>6} {'words':>7}  look-alike at")

    if a.demo:
        print(header)
        for ladder in LADDERS:
            for level in LEVELS:
                for kind in F.FILLER_KINDS:
                    d = build_document(DocSpec(a.length, ladder, level, kind, a.copies, a.seed, a.field), tok)
                    save_document(d, out)
                    print(_summary_row(d))
        print(f"\nsaved to {out}")
        return

    d = build_document(DocSpec(a.length, a.ladder, a.level, a.filler, a.copies, a.seed, a.field), tok)
    path = save_document(d, out)
    print(header)
    print(_summary_row(d))
    print(f"\nQUESTION (no answer in the document): {d['question']}")
    print(f"look-alike value(s) of '{a.field}': {d['lookalike_values']}")
    for rec in d["records"]:
        if rec["role"] == "lookalike":
            s, e = rec["char_start"], rec["char_end"]
            print("\n--- around the look-alike ---")
            print("..." + d["text"][max(0, s - 300):s] + ">>>" + d["text"][s:e] + "<<<" + d["text"][e:e + 300] + "...")
            break
    print(f"\nsaved: {path}  (+ .json metadata)")


if __name__ == "__main__":
    main()
