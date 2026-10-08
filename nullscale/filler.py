"""nullscale/filler.py

Builds the records that fill a document around the question-relevant records.

  unrelated  shipments, equipment and weather logs. Shares no record type, field or entity with
             the business records, so it can never look like the asked item.
  sibling    same-kind business records (leases, companies, people, buildings) about entities no
             question asks about. It "looks like" the domain, but clearly lacks the asked fact:
             it never mentions an asked company, building, stem or reserved generic word.

Both kinds are made with the same World, so their names pass the same similarity registry.

Equal size across filler kinds
  For a given document, assemble.py fixes the NUMBER of filler records N from the length
  budget, then select_to_budget() picks N records from a larger candidate pool so that the
  total token count hits the budget. So the two filler kinds get the same record count and the
  same token count (and, because the templates are balanced, nearly the same word count).

Run  `python -m nullscale.filler`  to compare the two kinds on one budget.
"""
from __future__ import annotations

import bisect
import random

from nullscale import schema as S
from nullscale.records import Record, World

FILLER_KINDS = ("unrelated", "sibling")


def _counts(mix: dict, n: int) -> dict:
    types = list(mix)
    out = {t: int(round(mix[t] * n)) for t in types}
    out[types[0]] += n - sum(out.values())
    return out


def make_pool(world: World, kind: str, n: int) -> list[Record]:
    """n candidate filler records of one kind, in random order."""
    if kind == "unrelated":
        recs = [world.make(t) for t, c in _counts(S.UNRELATED_MIX, n).items() for _ in range(c)]
    elif kind == "sibling":
        c = _counts(S.SIBLING_MIX, n)
        companies = [world.company() for _ in range(max(1, c["company"]))]
        buildings = [world.building() for _ in range(max(1, c["building"]))]
        cnames = [r.get("name") for r in companies]
        bnames = [r.get("name") for r in buildings]
        people = [world.person(employer=world.rng.choice(cnames)) for _ in range(c["person"])]
        leases = [world.lease(tenant=world.rng.choice(cnames), building=world.rng.choice(bnames))
                  for _ in range(c["lease"])]
        recs = companies[:c["company"]] + buildings[:c["building"]] + people + leases
    else:
        raise ValueError(f"unknown filler kind {kind}")
    for r in recs:
        r.role = "filler"
        r.tags = {"filler": kind}
    world.rng.shuffle(recs)
    return recs


def select_to_budget(costs: list[int], n: int, budget: int, rng: random.Random,
                     tol: int, max_iter: int = 20000) -> list[int]:
    """Pick n indices whose costs sum to budget +/- tol, by random start plus greedy swaps."""
    if n > len(costs):
        raise ValueError(f"pool of {len(costs)} is smaller than n={n}")
    chosen = rng.sample(range(len(costs)), n)
    chosen_set = set(chosen)
    total = sum(costs[i] for i in chosen)
    for _ in range(max_iter):
        gap = budget - total
        if abs(gap) <= tol:
            break
        rest = sorted((costs[j], j) for j in range(len(costs)) if j not in chosen_set)
        keys = [c for c, _ in rest]
        best = None
        for pos in rng.sample(range(n), min(n, 40)):
            i = chosen[pos]
            want = costs[i] + gap
            k = bisect.bisect_left(keys, want)
            for kk in (k - 1, k):
                if 0 <= kk < len(rest):
                    c, j = rest[kk]
                    new_gap = abs(gap - (c - costs[i]))
                    if best is None or new_gap < best[0]:
                        best = (new_gap, pos, j)
        if best is None or best[0] >= abs(gap):
            break
        _, pos, j = best
        i = chosen[pos]
        chosen_set.discard(i)
        chosen_set.add(j)
        chosen[pos] = j
        total += costs[j] - costs[i]
    return chosen


def main() -> None:
    from nullscale.assemble import load_tokenizer, ref_record_cost
    from nullscale.render import render
    tok = load_tokenizer()
    budget = 30_000
    n = round(budget / ref_record_cost(tok.name))      # same rule assemble.py uses
    print(f"tokenizer: {tok.name}\nbudget {budget:,} tokens, {n} records per kind\n")
    for kind in FILLER_KINDS:
        w = World(seed=5)
        pool = make_pool(w, kind, int(n * 2.5))
        rrng = random.Random(5)
        texts = [render(r, rrng) for r in pool]
        costs = [c + tok.sep for c in tok.count_many(texts)]
        idx = select_to_budget(costs, n, budget, random.Random(5), tol=budget // 500)
        words = sum(len(texts[i].split()) for i in idx)
        types = {}
        for i in idx:
            types[pool[i].type] = types.get(pool[i].type, 0) + 1
        mix = ", ".join(f"{t} {c / len(idx):.0%}" for t, c in sorted(types.items()))
        print(f"{kind:<10} records {len(idx)}  tokens {sum(costs[i] for i in idx):,}  words {words:,}  mix: {mix}")


if __name__ == "__main__":
    main()
