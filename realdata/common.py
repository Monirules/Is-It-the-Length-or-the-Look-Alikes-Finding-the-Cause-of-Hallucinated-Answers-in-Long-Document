"""realdata/common.py  (shared helpers for Exp 6)

Answer matching (does a passage HOLD the answer?) and a small, fast BM25 index.

Answer matching follows the standard open-domain QA convention (SQuAD / DPR "has_answer"):
lower case, remove punctuation and the articles a / an / the, collapse spaces, then look for the
answer as a whole-word sequence. "1,000" and "1000" match; "Lincoln" does not match "Lincolnshire".
"""
from __future__ import annotations

import gzip
import json
import math
import re
import string
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "outputs" / "realdata"            # small reports, shared through git

_PUNCT = set(string.punctuation) | {"‘", "’", "“", "”", "–", "—", "…"}
_ARTICLES = re.compile(r"\b(a|an|the)\b")


def normalize(s: str) -> str:
    s = (s or "").lower().replace(",", "")                 # 1,000 -> 1000 before punctuation becomes a space
    s = "".join(" " if ch in _PUNCT else ch for ch in s)
    s = _ARTICLES.sub(" ", s)
    return " ".join(s.split())


def holds_answer(text: str, answers: list[str], title: str = "") -> bool:
    """True if the text (or title) contains any answer as whole words."""
    hay = f" {normalize(title)} {normalize(text)} "
    for a in answers:
        na = normalize(a)
        if na and f" {na} " in hay:
            return True
    return False


def usable_answers(answers: list[str]) -> list[str]:
    """Answers that can be searched for safely: at least 2 characters after normalising, and not a bare
    one- or two-digit number (those appear in almost every passage)."""
    out = []
    for a in answers:
        na = normalize(a)
        if len(na) < 2 or re.fullmatch(r"\d{1,2}", na):
            continue
        out.append(a)
    return out


def read_jsonl_gz(path: Path):
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    op = gzip.open if str(path).endswith(".gz") else open
    n = 0
    with op(path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


# ----------------------------------------------------------------------------- BM25

_STOP = set("""a an the of in on at to for from by with and or but is are was were be been being it its this that
these those as which who whom whose what when where why how do does did has have had not no yes i you he she they
we his her their our your my me him them us there here than then so if into over under about after before during
s""".split())
_TOK = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return [t for t in _TOK.findall((text or "").lower()) if t not in _STOP]


class BM25:
    """Okapi BM25 (k1=0.9, b=0.4, the Pyserini defaults) over a sparse matrix. Scores 650,000 passages
    for one query in well under a second, with a few hundred MB of memory."""

    def __init__(self, texts, k1: float = 0.9, b: float = 0.4, progress=None):
        import numpy as np
        from scipy import sparse
        vocab: dict[str, int] = {}
        indptr, indices, data, lens = [0], [], [], []
        for i, t in enumerate(texts):
            c = Counter(tokens(t))
            for w, n in c.items():
                j = vocab.setdefault(w, len(vocab))
                indices.append(j)
                data.append(n)
            indptr.append(len(indices))
            lens.append(sum(c.values()))
            if progress and i % 100000 == 0:
                progress(i)
        n_docs = len(lens)
        tf = sparse.csr_matrix((np.asarray(data, dtype=np.float32), np.asarray(indices, dtype=np.int32),
                                np.asarray(indptr, dtype=np.int64)), shape=(n_docs, len(vocab)))
        dl = np.asarray(lens, dtype=np.float32)
        avg = float(dl.mean()) if n_docs else 1.0
        df = np.bincount(tf.indices, minlength=len(vocab)).astype(np.float32)
        self.idf = np.log(1 + (n_docs - df + 0.5) / (df + 0.5)).astype(np.float32)
        # pre-compute the BM25 term weight of every (doc, term) entry, then store by column for fast queries
        norm = k1 * (1 - b + b * dl / avg)
        rows = np.repeat(np.arange(n_docs), np.diff(tf.indptr))
        w = tf.data * (k1 + 1) / (tf.data + norm[rows])
        self.W = sparse.csc_matrix((w.astype(np.float32), (rows, tf.indices)), shape=tf.shape)
        self.vocab = vocab
        self.n_docs = n_docs

    def scores(self, query: str):
        import numpy as np
        ids = [self.vocab[t] for t in set(tokens(query)) if t in self.vocab]
        if not ids:
            return np.zeros(self.n_docs, dtype=np.float32)
        sub = self.W[:, ids]
        return np.asarray(sub @ self.idf[ids]).ravel()

    def top(self, query: str, k: int):
        import numpy as np
        s = self.scores(query)
        k = min(k, len(s))
        idx = np.argpartition(-s, k - 1)[:k]
        idx = idx[np.argsort(-s[idx])]
        return [(int(i), float(s[i])) for i in idx]


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)
