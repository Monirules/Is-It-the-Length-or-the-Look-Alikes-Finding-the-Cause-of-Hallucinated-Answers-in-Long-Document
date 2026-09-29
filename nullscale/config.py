"""Load the three YAML files in configs/ and check that they agree with each other.

Other code uses it like this:
    from nullscale.config import load_paths, load_models, load_experiments
    P = load_paths()            # profile from NULLSCALE_PROFILE (pc or cluster)
    P["hf_home"], P["data"]["nullscale"], P["outputs"]["answers"]

Run it directly to check everything and print a summary:
    python -m nullscale.config                      # check configs, current profile
    python -m nullscale.config --profile cluster    # check with the cluster paths
    python -m nullscale.config --make-dirs          # also create the data/output folders
    python -m nullscale.config --get hf_home        # print one path (used by setup_env.sh)
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import sys
from itertools import product
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "configs"


# ----------------------------------------------------------------------------- loading

def _read(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def detect_profile() -> str:
    """NULLSCALE_PROFILE wins; otherwise WSL means the PC and anything else means the cluster."""
    env = os.environ.get("NULLSCALE_PROFILE")
    if env:
        return env
    return "pc" if "microsoft" in platform.uname().release.lower() else "cluster"


def _expand(value, mapping: dict):
    if not isinstance(value, str):
        return value
    for key, rep in mapping.items():
        value = value.replace("${%s}" % key, rep)
    return os.path.expanduser(os.path.expandvars(value))


def _walk(obj, mapping):
    if isinstance(obj, dict):
        return {k: _walk(v, mapping) for k, v in obj.items()}
    return _expand(obj, mapping)


def load_paths(profile: str | None = None) -> dict:
    cfg = _read("paths.yaml")
    profile = profile or detect_profile()
    if profile not in cfg["profiles"]:
        raise KeyError(f"profile '{profile}' not in configs/paths.yaml (have: {list(cfg['profiles'])})")
    raw = cfg["profiles"][profile]
    mapping = {"PROJECT_ROOT": str(PROJECT_ROOT)}
    mapping["WORK_ROOT"] = _expand(raw["work_root"], mapping)
    out = _walk(raw, mapping)
    out["profile"] = profile
    out["project_root"] = str(PROJECT_ROOT)
    return out


def load_models() -> dict:
    return _read("models.yaml")


def load_experiments() -> dict:
    return _read("experiments.yaml")


def path_dirs(paths: dict) -> list[str]:
    """Every folder the profile needs."""
    dirs = [paths["work_root"], paths["hf_home"], paths["logs"]]
    dirs += list(paths["data"].values()) + list(paths["outputs"].values())
    return dirs


# ----------------------------------------------------------------------------- counting

def experiment_models(exp: dict, models_cfg: dict) -> list[str]:
    m = exp.get("models", [])
    return list(models_cfg["open_models"]) if m == "all_open" else list(m or [])


def count_experiment(exp: dict, defaults: dict) -> dict:
    """Contexts and answers per model for one experiment (one repeat, temperature 0)."""
    qpc = defaults["questions_per_context"]
    q_per_ctx = qpc["unanswerable"] + qpc["answerable"]
    t = exp["type"]
    if t == "nullscale":
        dims = [exp["lengths"], exp["ladders"], exp["lookalike_levels"],
                exp["lookalike_copies"], exp["filler"]]
        cells = len(list(product(*dims)))
        contexts = cells * exp["contexts_per_cell"]
        return {"cells": cells, "contexts": contexts, "answers": contexts * q_per_ctx}
    if t == "fixes":
        n = sum(exp["n_questions"].values())
        return {"cells": len(exp["versions"]), "contexts": None, "answers": n * len(exp["versions"])}
    if t == "realdata":
        return {"cells": len(exp["settings"]), "contexts": None,
                "answers": exp["n_questions"] * len(exp["settings"])}
    if t == "batching":
        return {"cells": len(exp["modes"]), "contexts": exp["contexts"],
                "answers": exp["contexts"] * q_per_ctx * len(exp["modes"])}
    if t == "reanalysis":
        return {"cells": 0, "contexts": 0, "answers": 0}
    raise ValueError(f"unknown experiment type {t}")


# ----------------------------------------------------------------------------- checking

def check(profile: str | None = None, make_dirs: bool = False) -> int:
    errors, warnings = [], []
    paths = load_paths(profile)
    mcfg = load_models()
    ecfg = load_experiments()
    d = ecfg["defaults"]
    unit = d["length_unit_tokens"]
    tol = d["length_tolerance"]
    head = d["prompt_headroom_tokens"]
    open_models = mcfg["open_models"]

    # models.yaml
    need = ["family", "hf_id", "base_hf_id", "gated", "max_model_len", "pc", "cluster"]
    for k, m in open_models.items():
        for f in need:
            if f not in m:
                errors.append(f"models.yaml: {k} is missing '{f}'")

    # experiments.yaml
    per_model = {k: 0 for k in open_models}
    rows = []
    for name, exp in ecfg["experiments"].items():
        for dim in ("ladders", "lookalike_levels", "filler"):
            bad = set(exp.get(dim, [])) - set(d["allowed"][dim])
            if bad:
                errors.append(f"{name}: unknown {dim} {sorted(bad)}")
        models = experiment_models(exp, mcfg)
        for mk in models:
            if mk not in open_models:
                errors.append(f"{name}: model '{mk}' is not in models.yaml")
        for ak in exp.get("api_models", []):
            if ak not in mcfg.get("api_models", {}):
                errors.append(f"{name}: api model '{ak}' is not in models.yaml")

        c = count_experiment(exp, d)
        lengths = exp.get("lengths", [])
        for mk in models:
            if mk not in open_models:
                continue
            per_model[mk] += c["answers"]
            limit = open_models[mk]["max_model_len"]
            for L in lengths:
                need_tok = int(L * unit * (1 + tol)) + head
                if need_tok > limit:
                    errors.append(f"{name}: {L}K document ({need_tok} tokens with prompt) "
                                  f"does not fit {mk} (max {limit})")

        pc_models = [mk for mk in models if open_models.get(mk, {}).get("pc", {}).get("runnable")]
        pc_lengths = sorted({L for mk in pc_models for L in lengths
                             if L * unit * (1 + tol) + head <= open_models[mk]["pc"]["max_len"]})
        rows.append((name, exp["rq"], exp["type"], c["contexts"], c["answers"], len(models),
                     ",".join(f"{L}K" for L in lengths) or "-",
                     ",".join(f"{L}K" for L in pc_lengths) if pc_models else "-"))

    # paths
    for p in path_dirs(paths):
        if "TODO" in p:
            warnings.append(f"paths.yaml [{paths['profile']}]: still has a TODO -> {p}")
    for k in ("partition", "gpu_type"):
        v = str(paths.get("slurm", {}).get(k, ""))
        if "TODO" in v:
            warnings.append(f"paths.yaml [{paths['profile']}]: slurm.{k} is still TODO")
    if make_dirs:
        for p in path_dirs(paths):
            if "TODO" not in p:
                Path(p).mkdir(parents=True, exist_ok=True)
    root = Path(paths["work_root"])
    probe = next((q for q in [root, *root.parents] if q.exists()), None)
    free_gb = shutil.disk_usage(probe).free / 1e9 if probe else float("nan")

    # ------------------------------------------------------------------ report
    print(f"\nProfile: {paths['profile']}   GPU: {paths.get('gpu')}")
    print(f"  project_root: {paths['project_root']}")
    print(f"  work_root:    {paths['work_root']}   (free disk here: {free_gb:,.0f} GB)")
    print(f"  hf_home:      {paths['hf_home']}")

    print("\nModels")
    print(f"  {'key':<16}{'hf_id':<46}{'gated':<7}{'max_len':>9}{'Roig fab@32K':>14}  PC")
    for k, m in open_models.items():
        fab = "-" if m.get("roig_fab_32k") is None else f"{m['roig_fab_32k']:.2f}%"
        pc = f"FP8, <= {m['pc']['max_len']//1024}K" if m["pc"].get("runnable") else "no"
        print(f"  {k:<16}{m['hf_id']:<46}{str(m['gated']):<7}{m['max_model_len']:>9}{fab:>14}  {pc}")

    print("\nExperiments (answers per model, temperature 0, one repeat)")
    print(f"  {'exp':<6}{'RQ':<17}{'type':<12}{'contexts':>9}{'answers':>9}{'models':>8}  lengths      PC lengths")
    for r in rows:
        ctx = "-" if r[3] is None else r[3]
        print(f"  {r[0]:<6}{r[1]:<17}{r[2]:<12}{ctx:>9}{r[4]:>9}{r[5]:>8}  {r[6]:<12} {r[7]}")
    reps = ecfg["experiments"].get("exp2", {}).get("repeats")
    if reps:
        extra = count_experiment(ecfg["experiments"]["exp2"], d)["answers"] * len(reps["seeds"])
        print(f"  + exp2 repeats at T={reps['temperature']}: {extra} answers per model")

    print("\nAnswers per model (all experiments, excluding repeats)")
    for k, n in per_model.items():
        print(f"  {k:<16}{n:>7,}")

    for w in warnings:
        print(f"WARNING  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print("\nOK: configs are consistent." if not errors else f"\n{len(errors)} error(s).")
    return 1 if errors else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", choices=["pc", "cluster"])
    ap.add_argument("--make-dirs", action="store_true")
    ap.add_argument("--get", metavar="KEY", help="print one top-level path, e.g. hf_home or work_root")
    a = ap.parse_args()
    if a.get:
        print(load_paths(a.profile)[a.get])
        return
    sys.exit(check(a.profile, a.make_dirs))


if __name__ == "__main__":
    main()
