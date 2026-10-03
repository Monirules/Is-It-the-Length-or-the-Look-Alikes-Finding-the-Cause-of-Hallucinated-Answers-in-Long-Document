"""run/run_vllm.py  (owner: Monirul)

Loads one model with vLLM, asks every question of the chosen documents ONE QUESTION PER CALL, and
saves every answer in the agreed format. Works the same on the PC (RTX 5070, FP8) and the cluster.

Reusing the document (prefix caching)
  All 12 questions of a document share the same prompt prefix (the document comes first, see
  run/prompts.py). For each document we send the first question alone, so vLLM computes the
  document once and caches it, then send the other 11 together; they reuse the cached document.
  Every saved answer records `cached_prompt_tokens`, so the reuse is visible in the data.

Output (one JSON line per answer, appended after every document, so an interrupted run resumes):
  <paths.outputs.answers>/<exp>/<model>/<prompt>_t<temp>_s<seed>.jsonl
  <same name>.meta.json   settings, versions, timings for the run

Answer format (one line per question). Keep in sync with the format in README.md:
  run_id, qid, exp, doc_id, probe_id, model, hf_id, profile, quantization, prompt_style,
  prompt_version, temperature, top_p, seed, max_tokens, question, answerable, field, ladder, level,
  copies, filler, length_k, gold, gold_aliases, lookalike_values, response, finish_reason,
  truncated, n_prompt_tokens, cached_prompt_tokens, n_output_tokens, call_id, call_size,
  call_seconds, batch_index, timestamp, vllm_version

Usage (Ubuntu, nullscale env, project folder). Needs the GPU; the dataset must be built.
  python -m run.run_vllm --model qwen3_4b --exp exp2 --n-docs 20 --balanced
  python -m run.run_vllm --model qwen3_4b --exp exp7 --prompt batch12
  python -m run.run_vllm --model qwen3_4b --exp exp2 --n-docs 2 --dry-run    # no GPU: show what would run
  # several GPUs at once (data parallel): one process per GPU, each answers every 4th document
  CUDA_VISIBLE_DEVICES=0 python -m run.run_vllm --model qwen3_4b --exp exp3 --shard 0 --num-shards 4 &
  ...  then:  python -m run.merge_shards --exp exp3 --model qwen3_4b
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import sys
import time
from collections import OrderedDict, defaultdict
from pathlib import Path

from nullscale.config import load_experiments, load_models, load_paths
from run.prompts import build_batch_messages, build_messages, parse_batch_answer, prompt_version

COPY_FIELDS = ("qid", "exp", "doc_id", "probe_id", "question", "answerable", "field", "ladder", "level",
               "copies", "filler", "length_k", "gold", "gold_aliases", "lookalike_values")
EXP6_FIELDS = ("source", "setting", "nq_id", "true_answers")      # Exp 6 only (Wikipedia documents)


# ----------------------------------------------------------------------------- data

def load_questions(data_root: Path, exp: str) -> list[dict]:
    path = data_root / exp / "questions.jsonl"
    if not path.exists():
        sys.exit(f"No dataset at {path}.\nBuild it first:  python -m nullscale.build_dataset --exp {exp}")
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def select_documents(questions: list[dict], n_docs: int | None, balanced: bool,
                     lengths: set[int] | None, levels: set[str] | None) -> "OrderedDict[str, list[dict]]":
    """Group questions by document, filter, and pick n_docs documents. balanced=True takes documents
    round-robin across (ladder, level, filler, copies) cells so a small run still covers every cell."""
    by_doc: "OrderedDict[str, list[dict]]" = OrderedDict()
    for q in questions:
        if lengths and q["length_k"] not in lengths:
            continue
        if levels and q["level"] not in levels:
            continue
        by_doc.setdefault(q["doc_id"], []).append(q)
    ids = list(by_doc)
    if balanced:
        cells: "OrderedDict[tuple, list[str]]" = OrderedDict()
        for d in ids:
            q0 = by_doc[d][0]
            cells.setdefault((q0["length_k"], q0["ladder"], q0["level"], q0["filler"], q0["copies"]), []).append(d)
        # order the cells so that any partial round is spread out: cells whose (ladder + level + ...)
        # index sum is even come first, e.g. name-none, role-weak, name-medium, role-strong, then the rest.
        # 20 documents over 8 cells then give every level 5 documents and every ladder 10.
        order = {"name": 0, "role": 1, "none": 0, "weak": 1, "medium": 2, "strong": 3, "unrelated": 0, "sibling": 1}
        def parity(key):
            return sum(order.get(v, v if isinstance(v, int) else 0) for v in key[1:]) % 2
        cells = OrderedDict(sorted(cells.items(), key=lambda kv: (parity(kv[0]), kv[0][0],
                                                                  order.get(kv[0][2], 0), order.get(kv[0][1], 0))))
        ids, k = [], 0
        while any(k < len(v) for v in cells.values()):
            ids += [v[k] for v in cells.values() if k < len(v)]
            k += 1
    if n_docs:
        ids = ids[:n_docs]
    return OrderedDict((d, sorted(by_doc[d], key=lambda q: q["order"])) for d in ids)


def read_document(data_root: Path, q: dict) -> str:
    return (data_root / q["doc_path"]).read_text(encoding="utf-8")


# ----------------------------------------------------------------------------- engine

def engine_settings(model_key: str, profile: str, max_model_len: int, gpu_mem: float | None,
                    eager: bool | None) -> tuple[dict, dict]:
    """vLLM LLM(...) keyword arguments and a description for the model on this profile."""
    models = load_models()["open_models"]
    if model_key not in models:
        sys.exit(f"unknown model '{model_key}'. Choose from: {', '.join(models)}")
    m = models[model_key]
    kw = {"model": m["hf_id"], "max_model_len": max_model_len, "enable_prefix_caching": True, "seed": 0}
    kw.update(m.get("vllm_args") or {})
    if profile == "pc":
        if not m["pc"].get("runnable"):
            sys.exit(f"{model_key} does not fit on the PC GPU; run it on the cluster.")
        kw["quantization"] = m["pc"]["quantization"]
        kw["kv_cache_dtype"] = m["pc"].get("kv_cache_dtype", "auto")
        kw["gpu_memory_utilization"] = gpu_mem or 0.80
        kw["enforce_eager"] = True if eager is None else eager
        backend = os.environ.get("NULLSCALE_ATTENTION_BACKEND") or m["pc"].get("attention_backend")
        if backend:
            kw["attention_backend"] = backend
        quant = f"{m['pc']['quantization']} (PC)"
    else:
        gpu_type = (os.environ.get("NULLSCALE_GPU_TYPE") or "h200").lower()
        tp = m["cluster"].get(f"tp_{gpu_type}", m["cluster"].get("tp_h200", 1))
        if os.environ.get("NULLSCALE_TP"):
            tp = int(os.environ["NULLSCALE_TP"])
        kw["tensor_parallel_size"] = tp
        kw["gpu_memory_utilization"] = gpu_mem or 0.90
        if eager:
            kw["enforce_eager"] = True
        quant = m["cluster"].get("dtype", "bfloat16")
    return kw, {"hf_id": m["hf_id"], "quantization": quant,
                "chat_template_kwargs": m.get("chat_template_kwargs") or {}}


def make_llm(kw: dict):
    """Create vllm.LLM, dropping any keyword this vLLM version does not accept (and saying so).

    The attention backend has had different names across vLLM versions. We set it three ways:
    the environment variable (older versions), attention_backend=..., and, if that keyword is
    refused, attention_config={"backend": ...}. The log line "Using ... attention backend" shows
    which one took effect."""
    from vllm import LLM
    kw = dict(kw)
    backend = kw.get("attention_backend")
    if backend:
        os.environ.setdefault("VLLM_ATTENTION_BACKEND", backend)     # inherited by the engine process
        if backend != "FLASHINFER":
            os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    for _ in range(len(kw) + 2):
        try:
            return LLM(**kw)
        except TypeError as e:
            bad = next((k for k in list(kw) if f"'{k}'" in str(e)), None)
            if bad is None or bad == "model":
                raise
            print(f"[run_vllm] this vLLM does not accept {bad}={kw[bad]!r}; continuing without it")
            val = kw.pop(bad)
            if bad == "attention_backend":
                kw["attention_config"] = {"backend": val}
                print(f"[run_vllm] trying attention_config={{'backend': {val!r}}} instead")
    raise RuntimeError("could not construct vllm.LLM")


def count_prompt_tokens(tokenizer, messages: list[dict], chat_kwargs: dict) -> int:
    ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, **chat_kwargs)
    if hasattr(ids, "keys"):                       # newer transformers return a dict-like object
        ids = ids["input_ids"]
    if ids and isinstance(ids[0], list):
        ids = ids[0]
    return len(ids)


def run_chat(llm, messages_list: list, params, chat_kwargs: dict):
    kwargs = {"use_tqdm": False}
    if chat_kwargs:
        kwargs["chat_template_kwargs"] = chat_kwargs
    try:
        return llm.chat(messages_list, params, **kwargs)
    except TypeError:
        kwargs.pop("use_tqdm", None)
        return llm.chat(messages_list, params, **kwargs)


# ----------------------------------------------------------------------------- answering

def _row(q: dict, base: dict, out, response: str, call: dict, batch_index=None) -> dict:
    o = out.outputs[0]
    fin = getattr(o, "finish_reason", None)
    row = {"run_id": base["run_id"]}
    row.update({k: q.get(k) for k in COPY_FIELDS})
    if q.get("source") == "wikipedia":
        row.update({k: q.get(k) for k in EXP6_FIELDS})
    row.update({k: base[k] for k in ("model", "hf_id", "profile", "quantization", "prompt_style", "prompt_version",
                                     "temperature", "top_p", "seed", "max_tokens", "vllm_version")})
    row.update({
        "response": response, "finish_reason": fin, "truncated": fin == "length",
        "n_prompt_tokens": len(getattr(out, "prompt_token_ids", None) or []),
        "cached_prompt_tokens": getattr(out, "num_cached_tokens", None),
        "n_output_tokens": len(getattr(o, "token_ids", None) or []),
        "call_id": call["id"], "call_size": call["size"], "call_seconds": round(call["seconds"], 3),
        "batch_index": batch_index,
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
    })
    return row


def answer_document(llm, doc_text: str, qs: list[dict], style: str, params, chat_kwargs: dict,
                    base: dict, call_counter: list) -> tuple[list[dict], dict]:
    """All questions of one document. Returns (rows, timing)."""
    rows, timing = [], {}
    if style == "batch12":
        msgs = build_batch_messages(doc_text, [q["question"] for q in qs])
        t = time.perf_counter()
        out = run_chat(llm, [msgs], params, chat_kwargs)[0]
        sec = time.perf_counter() - t
        call_counter[0] += 1
        call = {"id": call_counter[0], "size": 1, "seconds": sec}
        answers = parse_batch_answer(out.outputs[0].text, len(qs))
        for i, (q, a) in enumerate(zip(qs, answers)):
            r = _row(q, base, out, a, call, batch_index=i)
            r["raw_batch_response"] = out.outputs[0].text if i == 0 else None
            rows.append(r)
        return rows, {"first_seconds": sec, "rest_seconds": 0.0}

    msgs = [build_messages(doc_text, q["question"], style, q.get("source", "records")) for q in qs]
    # 1) first question alone: computes and caches the document
    t = time.perf_counter()
    first = run_chat(llm, [msgs[0]], params, chat_kwargs)
    t1 = time.perf_counter() - t
    call_counter[0] += 1
    rows.append(_row(qs[0], base, first[0], first[0].outputs[0].text, {"id": call_counter[0], "size": 1, "seconds": t1}))
    # 2) the other questions together: they reuse the cached document
    t2 = 0.0
    if len(qs) > 1:
        t = time.perf_counter()
        rest = run_chat(llm, msgs[1:], params, chat_kwargs)
        t2 = time.perf_counter() - t
        call_counter[0] += 1
        call = {"id": call_counter[0], "size": len(qs) - 1, "seconds": t2}
        rows += [_row(q, base, o, o.outputs[0].text, call) for q, o in zip(qs[1:], rest)]
    return rows, {"first_seconds": t1, "rest_seconds": t2}


# ----------------------------------------------------------------------------- main

def output_path(answers_root: Path, exp: str, model: str, style: str, temperature: float, seed: int) -> Path:
    return answers_root / exp / model / f"{style}_t{temperature:g}_s{seed}.jsonl"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="key from configs/models.yaml, e.g. qwen3_4b")
    ap.add_argument("--exp", required=True, help="exp2, exp3, exp4, exp5 or exp7")
    ap.add_argument("--prompt", default="normal", choices=["normal", "strict", "batch12"])
    ap.add_argument("--n-docs", type=int, default=None, help="only this many documents")
    ap.add_argument("--balanced", action="store_true", help="spread the documents over every cell")
    ap.add_argument("--lengths", default=None, help="only these lengths, e.g. 8,32")
    ap.add_argument("--levels", default=None, help="only these look-alike levels, e.g. none,strong")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=None, help="default 256 (1024 for batch12)")
    ap.add_argument("--gpu-mem", type=float, default=None, help="GPU memory share for vLLM (PC default 0.80)")
    ap.add_argument("--eager", action="store_true", default=None, help="disable CUDA graphs (PC default)")
    ap.add_argument("--profile", choices=["pc", "cluster"], default=None)
    ap.add_argument("--data", default=None, help="dataset root (default: paths.yaml data.nullscale)")
    ap.add_argument("--out", default=None, help="answers root (default: paths.yaml outputs.answers)")
    ap.add_argument("--fresh", action="store_true", help="start a new file instead of resuming")
    ap.add_argument("--dry-run", action="store_true", help="show what would run; no model is loaded")
    ap.add_argument("--shard", type=int, default=0, help="data parallel: which part this process answers (0-based)")
    ap.add_argument("--num-shards", type=int, default=1, help="data parallel: number of parts (one per GPU group); "
                    "merge afterwards with python -m run.merge_shards")
    a = ap.parse_args(argv)

    paths = load_paths(a.profile)
    profile = paths["profile"]
    exp_type = (load_experiments().get("experiments", {}).get(a.exp) or {}).get("type")
    default_root = paths["data"]["nq"] if exp_type == "realdata" else paths["data"]["nullscale"]
    data_root = Path(a.data or default_root)
    answers_root = Path(a.out or paths["outputs"]["answers"])
    max_tokens = a.max_tokens or (1024 if a.prompt == "batch12" else 256)
    lengths = {int(x) for x in a.lengths.split(",")} if a.lengths else None
    levels = set(a.levels.split(",")) if a.levels else None

    docs = select_documents(load_questions(data_root, a.exp), a.n_docs, a.balanced, lengths, levels)
    if not docs:
        sys.exit("no documents match the filters")
    main_path = output_path(answers_root, a.exp, a.model, a.prompt, a.temperature, a.seed)
    out_path = main_path
    if a.num_shards > 1:
        # data parallel: this process answers every num_shards-th document (stable split of the full list)
        if not 0 <= a.shard < a.num_shards:
            sys.exit("--shard must be between 0 and --num-shards - 1")
        docs = OrderedDict(list(docs.items())[a.shard::a.num_shards])
        out_path = main_path.with_name(f"{main_path.stem}.part{a.shard}of{a.num_shards}.jsonl")
    done = set()
    if not a.fresh:
        # answers already saved in the main file or in ANY shard file of this run (resume across splits)
        for p in [main_path, *main_path.parent.glob(f"{main_path.stem}.part*of*.jsonl"),
                  *(main_path.parent / "parts").glob(f"{main_path.stem}.part*of*.jsonl")]:
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    done |= {json.loads(line)["qid"] for line in f if line.strip()}
    todo = OrderedDict((d, qs) for d, qs in docs.items() if not all(q["qid"] in done for q in qs))
    n_q = sum(len(v) for v in docs.values())
    print(f"model {a.model} | profile {profile} | {a.exp} | prompt {a.prompt} | T={a.temperature} seed={a.seed}")
    print(f"{len(docs)} documents, {n_q} questions; {len(docs) - len(todo)} documents already answered")
    print(f"answers -> {out_path}")
    if not todo:
        print("nothing to do")
        return {"out_path": str(out_path), "docs": 0}

    # prompt length: measured with the model's tokenizer after loading; start from a safe estimate
    longest = max(q["length_k"] for qs in todo.values() for q in qs)
    est_len = int(longest * 1000 * 1.12) + 1500 + max_tokens
    if a.dry_run:
        first_doc, qs = next(iter(todo.items()))
        text = read_document(data_root, qs[0])
        msg = (build_batch_messages(text, [q["question"] for q in qs]) if a.prompt == "batch12"
               else build_messages(text, qs[0]["question"], a.prompt, qs[0].get("source", "records")))[0]["content"]
        print(f"\n[dry run] first document {first_doc}: {len(text):,} characters; prompt tail:\n"
              + msg[-600:])
        print(f"\n[dry run] questions of that document:")
        for q in qs:
            print(f"   {q['probe_id']}  {'ANSWER ' + q['gold'] if q['answerable'] else 'no answer':<22} {q['question']}")
        kw, _ = engine_settings(a.model, profile, est_len, a.gpu_mem, a.eager)
        print(f"\n[dry run] vLLM settings: {kw}")
        return {"out_path": str(out_path), "docs": 0}

    import vllm
    from vllm import SamplingParams

    # size the context to what these documents need (measured with THIS model's tokenizer)
    from transformers import AutoTokenizer
    m_cfg = load_models()["open_models"][a.model]
    tok = AutoTokenizer.from_pretrained(m_cfg["hf_id"])
    chat_kwargs = m_cfg.get("chat_template_kwargs") or {}
    need = 0
    limit = m_cfg["pc"]["max_len"] if profile == "pc" else m_cfg["max_model_len"]
    skipped = []
    for doc_id, qs in list(todo.items()):
        text = read_document(data_root, qs[0])
        if a.prompt == "batch12":
            m = build_batch_messages(text, [q["question"] for q in qs])
        else:
            m = build_messages(text, max(qs, key=lambda q: len(q["question"]))["question"], a.prompt,
                               qs[0].get("source", "records"))
        n_tok = count_prompt_tokens(tok, m, chat_kwargs)
        if n_tok + max_tokens + 64 > limit and profile != "pc":
            # cluster: a document longer than the model's window is skipped and listed, never cut
            skipped.append({"doc_id": doc_id, "length_k": qs[0]["length_k"], "prompt_tokens": n_tok, "limit": limit})
            del todo[doc_id]
            continue
        need = max(need, n_tok)
    if skipped:
        print(f"SKIPPED {len(skipped)} documents that do not fit {a.model}'s {limit:,}-token window "
              f"(lengths {sorted({s['length_k'] for s in skipped})}K); listed in the .meta.json and .skipped.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.with_suffix(".skipped.json").write_text(json.dumps(skipped, indent=1), encoding="utf-8")
    if not todo:
        print("nothing left to run")
        return {"out_path": str(out_path), "docs": 0, "skipped": skipped}
    max_len = need + max_tokens + 64
    if max_len > limit and profile == "pc":
        sys.exit(f"the longest prompt needs {max_len:,} tokens but the PC limit for {a.model} is {limit:,}.")
    max_len = min(max_len, m_cfg["max_model_len"])
    print(f"longest prompt {need:,} tokens -> max_model_len {max_len:,}")

    kw, info = engine_settings(a.model, profile, max_len, a.gpu_mem, a.eager)
    t0 = time.perf_counter()
    llm = make_llm(kw)
    load_s = time.perf_counter() - t0
    print(f"model loaded in {load_s:.0f}s")
    params = SamplingParams(temperature=a.temperature, top_p=a.top_p, max_tokens=max_tokens, seed=a.seed)

    run_id = f"{a.model}-{a.exp}-{a.prompt}-t{a.temperature:g}-s{a.seed}-{dt.datetime.now():%Y%m%d%H%M%S}"
    base = {"run_id": run_id, "model": a.model, "hf_id": info["hf_id"], "profile": profile,
            "quantization": info["quantization"], "prompt_style": a.prompt,
            "prompt_version": prompt_version(next(iter(todo.values()))[0].get("source", "records")),
            "temperature": a.temperature, "top_p": a.top_p, "seed": a.seed, "max_tokens": max_tokens,
            "vllm_version": getattr(vllm, "__version__", "?")}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    per_doc, calls, t_run = [], [0], time.perf_counter()
    with open(out_path, "a" if not a.fresh else "w", encoding="utf-8") as f:
        for i, (doc_id, qs) in enumerate(todo.items(), 1):
            qs = [q for q in qs if q["qid"] not in done]
            text = read_document(data_root, qs[0])
            rows, tm = answer_document(llm, text, qs, a.prompt, params, chat_kwargs, base, calls)
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.flush()
            cached = [r["cached_prompt_tokens"] for r in rows[1:] if r["cached_prompt_tokens"] is not None]
            per_doc.append({"doc_id": doc_id, "length_k": qs[0]["length_k"], "n_questions": len(qs),
                            "prompt_tokens": rows[0]["n_prompt_tokens"], **tm,
                            "mean_cached_tokens_rest": (sum(cached) / len(cached)) if cached else None})
            el = time.perf_counter() - t_run
            print(f"  [{i}/{len(todo)}] {doc_id}: first {tm['first_seconds']:.1f}s, other {len(qs) - 1} "
                  f"{tm['rest_seconds']:.1f}s | elapsed {el / 60:.1f} min, ~{el / i * (len(todo) - i) / 60:.1f} min left")

    meta = {"run_id": run_id, "argv": sys.argv, "settings": {k: v for k, v in kw.items()},
            "base": base, "load_seconds": load_s, "run_seconds": time.perf_counter() - t_run,
            "n_documents": len(per_doc), "n_answers": sum(d["n_questions"] for d in per_doc),
            "skipped_too_long": skipped,
            "per_document": per_doc, "host": platform.node(), "python": sys.version.split()[0],
            "finished": dt.datetime.now().isoformat(timespec="seconds")}
    try:
        import torch
        meta["gpu"] = torch.cuda.get_device_name(0)
    except Exception:
        meta["gpu"] = None
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"done: {meta['n_answers']} answers in {meta['run_seconds'] / 60:.1f} min -> {out_path}")
    return {"out_path": str(out_path), "meta_path": str(meta_path), "docs": len(per_doc), "llm": llm}


if __name__ == "__main__":        # required: vLLM on WSL starts workers that re-import this file
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
