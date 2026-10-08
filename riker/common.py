"""riker/common.py  (shared helpers for the RIKER2 scripts)

What RIKER2 contains (checked on 2026-10-03 by reading both zip files' directories directly):

  RIKER2_corpora_groundtruth_testsets.zip   (0.6 MB; 9 files + macOS junk)
      {32K,128K,200K}_riker_<date>_concatenated.md   the FULL document text the models read: every
                                                     lease / field report / HR report, each between
                                                     "=== LEASE: lease_0000.md ===" and "=== END OF ... ===" lines
      {32K,128K,200K}_riker_<date>.db                SQLite ground truth: lease_documents, field_reports,
                                                     hr_reports, entity pools (pool_lessees, ...)
      {32K,128K,200K}_riker_<date>.yaml              the test set: question_id, template (the question),
                                                     scoring_type, expected_response
  RIKER2_March2026.zip                       (4.65 GB; 3.7 million files)
      riker/*.csv                            Roig's summary tables (e.g. 32k_summary.csv, fabrication_pct)
      riker/<platform>/<run>/scores.json     per question: correct, actual_raw (the model's reply),
                                             actual_extracted (its "Final answer"), error_message
      riker/<platform>/<run>/responses.jsonl, precheck.jsonl, test_summary.json, conversations/...
      <run> = temp<T>_<ctx>k_riker_<model>_run<n>_<YYYYMMDD_HHMMSS>, e.g.
              temp0_4_32k_riker_qwen3_4b_instruct_2507_run5_20251226_032812

Question ids: <doc_type>_L<level>_T<template>_<n>, doc_type = lease_document | field_report | hr.
Trap questions (no answer exists): L11 = a person who does not exist (expected N/A, Unknown or NONE),
L12 = a real record whose optional field is absent (expected N/A or NONE). Roig's "fabrication" is the
error rate on L11 and L12.

The big zip is never fully unpacked (3.7 million files). download_riker.py reads its directory, takes
only scores.json + test_summary.json + the summary CSVs, and writes one compact cache:
    <riker2>/cache/riker2_answers.jsonl.gz      one line per (run, question)
"""
from __future__ import annotations

import gzip
import io
import json
import re
import sqlite3
import struct
import zlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "outputs" / "riker"            # small results, shared through git

BASE_URL = "https://research.kamiwaza.ai/HowMuchDoLLMsHallucinateInDocQA/"
ZIPS = {
    "groundtruth": "RIKER2_corpora_groundtruth_testsets.zip",
    "outputs": "RIKER2_March2026.zip",
}
CONTEXTS = (32, 128, 200)
TRAP_LEVELS = ("L11", "L12")
GROUNDING_LEVELS = ("L01", "L02", "L03", "L04")
RUN_RE = re.compile(r"^temp(?P<t1>\d+)_(?P<t2>\d+)_(?P<ctx>\d+)k_riker_(?P<model>.+?)_run(?P<run>\d+)_(?P<stamp>\d{8}_\d{6})$")
QID_RE = re.compile(r"^(?P<doc_type>lease_document|field_report|hr)_(?P<level>L\d\d)_T(?P<template>\d+)_(?P<n>\d+)$")


# ----------------------------------------------------------------------------- folders

def riker_root() -> Path:
    try:
        from nullscale.config import load_paths
        return Path(load_paths()["data"]["riker2"])
    except Exception:
        return Path.home() / "nullscale_work" / "data" / "riker2"


def gt_dir(root: Path) -> Path:
    return root / "groundtruth"


def cache_path(root: Path) -> Path:
    return root / "cache" / "riker2_answers.jsonl.gz"


def parse_run_name(name: str) -> dict | None:
    m = RUN_RE.match(name)
    if not m:
        return None
    return {"temperature": float(f"{int(m['t1'])}.{m['t2']}"), "context_k": int(m["ctx"]), "model": m["model"],
            "run": int(m["run"]), "stamp": m["stamp"]}


def parse_qid(qid: str) -> dict:
    m = QID_RE.match(qid or "")
    return m.groupdict() if m else {"doc_type": None, "level": None, "template": None, "n": None}


# ----------------------------------------------------------------------------- ground truth files

def corpus_files(root: Path, context_k: int) -> dict:
    """{'md','db','yaml'} paths for one context length (None if missing)."""
    g = gt_dir(root)
    out = {}
    for key, pat in (("md", f"{context_k}K_riker_*_concatenated.md"), ("db", f"{context_k}K_riker_*.db"),
                     ("yaml", f"{context_k}K_riker_*.yaml")):
        hits = sorted(p for p in g.rglob(pat) if "__MACOSX" not in p.parts and not p.name.startswith("._"))
        out[key] = hits[0] if hits else None
    return out


def load_tests(yaml_path: Path) -> list[dict]:
    import yaml
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    tests = data.get("tests", data) if isinstance(data, dict) else data
    for t in tests:
        t["prompt"] = t.get("template") or ""                        # RIKER calls the full question "template"
        t["question"] = clean_question(t["prompt"])
        q = parse_qid(t.get("question_id"))
        t["template_no"] = q.pop("template")
        t.update(q)
    return tests


def clean_question(template: str) -> str:
    """The question without RIKER's answer-format instructions."""
    return re.split(r"\s+(?:Reply|Or reply|Respond|If not explicitly|Indicate your final answer)\b", template)[0].strip()


def load_db(db_path: Path) -> dict[str, list[dict]]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    out = {}
    for (name,) in con.execute("select name from sqlite_master where type='table'"):
        out[name] = [dict(r) for r in con.execute(f'select * from "{name}"')]
    con.close()
    return out


DOC_HEADER = re.compile(r"^=== (?P<kind>LEASE|FIELD REPORT|HR REPORT): (?P<file>\S+?)(?:\.md)? ===\s*$", re.M)


def split_corpus(md_text: str) -> dict[str, dict]:
    """doc_id -> {'start','end','text','kind'} from the concatenated markdown."""
    heads = list(DOC_HEADER.finditer(md_text))
    docs = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md_text)
        docs[h["file"]] = {"start": h.start(), "end": end, "text": md_text[h.start():end], "kind": h["kind"]}
    return docs


# ----------------------------------------------------------------------------- the big zip, read lean

class LeanZip:
    """Reads a (zip64) archive's central directory in chunks and keeps only the entries we want.
    Python's zipfile would build 3.7 million ZipInfo objects (several GB of RAM); this keeps ~8,000."""

    def __init__(self, path: Path, keep=lambda name: True, progress=None):
        self.path = Path(path)
        self.f = open(self.path, "rb")
        self.size = self.path.stat().st_size
        self.entries: list[tuple[str, int, int, int, int, int]] = []   # name, method, csize, usize, offset, crc
        self.n_total, self.cd_size = self._read_eocd()
        self._scan(keep, progress)

    def _read_eocd(self) -> tuple[int, int]:
        tail = min(self.size, 65557 + 20 + 56)
        self.f.seek(self.size - tail)
        buf = self.f.read(tail)
        e = buf.rfind(b"PK\x05\x06")
        if e < 0:
            raise ValueError(f"{self.path.name}: end of central directory not found (file cut off?)")
        n, cd_size, cd_off = struct.unpack("<HII", buf[e + 10:e + 20])
        loc = buf.rfind(b"PK\x06\x07", 0, e)
        if loc >= 0:                                                  # zip64
            (z64_off,) = struct.unpack("<Q", buf[loc + 8:loc + 16])
            self.f.seek(z64_off)
            z = self.f.read(56)
            if z[:4] != b"PK\x06\x06":
                raise ValueError("bad zip64 end record")
            n, cd_size, cd_off = struct.unpack("<QQQ", z[32:56])
        self.cd_off = cd_off
        return n, cd_size

    def _scan(self, keep, progress) -> None:
        self.f.seek(self.cd_off)
        remaining = self.cd_size
        buf = b""
        seen = 0
        chunk = 64 << 20
        while remaining > 0 or len(buf) >= 46:
            if remaining > 0 and len(buf) < (1 << 20):
                data = self.f.read(min(chunk, remaining))
                remaining -= len(data)
                buf += data
            p = 0
            while p + 46 <= len(buf):
                if buf[p:p + 4] != b"PK\x01\x02":
                    raise ValueError(f"central directory damaged at entry {seen}")
                (meth,) = struct.unpack("<H", buf[p + 10:p + 12])
                crc, cs, us, fl, el, cl = struct.unpack("<IIIHHH", buf[p + 16:p + 34])
                (lo,) = struct.unpack("<I", buf[p + 42:p + 46])
                end = p + 46 + fl + el + cl
                if end > len(buf):
                    break
                name = buf[p + 46:p + 46 + fl].decode("utf-8", "replace")
                seen += 1
                if keep(name):
                    q, qe = p + 46 + fl, p + 46 + fl + el
                    while q + 4 <= qe:
                        hid, hsz = struct.unpack("<HH", buf[q:q + 4])
                        if hid == 1:
                            k = q + 4
                            if us == 0xFFFFFFFF:
                                (us,) = struct.unpack("<Q", buf[k:k + 8]); k += 8
                            if cs == 0xFFFFFFFF:
                                (cs,) = struct.unpack("<Q", buf[k:k + 8]); k += 8
                            if lo == 0xFFFFFFFF:
                                (lo,) = struct.unpack("<Q", buf[k:k + 8]); k += 8
                        q += 4 + hsz
                    self.entries.append((name, meth, cs, us, lo, crc))
                p = end
            buf = buf[p:]
            if progress:
                progress(seen, self.n_total)
            if remaining <= 0 and p == 0:
                break
        self.n_seen = seen

    def read(self, entry) -> bytes:
        name, meth, cs, us, lo, crc = entry
        self.f.seek(lo)
        h = self.f.read(30)
        if h[:4] != b"PK\x03\x04":
            raise ValueError(f"{name}: bad local header")
        fl, el = struct.unpack("<HH", h[26:30])
        self.f.seek(lo + 30 + fl + el)
        raw = self.f.read(cs)
        if meth == 0:
            data = raw
        elif meth == 8:
            data = zlib.decompress(raw, -15)
        else:
            raise ValueError(f"{name}: compression method {meth} not supported")
        if zlib.crc32(data) & 0xFFFFFFFF != crc:
            raise ValueError(f"{name}: CRC check failed (file damaged)")
        return data

    def close(self):
        self.f.close()


# ----------------------------------------------------------------------------- answers cache

def iter_cache(root: Path, levels=None, contexts=None):
    p = cache_path(root)
    if not p.exists():
        raise SystemExit(f"no answers cache at {p}. Run: python -m riker.download_riker")
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if levels and r["level"] not in levels:
                continue
            if contexts and r["context_k"] not in contexts:
                continue
            yield r


def iter_run_answers(root: Path, levels=TRAP_LEVELS, limit_runs: int | None = None):
    """Rows from the cache (one per run x question), optionally only the first N runs."""
    runs = set()
    for r in iter_cache(root, levels=levels):
        key = (r["platform"], r["run_name"])
        if limit_runs and key not in runs and len(runs) >= limit_runs:
            continue
        runs.add(key)
        yield r


def write_jsonl_gz(path: Path, rows) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_json_bytes(data: bytes):
    return json.load(io.TextIOWrapper(io.BytesIO(data), encoding="utf-8"))
