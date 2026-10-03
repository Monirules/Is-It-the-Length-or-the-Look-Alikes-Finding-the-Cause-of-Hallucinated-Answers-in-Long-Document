"""score/capture_tag.py  (owner: Jayden; written for the team by M. I. Mahmud)

Checks whether a made-up answer COPIED the look-alike record's value. This is the "look-alike capture
rate" in the proposal (Section 9): it shows the cause directly.

Tags for every answer to a question with no answer
  captured            the committed value equals one of the look-alike record's values
                      (lookalike_values in the agreed format; written forms are normalised)
  mentions_lookalike  the look-alike's value appears ANYWHERE in the reply, even as context inside a
                      refusal ("The closest match, Pousquieck Pharma, is on floor 20. Not in the records.")
                      A strict reading of "made up" counts these too; we report them separately.
  source              where a made-up value came from:
                        lookalike       copied from the look-alike record
                        other_record    the value is written somewhere else in the document
                        not_in_document the value is nowhere in the document (invented)
                        unknown         the document text was not available
                        -               not made up

Usage
  from score.capture_tag import capture_tags
  tags = capture_tags(row, label="made_up", values=[...], document_text=None)
"""
from __future__ import annotations

from score.match_answer import KIND, contains_value, normalise_value, same_value, values_of_kind


def capture_tags(row: dict, label: str, values: list | None = None, document_text: str | None = None) -> dict:
    """row: one saved answer. label/values: from score.match_answer.label_row."""
    field = row["field"]
    kind = KIND.get(field, "money")
    response = row.get("response") or ""
    la_vals = [v for v in (row.get("lookalike_values") or []) if v]
    out = {"captured": False, "mentions_lookalike": False, "source": "-"}
    if row.get("answerable"):
        return out
    out["mentions_lookalike"] = any(contains_value(response, v, kind) for v in la_vals)
    if label != "made_up":
        return out
    committed = values if values is not None else values_of_kind(response, kind)
    committed = [_coerce(v, kind) for v in committed]
    la_norm = [normalise_value(v, kind) for v in la_vals]
    out["captured"] = any(same_value(c, t, kind) for c in committed for t in la_norm if t is not None)
    if out["captured"]:
        out["source"] = "lookalike"
    elif document_text is None:
        out["source"] = "unknown"
    else:
        doc_vals = values_of_kind(document_text, kind)
        in_doc = any(same_value(c, d, kind) for c in committed for d in doc_vals)
        out["source"] = "other_record" if in_doc else "not_in_document"
    return out


def _coerce(v, kind):
    """values from label_row are strings; turn them back into comparable values."""
    if kind == "money":
        return float(v)
    if kind == "floor":
        return int(v)
    return str(v)
