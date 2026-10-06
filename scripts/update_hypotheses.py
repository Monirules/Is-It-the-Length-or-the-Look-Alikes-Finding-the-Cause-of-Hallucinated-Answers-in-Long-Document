"""scripts/update_hypotheses.py  (owner: Monirul; the change log was Jayden's task)

Step 8: fills the sign-off lines and adds the dated change log at the END of hypotheses.md.
Nothing else in the file is touched. Running it twice does nothing the second time.

Before writing, it checks with git that hypotheses.md is unchanged since the commit that first added it
(3 October 2026, 12:40, before the first H200 run). If the file was changed, it stops and tells you.

Usage (Ubuntu, project folder)
  python scripts/update_hypotheses.py --glm-exp6 pending --strict submitted     # today
  python scripts/update_hypotheses.py --dry-run                                 # show the text, change nothing
Options
  --glm-exp6  pending | done | not-run      status of GLM-4.5-Air on Exp 6
  --strict    submitted | done | not-run    status of the optional strict-prompt baseline
  --date      date written into the log (default: today)
Then commit:  git add hypotheses.md && git commit -m "hypotheses.md: sign-off and change log"
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
H = PROJECT_ROOT / "hypotheses.md"
REVIEW_OLD = "- Reviewed by Monirul: ______________________  Date: __________"
SEEN_OLD = "- Seen by Jayden: ______________________  Date: __________"


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glm-exp6", choices=["pending", "done", "not-run"], default="pending")
    ap.add_argument("--strict", choices=["submitted", "done", "not-run"], default="not-run")
    ap.add_argument("--date", default=f"{date.today():%-d %B %Y}")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    text = H.read_text(encoding="utf-8")
    if "### Change log entry of" in text:
        sys.exit("hypotheses.md already has the change log; nothing to do")

    first = git("log", "--diff-filter=A", "--format=%h %ci", "--", "hypotheses.md")
    if first:
        h = first.split()[0]
        if git("diff", h, "--", "hypotheses.md"):
            sys.exit(f"hypotheses.md differs from commit {h}; it must be unchanged before sign-off. Check: git diff {h} -- hypotheses.md")
        proof = f"commit {first}"
    else:
        proof = "commit of 3 October 2026, 12:40 (git history not found on this machine; check on GitHub)"

    review = (f"- Reviewed by Monirul: M. I. Mahmud  Date: {a.date}. Content unchanged since {proof}, "
              "before the first H200 run (3 October 2026, 16:25).")
    seen = (f"- Seen by Jayden: not signed. Jayden left the project before sign-off; his remaining tasks were "
            f"done by M. I. Mahmud (noted {a.date}).")
    glm = {"pending": "GLM-4.5-Air was not in the first Exp 6 run; its Exp 6 run was submitted on " + a.date + ".",
           "done": "GLM-4.5-Air ran Exp 6 after the other six models (" + a.date + ").",
           "not-run": "GLM-4.5-Air was not run on Exp 6 (no H200 time before the deadline)."}[a.glm_exp6]
    strict = {"submitted": "Added (exploratory, not pre-registered): a strict-prompt run on the Exp 2 documents with a "
                           "strong look-alike, all models, as a baseline to compare with sibling filler. Submitted " + a.date + ".",
              "done": "Added (exploratory, not pre-registered): a strict-prompt run on the Exp 2 documents with a "
                      "strong look-alike, as a baseline to compare with sibling filler.",
              "not-run": ""}[a.strict]
    entries = [
        "Hand check of 300 answers dropped for time. It is replaced by the agreement between our scoring rules and "
        "RIKER2's official scorer: 99.21%, Cohen's kappa 0.981, on 605,948 answers (outputs/riker/refusal_rules_on_riker.md). "
        "The unit tests in tests/test_scoring.py also support the rules. The 'scorer agreement' metric above is reported "
        "from this comparison, not from human checkers.",
        "Exp 5 dropped (no time). RQ4 is answered only from the sibling filler result in Exp 3. The cost comparison "
        "against standard fixes is not done.",
        "The optional API model (Claude Haiku 4.5) was not run.",
        "The regression without Llama 3.3 70B at 128K was added after seeing the data. It is a sensitivity check only, "
        "not the main result. The main result is the regression on all Exp 3 answers.",
        "Gemma 3 27B was not run at 128K. Its window is 131,072 tokens, which cannot hold a 128K document plus the prompt "
        "(Gemma's tokenizer needs about 156K tokens for it). GLM-4.5-Air could hold only 40 of the 80 Exp 3 documents at 128K.",
        glm,
        "Added after seeing the data (Step 9, exploratory): the breaking-length table (first length whose no-look-alike "
        "interval lies fully above the 8K interval), the answer-accuracy check of sibling vs unrelated filler, and a "
        "document-bootstrap interval for the exchange rate.",
        "Jayden left the project. His remaining tasks (this change log, the Exp 1 summary, the results summary) were done "
        "by M. I. Mahmud.",
    ] + ([strict] if strict else [])
    log = [f"### Change log entry of {a.date}", "",
           "Nothing above the sign-off lines was edited. Each change and its reason:", ""]
    log += [f"{i}. {e}" for i, e in enumerate(entries, 1)]
    new = text
    for old, rep in ((REVIEW_OLD, review), (SEEN_OLD, seen)):
        if old not in new:
            sys.exit(f"sign-off line not found exactly as expected:\n  {old}\nfill it by hand, then rerun")
        new = new.replace(old, rep)
    if "## Change log\n\n(none)" in new:
        new = new.replace("## Change log\n\n(none)", "## Change log\n\n" + "\n".join(log))
    else:
        new = new.rstrip("\n") + "\n\n" + "\n".join(log)
    new = new.rstrip("\n") + "\n"
    if a.dry_run:
        print(new[new.index("## Sign-off"):])
        return
    H.write_text(new, encoding="utf-8")
    print(new[new.index("## Sign-off"):])
    print("\nwritten. Commit:  git add hypotheses.md && git commit -m \"hypotheses.md: sign-off and change log\" && git push")


if __name__ == "__main__":
    main()
