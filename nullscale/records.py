"""nullscale/records.py  (owner: Monirul)

Creates fake records with random names, dates and values, with one hard guarantee:
no two names in a document are accidentally similar.

How the guarantee works
  Every name has a distinctive invented "stem" (Morvane in "Morvane Logistics", Okorvel in
  "Dana Okorvel"). The NameRegistry refuses any new stem within edit distance 2 of a stem it
  already holds (so no "one letter apart" or "two letters apart" pairs), and any stem that
  shares its first four letters with one. The only similar names in a document are the
  look-alikes that lookalike.py adds on purpose with force=True.

All randomness comes from one random.Random(seed), so the same seed gives the same world.

Run  `python -m nullscale.records`  for a quick self-check.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import combinations

from nullscale import schema as S


@dataclass
class Record:
    type: str                         # a key of schema.SCHEMA
    fields: dict                      # field name -> python value (str, int, float, date)
    rid: str = ""                     # unique id inside a document
    role: str = "filler"              # filler | entity | witness | lookalike
    tags: dict = field(default_factory=dict)   # extra info, e.g. which ladder/level made it

    def get(self, name, default=None):
        return self.fields.get(name, default)


# ----------------------------------------------------------------------------- similarity

def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalpha())


def _deletions(key: str, depth: int = 2) -> set[str]:
    """All strings obtained by deleting up to `depth` characters. Two strings within edit
    distance 2 always share at least one such string (symmetric-delete trick)."""
    out, frontier = {key}, {key}
    for _ in range(depth):
        nxt = set()
        for w in frontier:
            for i in range(len(w)):
                nxt.add(w[:i] + w[i + 1:])
        out |= nxt
        frontier = nxt
    return out


def edit_distance(a: str, b: str) -> int:
    a, b = _norm(a), _norm(b)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


class NameRegistry:
    """Holds every stem used in one document and rejects near-duplicates."""

    def __init__(self):
        self._stems: set[str] = set()
        self._prefix: set[str] = set()
        self._index: set[str] = set()

    def __len__(self):
        return len(self._stems)

    def __contains__(self, stem: str) -> bool:
        return _norm(stem) in self._stems

    def conflicts(self, stem: str) -> bool:
        k = _norm(stem)
        if k in self._stems or k[:4] in self._prefix:
            return True
        return not self._index.isdisjoint(_deletions(k))

    def add(self, stem: str, force: bool = False) -> None:
        if not force and self.conflicts(stem):
            raise ValueError(f"stem '{stem}' is too similar to one already used")
        k = _norm(stem)
        self._stems.add(k)
        self._prefix.add(k[:4])
        self._index |= _deletions(k)

    def stems(self) -> list[str]:
        return sorted(self._stems)


# ----------------------------------------------------------------------------- invented words

_ONSETS = ["b", "br", "c", "cl", "d", "dr", "f", "fl", "g", "gr", "h", "k", "l", "m", "n", "p", "pr",
           "r", "s", "sk", "st", "t", "tr", "v", "w", "z", "th", "sh", "ch", "qu"]
_VOWELS = ["a", "e", "i", "o", "u", "ai", "ea", "oa", "ou", "ie"]
_CODAS = ["", "", "n", "r", "l", "s", "m", "nd", "rt", "st", "ck", "x", "rn"]


def invent_word(rng: random.Random) -> str:
    while True:
        n = rng.choice([2, 2, 3])
        w = "".join(rng.choice(_ONSETS) + rng.choice(_VOWELS) + rng.choice(_CODAS) for _ in range(n))
        if 5 <= len(w) <= 10:
            return w.capitalize()


# ----------------------------------------------------------------------------- the world

class World:
    """Makes records for one document. Keeps the name registry and all ids unique."""

    def __init__(self, seed: int, optional_rate: float = 0.6):
        self.seed = seed
        self.rng = random.Random(seed)
        self.names = NameRegistry()
        self.optional_rate = optional_rate      # chance that each optional field is present
        self.reserved_generics: set[str] = set()
        self._codes: set[str] = set()
        self._n = 0

    # ---- helpers
    def new_stem(self) -> str:
        for _ in range(10_000):
            w = invent_word(self.rng)
            if not self.names.conflicts(w):
                self.names.add(w)
                return w
        raise RuntimeError("could not find a new distinct stem; registry is saturated")

    def reserve_stem(self, stem: str, force: bool = False) -> str:
        self.names.add(stem, force=force)
        return stem

    def _code(self, prefix: str, digits: int = 5) -> str:
        while True:
            c = f"{prefix}-{self.rng.randrange(10 ** (digits - 1), 10 ** digits)}"
            if c not in self._codes:
                self._codes.add(c)
                return c

    def _rid(self, t: str) -> str:
        self._n += 1
        return f"{t[:3]}{self._n:05d}"

    def _opt(self) -> bool:
        return self.rng.random() < self.optional_rate

    def rand_date(self, y0=2012, y1=2025, year=None) -> date:
        y = year if year is not None else self.rng.randint(y0, y1)
        return date(y, 1, 1) + timedelta(days=self.rng.randrange(365))

    def money(self, lo, hi, step=50) -> int:
        return self.rng.randrange(lo // step, hi // step + 1) * step

    def generic(self) -> str:
        choices = [g for g in S.COMPANY_GENERICS if g not in self.reserved_generics]
        return self.rng.choice(choices)

    def person_name(self) -> str:
        return f"{self.rng.choice(S.FIRST_NAMES)} {self.new_stem()}"

    def company_name(self, generic: str | None = None) -> str:
        return f"{self.new_stem()} {generic or self.generic()}"

    def building_name(self) -> str:
        return f"{self.new_stem()} {self.rng.choice(S.BUILDING_WORDS)}"

    # ---- business records
    def company(self, name: str | None = None) -> Record:
        f = {"name": name or self.company_name(),
             "industry": self.rng.choice(S.INDUSTRIES),
             "founded_year": self.rng.randint(1960, 2018),
             "headquarters": self.rng.choice(S.CITIES),
             "employees": self.rng.randint(12, 4800)}
        if self._opt():
            f["ceo"] = self.person_name()
        if self._opt():
            f["website"] = f"www.{_norm(f['name'].split()[0])}.com"
        return Record("company", f, self._rid("company"))

    def person(self, name: str | None = None, employer: str | None = None) -> Record:
        name = name or self.person_name()
        f = {"name": name,
             "role": self.rng.choice(S.ROLES),
             "employer": employer or self.company_name(),
             "start_year": self.rng.randint(2000, 2024)}
        first, last = name.split(" ", 1)
        if self._opt():
            f["email"] = f"{first[0].lower()}.{_norm(last)}@{_norm(f['employer'].split()[0])}.com"
        if self._opt():
            f["phone"] = f"({self.rng.randint(201, 989)}) 555-{self.rng.randint(1000, 9999)}"
        return Record("person", f, self._rid("person"))

    def building(self, name: str | None = None) -> Record:
        f = {"name": name or self.building_name(),
             "address": f"{self.rng.randint(10, 2999)} {self.new_stem()} {self.rng.choice(S.STREET_WORDS)}",
             "city": self.rng.choice(S.CITIES),
             "floors": self.rng.randint(2, 38),
             "year_built": self.rng.randint(1925, 2021)}
        if self._opt():
            f["manager"] = self.person_name()
        if self._opt():
            f["parking_spaces"] = self.rng.randint(8, 600)
        return Record("building", f, self._rid("building"))

    def lease(self, tenant: str | None = None, building: str | None = None,
              start_year: int | None = None, floor: int | None = None) -> Record:
        start = self.rand_date(2012, 2024, year=start_year)
        years = self.rng.choice([2, 3, 5, 7, 10])
        rent = self.money(1800, 48000)
        f = {"lease_id": self._code("L"),
             "tenant": tenant or self.company_name(),
             "building": building or self.building_name(),
             "floor": floor if floor is not None else self.rng.randint(1, 30),
             "start_date": start,
             "end_date": date(start.year + years, start.month, min(start.day, 28)),
             "monthly_rent": rent}
        if self._opt():
            f["deposit"] = self.money(rent, rent * 3)
        if self._opt():
            f["signed_by"] = self.person_name()
        if self._opt():
            f["renewal_option"] = self.rng.choice(S.RENEWAL_OPTIONS)
        return Record("lease", f, self._rid("lease"))

    # ---- unrelated records
    def shipment(self) -> Record:
        o, d = self.rng.sample(S.CITIES, 2)
        f = {"tracking_code": self._code("SH", 6),
             "carrier": f"{self.new_stem()} {self.rng.choice(S.CARRIER_WORDS)}",
             "origin": o, "destination": d,
             "weight_kg": round(self.rng.uniform(2, 950), 1),
             "ship_date": self.rand_date(2015, 2025),
             "contents": self.rng.choice(S.CONTENTS),
             "packages": self.rng.randint(1, 240),
             "priority": self.rng.choice(S.PRIORITIES)}
        if self._opt():
            f["insured_value"] = self.money(200, 60000)
        return Record("shipment", f, self._rid("shipment"))

    def equipment(self) -> Record:
        f = {"asset_tag": self._code("EQ"),
             "model": f"{self.new_stem()} {self.rng.randint(100, 990)}",
             "category": self.rng.choice(S.EQUIPMENT_CATEGORIES),
             "purchase_year": self.rng.randint(2008, 2025),
             "room": f"room {self.rng.randint(1, 9)}{self.rng.randint(0, 40):02d}",
             "condition": self.rng.choice(S.CONDITIONS),
             "serial_number": f"SN{self.rng.randrange(10**7, 10**8)}",
             "warranty_until": self.rng.randint(2024, 2031)}
        if self._opt():
            f["last_service"] = self.rand_date(2019, 2025)
        return Record("equipment", f, self._rid("equipment"))

    def weather(self) -> Record:
        hi = round(self.rng.uniform(-8, 36), 1)
        f = {"station": f"{self.new_stem()} {self.rng.choice(S.STATION_WORDS)}",
             "date": self.rand_date(2015, 2025),
             "high_c": hi,
             "low_c": round(hi - self.rng.uniform(3, 14), 1),
             "precipitation_mm": round(self.rng.choice([0, 0, 0.4, 2.5, 8.0, 21.0]) * self.rng.uniform(0.5, 1.5), 1),
             "sky": self.rng.choice(S.SKIES),
             "humidity_pct": self.rng.randint(18, 99),
             "visibility_km": round(self.rng.uniform(0.4, 30), 1)}
        if self._opt():
            f["wind_kmh"] = self.rng.randint(0, 70)
        return Record("weather", f, self._rid("weather"))

    def make(self, rtype: str) -> Record:
        return getattr(self, rtype)()


# ----------------------------------------------------------------------------- self-check

def main() -> None:
    w = World(seed=7)
    recs = [w.make(t) for t in ["company", "person", "building", "lease"] * 150]
    stems = w.names.stems()
    sample = stems[:600]
    min_d = min(edit_distance(a, b) for a, b in combinations(sample, 2))
    print(f"records made: {len(recs)}   distinct name stems: {len(stems)}")
    print(f"smallest edit distance between any two of {len(sample)} stems: {min_d}  (must be >= 3)")
    print("example stems:", ", ".join(stems[:12]))
    assert min_d >= 3, "similarity guarantee broken"
    print("OK")


if __name__ == "__main__":
    main()
