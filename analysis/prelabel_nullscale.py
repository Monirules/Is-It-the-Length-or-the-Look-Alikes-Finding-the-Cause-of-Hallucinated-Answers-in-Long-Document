from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REFUSE = re.compile(r"(not (in|mentioned|stated|found|provided|listed|included|specified|available|present|contain)|"
                    r"no (record|information|mention|lease|data|entry)|does not (contain|mention|include|state|specify|appear)|"
                    r"do not (contain|mention|include|state|specify)|cannot (find|be determined|determine)|"
                    r"isn'?t (in|mentioned|listed)|there is no|unable to|NOT FOUND|none of the records)", re.I)
WARN = re.compile(r"\b(however|but|although|though|instead|closest|similar|differ|different|not \d{4}|rather than|"
                  r"typo|spelled|spelling|assum|note that|noting|might|may be|possibly|likely|seems|only|"
                  r"the records (do not|don't)|not the|a different|another)\b", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def value_stated(response: str, value: str) -> bool:
    r = f" {norm(response)} "
    vals = [v for v in re.split(r"\s*\|\s*|;\s*", str(value)) if v.strip()]
    for v in vals:
        n = norm(v)
        if n and f" {n} " in r:
            return True
        digits = re.sub(r"\D", "", v)
        if len(digits) >= 2 and digits in re.sub(r"\D", "", response):
            return True
    return False


def label(row) -> tuple[str, str, str]:
    resp = str(row["response"])
    refuse = bool(REFUSE.search(resp))
    stated = value_stated(resp, row["lookalike_values"])
    warn = bool(WARN.search(resp))
    if refuse and not stated:
        return "R", "refusal phrase, look-alike value not stated", "high"
    if refuse and stated:
        return "W", "refusal phrase and look-alike value both present", "medium"
    if stated and warn:
        return "W", "look-alike value stated with a warning word", "medium"
    if stated:
        return "U", "look-alike value stated without warning", "high"
    if re.search(r"\d", resp) or len(resp.split()) <= 8:
        return "U", "a value is stated that is not the look-alike value", "medium"
    return "O", "no refusal phrase and no clear value", "low"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_nullscale_sheet.csv"))
    ap.add_argument("--key", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_nullscale_key.csv"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_nullscale_prelabeled.csv"))
    a = ap.parse_args(argv)
    s = pd.read_csv(a.sheet, dtype=str, keep_default_na=False)
    lab = s.apply(label, axis=1, result_type="expand")
    s["label"], s["reason"], s["confidence"] = lab[0], lab[1], lab[2]
    s["verified"] = ""
    s = s[["item", "question", "lookalike_values", "response", "label", "confidence", "reason", "verified", "notes"]]
    s.to_csv(a.out, index=False)
    print(s["label"].value_counts().to_string())
    print(s["confidence"].value_counts().to_string())
    k = Path(a.key)
    if k.exists():
        m = s.merge(pd.read_csv(k, dtype=str, keep_default_na=False), on="item")
        print(pd.crosstab(m["auto_label"], m["label"]).to_string())
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
