"""riker/download_riker.py

Downloads both RIKER2 zip files, checks that nothing is broken, unpacks the small one, and turns the
big one into one compact answers cache (it holds 3.7 million files; we never unpack all of them).

Steps
  1. download   <riker2>/zips/RIKER2_corpora_groundtruth_testsets.zip   (0.6 MB)
                <riker2>/zips/RIKER2_March2026.zip                      (4.65 GB)
                Resumes an interrupted download. Size is checked against the server.
  2. check      small zip: every file's CRC.  big zip: the directory is complete (entry count), and every
                file we take passes its CRC check while it is read.
  3. unpack     small zip -> <riker2>/groundtruth/   (documents .md, ground truth .db, test sets .yaml)
                big zip   -> <riker2>/raw/riker/*.csv  (Roig's summary tables)
                          -> <riker2>/cache/riker2_answers.jsonl.gz   one line per (run, question):
                             platform, run_name, model, temperature, context_k, run, question_id, level,
                             doc_type, riker_correct, failed, riker_extracted, response (L11, L12, L01-L04)
                          -> <riker2>/cache/runs.csv   one line per run
  4. manifest   <riker2>/manifest.json  (sizes, SHA-256, counts) and a copy in outputs/riker/

<riker2> is paths.yaml data.riker2 (PC: ~/nullscale_work/data/riker2). Needs about 6 GB free.

Usage (Ubuntu/WSL, nullscale env, project folder; no GPU; about 15-40 min, mostly the download)
  python -m riker.download_riker
  python -m riker.download_riker --skip-download        # zips already in <riker2>/zips (e.g. downloaded in a browser)
  python -m riker.download_riker --delete-big-zip       # free 4.65 GB after the cache is built
  python -m riker.download_riker --limit-runs 20        # quick test on 20 runs only
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from riker.common import (BASE_URL, GROUNDING_LEVELS, OUT_DIR, TRAP_LEVELS, ZIPS, LeanZip, cache_path,  # noqa: E402
                          gt_dir, parse_qid, parse_run_name, read_json_bytes, riker_root, write_jsonl_gz)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
KEEP_TEXT_LEVELS = set(TRAP_LEVELS) | set(GROUNDING_LEVELS)
MAX_TEXT = 4000                                          # characters of each reply kept in the cache


# ----------------------------------------------------------------------------- download

def remote_size(url: str) -> int | None:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return int(r.headers.get("Content-Length") or 0) or None
    except Exception as e:
        print(f"  (could not read the size from the server: {e})")
        return None


def download(url: str, dest: Path, retries: int = 8) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = remote_size(url)
    if dest.exists() and total and dest.stat().st_size == total:
        print(f"  already complete: {dest.name} ({total / 1e9:.2f} GB)")
        return
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        have = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": UA}
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r:
                if have and r.status != 206:                 # server ignored the range: start again
                    have = 0
                    part.unlink(missing_ok=True)
                mode = "ab" if have else "wb"
                t0, done, last = time.time(), have, 0.0
                with open(part, mode) as f:
                    while True:
                        buf = r.read(4 << 20)
                        if not buf:
                            break
                        f.write(buf)
                        done += len(buf)
                        if time.time() - last > 5:
                            last = time.time()
                            rate = (done - have) / max(1e-6, last - t0) / 1e6
                            tot = f"/{total / 1e9:.2f}" if total else ""
                            print(f"  {dest.name}: {done / 1e9:.2f}{tot} GB  ({rate:.1f} MB/s)", flush=True)
            if total and part.stat().st_size != total:
                raise IOError(f"got {part.stat().st_size} of {total} bytes")
            part.replace(dest)
            print(f"  done: {dest.name} ({dest.stat().st_size / 1e9:.3f} GB)")
            return
        except Exception as e:
            wait = min(60, 5 * attempt)
            print(f"  attempt {attempt} failed: {e}. Retrying in {wait}s (the download resumes).")
            time.sleep(wait)
    raise SystemExit(f"download failed: {url}\nDownload it in a browser, put it in {dest.parent}, and run with --skip-download.")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for buf in iter(lambda: f.read(16 << 20), b""):
            h.update(buf)
    return h.hexdigest()


# ----------------------------------------------------------------------------- unpack

def unpack_groundtruth(zpath: Path, root: Path) -> dict:
    dest = gt_dir(root)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        bad = z.testzip()
        if bad:
            raise SystemExit(f"{zpath.name} is damaged (first bad file: {bad}). Delete it and download again.")
        files = []
        for info in z.infolist():
            name = info.filename
            if name.endswith("/") or name.startswith("__MACOSX") or Path(name).name.startswith("._") \
                    or Path(name).name == ".DS_Store":
                continue
            target = dest / Path(name).name
            with z.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
            files.append({"name": Path(name).name, "bytes": info.file_size})
    print(f"  unpacked {len(files)} files to {dest}")
    for f in files:
        print(f"    {f['name']:50s} {f['bytes'] / 1e3:9.1f} KB")
    return {"files": files}


def build_cache(zpath: Path, root: Path, limit_runs: int | None) -> dict:
    """Read only scores.json, test_summary.json and the top-level CSVs of the big zip."""
    def keep(name: str) -> bool:
        parts = name.split("/")
        if parts[0] == "__MACOSX":
            return False
        if len(parts) == 2 and name.endswith(".csv"):
            return True
        return len(parts) == 4 and parts[3] in ("scores.json", "test_summary.json")

    t0 = time.time()
    last = [0.0]

    def prog(seen, total):
        if time.time() - last[0] > 10:
            last[0] = time.time()
            print(f"  reading the directory: {seen:,} / {total:,} entries", flush=True)

    print(f"  reading the directory of {zpath.name} (3.7 million entries; 1-3 min)...")
    z = LeanZip(zpath, keep=keep, progress=prog)
    if z.n_seen != z.n_total:
        raise SystemExit(f"directory incomplete: {z.n_seen} of {z.n_total} entries. Download again.")
    print(f"  directory OK: {z.n_total:,} entries; keeping {len(z.entries):,} ({time.time() - t0:.0f}s)")

    # all file names, for the inspect report (counts by kind only)
    raw_dir = root / "raw" / "riker"
    raw_dir.mkdir(parents=True, exist_ok=True)
    csvs = [e for e in z.entries if e[0].count("/") == 1]
    for e in csvs:
        (raw_dir / Path(e[0]).name).write_bytes(z.read(e))
    print(f"  saved {len(csvs)} summary CSVs to {raw_dir}")

    by_run: dict[str, dict] = {}
    for e in z.entries:
        parts = e[0].split("/")
        if len(parts) == 4:
            by_run.setdefault(f"{parts[1]}/{parts[2]}", {})[parts[3]] = e
    run_keys = sorted(by_run)
    if limit_runs:
        run_keys = run_keys[:limit_runs]
    runs_meta, problems = [], Counter()

    def rows():
        for i, key in enumerate(run_keys, 1):
            platform, run_name = key.split("/")
            meta = parse_run_name(run_name)
            files = by_run[key]
            if meta is None:
                problems["run name not understood"] += 1
                continue
            if "scores.json" not in files:
                problems["no scores.json"] += 1
                runs_meta.append({"platform": platform, "run_name": run_name, **meta, "status": "no scores.json"})
                continue
            try:
                sc = read_json_bytes(z.read(files["scores.json"]))
            except Exception as ex:
                problems[f"scores.json unreadable: {type(ex).__name__}"] += 1
                runs_meta.append({"platform": platform, "run_name": run_name, **meta, "status": f"bad: {ex}"})
                continue
            det = sc.get("detailed_results") or []
            md = sc.get("metadata") or {}
            runs_meta.append({"platform": platform, "run_name": run_name, **meta, "status": "ok",
                              "n_questions": len(det), "accuracy_pct": md.get("accuracy_percentage")})
            for d in det:
                qid = d.get("question_id")
                q = parse_qid(qid)
                det_d = d.get("details") or {}
                text = det_d.get("actual_cleaned") or det_d.get("actual_raw") or ""
                # failed = the model produced no reply (crash, timeout, context too long). RIKER2 also fills
                # error_message for ordinary wrong answers ("expected X, got Y"), so it is NOT a failure signal.
                raw = det_d.get("actual_raw") or det_d.get("actual_cleaned") or ""
                failed = not str(raw).strip()
                yield {
                    "platform": platform, "run_name": run_name, "model": meta["model"],
                    "temperature": meta["temperature"], "context_k": meta["context_k"], "run": meta["run"],
                    "question_id": qid, "sample": d.get("sample_number"), "level": q["level"],
                    "doc_type": q["doc_type"], "riker_correct": bool(d.get("correct")), "failed": failed,
                    "error": (d.get("error_message") or "")[:200] or None,
                    "riker_extracted": (det_d.get("actual_extracted") or "")[:300] if q["level"] in KEEP_TEXT_LEVELS else None,
                    "riker_expected": det_d.get("expected"),
                    "response": str(text)[:MAX_TEXT] if q["level"] in KEEP_TEXT_LEVELS else None,
                }
            if i % 200 == 0 or i == len(run_keys):
                print(f"  runs read: {i:,} / {len(run_keys):,} ({time.time() - t0:.0f}s)", flush=True)

    n = write_jsonl_gz(cache_path(root), rows())
    z.close()
    with open(root / "cache" / "runs.csv", "w", newline="", encoding="utf-8") as f:
        keys = ["platform", "run_name", "model", "temperature", "context_k", "run", "stamp", "status",
                "n_questions", "accuracy_pct"]
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(runs_meta)
    ok = [r for r in runs_meta if r.get("status") == "ok"]
    summary = {
        "entries_in_zip": z.n_total, "runs": len(run_keys), "runs_ok": len(ok), "answer_rows": n,
        "models": len({r["model"] for r in ok}), "platforms": sorted({r["platform"] for r in ok}),
        "contexts": dict(Counter(r["context_k"] for r in ok)), "temperatures": dict(Counter(r["temperature"] for r in ok)),
        "problems": dict(problems), "summary_csvs": [Path(e[0]).name for e in csvs],
    }
    print(f"  cache: {n:,} answer rows from {len(ok):,} runs -> {cache_path(root)}")
    if problems:
        print(f"  problems: {dict(problems)}")
    return summary


# ----------------------------------------------------------------------------- main

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="RIKER2 folder (default: paths.yaml data.riker2)")
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--only-groundtruth", action="store_true", help="only the small zip (documents, ground truth, tests)")
    ap.add_argument("--limit-runs", type=int, default=None, help="cache only the first N runs (quick test)")
    ap.add_argument("--delete-big-zip", action="store_true", help="delete RIKER2_March2026.zip after the cache is built")
    ap.add_argument("--no-sha", action="store_true", help="skip the SHA-256 of the big zip (saves ~30 s)")
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else riker_root()
    zdir = root / "zips"
    zdir.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(zdir).free / 1e9
    print(f"RIKER2 folder: {root}  (free disk: {free:.1f} GB)")
    names = ["groundtruth"] if a.only_groundtruth else ["groundtruth", "outputs"]
    if free < 6.5 and not a.only_groundtruth and not (zdir / ZIPS["outputs"]).exists():
        print("WARNING: less than 6.5 GB free; the big zip needs 4.65 GB plus ~0.5 GB for the cache.")

    print("\n[1/4] download")
    for key in names:
        dest = zdir / ZIPS[key]
        if a.skip_download:
            if not dest.exists():
                sys.exit(f"--skip-download but {dest} is missing")
            print(f"  using {dest.name} ({dest.stat().st_size / 1e9:.3f} GB)")
        else:
            download(BASE_URL + ZIPS[key], dest)

    manifest = {"source": BASE_URL, "downloaded": time.strftime("%Y-%m-%d %H:%M"), "zips": {}}
    for key in names:
        p = zdir / ZIPS[key]
        manifest["zips"][ZIPS[key]] = {"bytes": p.stat().st_size,
                                       "sha256": None if (a.no_sha and key == "outputs") else sha256(p)}

    print("\n[2/4] check + unpack the ground truth zip")
    manifest["groundtruth"] = unpack_groundtruth(zdir / ZIPS["groundtruth"], root)

    if not a.only_groundtruth:
        print("\n[3/4] check the big zip and build the answers cache")
        manifest["outputs"] = build_cache(zdir / ZIPS["outputs"], root, a.limit_runs)
        if a.delete_big_zip and not a.limit_runs:
            (zdir / ZIPS["outputs"]).unlink()
            print(f"  deleted {ZIPS['outputs']} (the cache has everything the scripts need)")

    print("\n[4/4] manifest")
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "riker_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  {root / 'manifest.json'}\n  {OUT_DIR / 'riker_manifest.json'}")
    print("\nAll good. Next:  python -m riker.inspect_riker")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
