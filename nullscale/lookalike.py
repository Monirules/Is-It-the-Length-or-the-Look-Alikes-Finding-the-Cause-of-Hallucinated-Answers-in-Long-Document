"""nullscale/lookalike.py  (owner: Monirul)

Builds the look-alike records for one unanswerable question, at four levels on two ladders.
The question always asks about a lease fact that is NOT in the document; the look-alike is a
real lease record that resembles what is asked.

NAME LADDER: the asked company does not exist anywhere in the document.
  Asked: "What monthly rent does Morvane Logistics pay under its lease?"
    none    no lease resembles it (and no filler company shares its stem or its generic word)
    weak    a lease for another company with the same generic word     -> Talbrick Logistics
    medium  a lease for a company with the same stem, other generic    -> Morvane Holdings
    strong  a lease for a company one letter away, same generic word   -> Morvanne Logistics

ROLE LADDER: the asked company and building both exist (profile records are in the document),
but the asked lease (company X at building Y, starting in year T) does not.
  Asked: "What was the monthly rent of Morvane Logistics's lease at Talbrick Court that started in 2019?"
    none    no lease involves X or Y
    weak    a lease at Y, for another company                          (building matches)
    medium  a lease of X, at another building, starting in T           (company and year match)
    strong  a lease of X at Y, starting in a different year            (only the year differs)

copies = k gives k interchangeable look-alikes of the same level (Exp 4): k one-letter variants,
k other generic words, k other buildings, k other years, and so on.

Run  `python -m nullscale.lookalike`  to print both ladders at all four levels.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from nullscale import schema as S
from nullscale.records import Record, World, edit_distance

LEVELS = ("none", "weak", "medium", "strong")
LADDERS = ("name", "role")

QUESTION = {
    "name": {
        "monthly_rent": "What monthly rent does {tenant} pay under its lease?",
        "deposit": "How large was the security deposit on {tenant_pos} lease?",
        "start_date": "On what date did {tenant_pos} lease begin?",
        "end_date": "On what date does {tenant_pos} lease end?",
        "floor": "Which floor does {tenant} lease?",
    },
    "role": {
        "monthly_rent": "What was the monthly rent of {tenant_pos} lease at {building} that started in {year}?",
        "deposit": "How large was the security deposit on {tenant_pos} lease at {building} that started in {year}?",
        "end_date": "When does {tenant_pos} lease at {building} that started in {year} end?",
        "floor": "Which floor did {tenant} lease at {building} under the lease that started in {year}?",
    },
}

_VOWELS = "aeiou"


def possessive(name: str) -> str:
    return name + ("'" if name.endswith("s") else "'s")


@dataclass
class Case:
    ladder: str
    level: str
    copies: int
    field: str
    question: str
    target: dict                                          # what is asked (does not exist)
    lookalikes: list[Record] = field(default_factory=list)
    entities: list[Record] = field(default_factory=list)  # records that must be in the document

    def lookalike_values(self) -> list:
        """Value of the asked field in each look-alike (what a 'captured' wrong answer would copy)."""
        return [r.get(self.field) for r in self.lookalikes]


def one_edit_variants(stem: str, rng: random.Random, k: int, avoid: list[str] = ()) -> list[str]:
    """k distinct spellings exactly one edit away from stem (never touching the first letter),
    each at least 3 edits away from every stem in `avoid` (the other probes' asked stems)."""
    s = stem.lower()
    cands = set()
    for i in range(1, len(s)):
        c = s[i]
        if c in _VOWELS:                                   # swap a vowel
            for v in _VOWELS:
                if v != c:
                    cands.add(s[:i] + v + s[i + 1:])
        else:                                              # double a consonant
            cands.add(s[:i] + c + s[i:])
        if 1 <= i < len(s) - 1:                            # drop an inner letter
            cands.add(s[:i] + s[i + 1:])
    from nullscale.records import _BLOCKED
    cands = sorted(w for w in cands if w != s and edit_distance(w, s) == 1 and not any(b in w for b in _BLOCKED)
                   and all(edit_distance(w, a) >= 3 for a in avoid if a.lower() != s))
    if len(cands) < k:
        raise ValueError(f"only {len(cands)} one-edit variants of {stem}")
    return [w.capitalize() for w in rng.sample(cands, k)]


def make_case(world: World, ladder: str, level: str, copies: int = 1,
              field: str = "monthly_rent", probe_id: str = "u0", generic: str | None = None) -> Case:
    if ladder not in LADDERS or level not in LEVELS:
        raise ValueError(f"unknown ladder/level {ladder}/{level}")
    if field not in QUESTION[ladder]:
        raise ValueError(f"field {field} not supported on the {ladder} ladder")
    rng = world.rng
    k = 0 if level == "none" else copies
    las: list[Record] = []

    if ladder == "name":
        stem = world.new_stem()
        world.asked_stems.append(stem)
        generic = generic or world.generic()
        world.reserved_generics.add(generic)               # filler companies never use this word
        tenant = f"{stem} {generic}"
        target = {"probe_id": probe_id, "tenant": tenant, "stem": stem, "generic": generic, "field": field}
        if level == "weak":
            las = [world.lease(tenant=world.company_name(generic=generic)) for _ in range(k)]
        elif level == "medium":
            # any word except the asked ones (all asked words are reserved up front by questions.py)
            others = rng.sample([g for g in S.COMPANY_GENERICS if g not in world.reserved_generics], k)
            las = [world.lease(tenant=f"{stem} {g}") for g in others]
        elif level == "strong":
            for v in one_edit_variants(stem, rng, k, avoid=world.asked_stems):
                world.reserve_stem(v, force=True)
                las.append(world.lease(tenant=f"{v} {generic}"))
        question = QUESTION["name"][field].format(tenant=tenant, tenant_pos=possessive(tenant))
        entities: list[Record] = []

    else:  # role ladder
        x = world.company()
        y = world.building()
        year = rng.randint(2014, 2022)
        tenant, building = x.get("name"), y.get("name")
        target = {"probe_id": probe_id, "tenant": tenant, "building": building, "start_year": year, "field": field}
        if level == "weak":
            las = [world.lease(building=building, start_year=rng.choice([t for t in range(2012, 2025) if t != year]))
                   for _ in range(k)]
        elif level == "medium":
            las = [world.lease(tenant=tenant, start_year=year) for _ in range(k)]
        elif level == "strong":
            near = [t for t in range(year - 9, year + 10) if t != year and 2006 <= t <= 2026]
            years = sorted(near, key=lambda t: (abs(t - year), rng.random()))[:k]   # closest other years first
            las = [world.lease(tenant=tenant, building=building, start_year=t) for t in years]
        question = QUESTION["role"][field].format(tenant=tenant, tenant_pos=possessive(tenant),
                                                  building=building, year=year)
        entities = [x, y]
        for r in entities:
            r.role = "entity"
            r.tags = {"probe_id": probe_id}

    for r in las:
        r.role = "lookalike"
        r.tags = {"ladder": ladder, "level": level, "probe_id": probe_id}
        if field == "deposit" and field not in r.fields:     # asked optional field must exist in the look-alike
            r.fields[field] = world.money(r.get("monthly_rent"), r.get("monthly_rent") * 3)
    return Case(ladder, level, copies, field, question, target, las, entities)


def main() -> None:
    from nullscale.render import render
    rrng = random.Random(3)
    for ladder in LADDERS:
        print(f"\n==================== {ladder.upper()} LADDER ====================")
        for level in LEVELS:
            case = make_case(World(seed=42), ladder, level)
            print(f"\n[{level}]  Q: {case.question}")
            if not case.lookalikes:
                print("    (no look-alike record in the document)")
            for r in case.lookalikes:
                print("    LOOK-ALIKE: " + render(r, rrng))
    case = make_case(World(seed=42), "name", "strong", copies=4)
    print("\n[name/strong, copies=4]  Q:", case.question)
    for r in case.lookalikes:
        print("    tenant:", r.get("tenant"), "  rent:", r.get("monthly_rent"))


if __name__ == "__main__":
    main()
