"""scripts/check_token_lengths.py

Document lengths are defined in Llama 3.1 tokens (configs/experiments.yaml, reference_tokenizer).
Other models split text differently. Qwen, for example, splits every digit into its own token, so
the same document is longer for it. This script measures, for EVERY model, how many of its own
tokens the longest prompt at each length needs, and whether that fits the model's context window
(and the PC limit). No GPU needed; it only downloads the tokenizers (a few MB each).

Output: a table on screen and outputs/timing/token_lengths.md

Run (Ubuntu, nullscale env, project folder):
  python scripts/check_token_lengths.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nullscale.config import load_models, load_paths  # noqa: E402
from run import run_vllm as R  # noqa: E402
from run.prompts import build_messages  # noqa: E402

HEADROOM = 256 + 64          # answer tokens + safety


def main() -> None:
    from transformers import AutoTokenizer
    data = Path(load_paths()["data"]["nullscale"])
    qs = R.load_questions(data, "exp3")
    samples = {}
    for L in (8, 32, 64, 128):
        docs = R.select_documents(qs, None, False, {L}, None)
        doc_qs = next(iter(docs.values()))
        q = max(doc_qs, key=lambda x: len(x["question"]))
        samples[L] = build_messages(R.read_document(data, doc_qs[0]), q["question"], "normal")

    models = load_models()["open_models"]
    rows, ref = [], {}
    for key, m in models.items():
        try:
            tok = AutoTokenizer.from_pretrained(m["hf_id"])
        except Exception as e:
            print(f"{key}: could not load tokenizer ({type(e).__name__}); skipped")
            continue
        kw = m.get("chat_template_kwargs") or {}
        counts = {L: R.count_prompt_tokens(tok, msgs, kw) for L, msgs in samples.items()}
        if key == "llama31_8b":
            ref = counts
        rows.append((key, m, counts))
        print(f"  measured {key}")

    head = ("| model | window | " + " | ".join(f"{L}K prompt" for L in samples) + " | fits 128K? | PC limit |")
    lines = ["# Prompt length in each model's own tokens", "",
             "Documents are sized in Llama 3.1 tokens. Numbers are the longest normal prompt at each length "
             f"(+{HEADROOM} for the answer must fit the window).", "", head,
             "|" + "---|" * (len(samples) + 4)]
    problems = []
    for key, m, c in rows:
        cells = []
        for L in samples:
            ratio = f" ({c[L] / ref[L]:.2f}x)" if ref else ""
            ok = c[L] + HEADROOM <= m["max_model_len"]
            cells.append(f"{c[L]:,}{ratio}" + ("" if ok else " **TOO LONG**"))
            if not ok:
                problems.append(f"{key}: {L}K needs {c[L] + HEADROOM:,} tokens, window is {m['max_model_len']:,}")
        pc = ""
        if m["pc"].get("runnable"):
            ok32 = c[32] + HEADROOM <= m["pc"]["max_len"]
            pc = f"{m['pc']['max_len']:,} " + ("ok for 32K" if ok32 else f"**raise to >= {c[32] + HEADROOM:,}**")
            if not ok32:
                problems.append(f"{key}: PC limit {m['pc']['max_len']:,} < {c[32] + HEADROOM:,} needed at 32K")
        lines.append(f"| {key} | {m['max_model_len']:,} | " + " | ".join(cells) +
                     f" | {'yes' if c[128] + HEADROOM <= m['max_model_len'] else '**no**'} | {pc} |")
    lines += ["", "## Problems" if problems else "## No problems", ""] + [f"- {p}" for p in problems]
    out = PROJECT_ROOT / "outputs" / "timing"
    out.mkdir(parents=True, exist_ok=True)
    (out / "token_lengths.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nsaved: {out / 'token_lengths.md'}")


if __name__ == "__main__":
    main()
