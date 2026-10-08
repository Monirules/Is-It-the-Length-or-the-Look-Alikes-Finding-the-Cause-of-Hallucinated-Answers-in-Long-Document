"""nullscale/schema.py

The fake world NullScale documents are written about.

Two families of record types:

* BUSINESS records (company, person, building, lease). The questions are about these, and the
  look-alike records and the "sibling" filler are made of them.
* UNRELATED records (shipment, equipment, weather). They share no fields or entities with the
  business records and form the "unrelated" filler.

Every field is marked required or optional. Optional fields are left out of some records on
purpose, so a record can exist while one of its facts does not (Roig's L12 "absent optional
field" questions).

Run  `python -m nullscale.schema`  to print the schema.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    name: str
    kind: str              # stem_name | ref | date | year | money | int | choice | text | code | float
    optional: bool = False
    ref: str | None = None  # record type this field points to, for kind == "ref"
    note: str = ""


# ----------------------------------------------------------------------------- business family

COMPANY = [
    Field("name", "stem_name", note="invented stem + generic word, e.g. 'Morvane Logistics'"),
    Field("industry", "choice"),
    Field("founded_year", "year"),
    Field("headquarters", "choice", note="city"),
    Field("employees", "int"),
    Field("ceo", "ref", optional=True, ref="person"),
    Field("website", "text", optional=True),
]

PERSON = [
    Field("name", "stem_name", note="real first name + invented last name"),
    Field("role", "choice"),
    Field("employer", "ref", ref="company"),
    Field("start_year", "year"),
    Field("email", "text", optional=True),
    Field("phone", "text", optional=True),
]

BUILDING = [
    Field("name", "stem_name", note="invented stem + building word, e.g. 'Talbrick Court'"),
    Field("address", "text"),
    Field("city", "choice"),
    Field("floors", "int"),
    Field("year_built", "year"),
    Field("manager", "ref", optional=True, ref="person"),
    Field("parking_spaces", "int", optional=True),
]

LEASE = [
    Field("lease_id", "code"),
    Field("tenant", "ref", ref="company"),
    Field("building", "ref", ref="building"),
    Field("floor", "int"),
    Field("start_date", "date"),
    Field("end_date", "date"),
    Field("monthly_rent", "money"),
    Field("deposit", "money", optional=True),
    Field("signed_by", "ref", optional=True, ref="person"),
    Field("renewal_option", "choice", optional=True),
]

# ----------------------------------------------------------------------------- unrelated family

SHIPMENT = [
    Field("tracking_code", "code"),
    Field("carrier", "stem_name", note="invented stem + 'Freight' etc."),
    Field("origin", "choice"),
    Field("destination", "choice"),
    Field("weight_kg", "float"),
    Field("ship_date", "date"),
    Field("contents", "choice"),
    Field("packages", "int"),
    Field("priority", "choice"),
    Field("insured_value", "money", optional=True),
]

EQUIPMENT = [
    Field("asset_tag", "code"),
    Field("model", "stem_name", note="invented stem + model number"),
    Field("category", "choice"),
    Field("purchase_year", "year"),
    Field("room", "text"),
    Field("condition", "choice"),
    Field("serial_number", "code"),
    Field("warranty_until", "year"),
    Field("last_service", "date", optional=True),
]

WEATHER = [
    Field("station", "stem_name", note="invented stem + 'Station'"),
    Field("date", "date"),
    Field("high_c", "float"),
    Field("low_c", "float"),
    Field("precipitation_mm", "float"),
    Field("sky", "choice"),
    Field("humidity_pct", "int"),
    Field("visibility_km", "float"),
    Field("wind_kmh", "int", optional=True),
]

SCHEMA: dict[str, list[Field]] = {
    "company": COMPANY, "person": PERSON, "building": BUILDING, "lease": LEASE,
    "shipment": SHIPMENT, "equipment": EQUIPMENT, "weather": WEATHER,
}
BUSINESS_TYPES = ("company", "person", "building", "lease")
UNRELATED_TYPES = ("shipment", "equipment", "weather")

# Filler mix: which record types each filler kind draws from, and how often.
SIBLING_MIX = {"lease": 0.45, "company": 0.20, "person": 0.20, "building": 0.15}
UNRELATED_MIX = {"shipment": 0.40, "equipment": 0.30, "weather": 0.30}

# Facts a question can ask about: (record type, field). Lease facts are the main targets.
QUERYABLE = [
    ("lease", "monthly_rent"), ("lease", "deposit"), ("lease", "start_date"), ("lease", "end_date"),
    ("lease", "floor"), ("company", "employees"), ("company", "founded_year"),
    ("building", "year_built"), ("person", "role"),
]

# ----------------------------------------------------------------------------- value pools

INDUSTRIES = ["logistics", "software", "food wholesale", "architecture", "biotechnology", "textiles",
              "insurance", "furniture", "consulting", "printing", "renewable energy", "medical devices",
              "publishing", "legal services", "catering", "robotics", "marine supply", "optics"]

# Company generic words. The generic word of an asked company is reserved, so filler never shares it.
COMPANY_GENERICS = ["Logistics", "Holdings", "Partners", "Analytics", "Foods", "Textiles", "Systems",
                    "Dynamics", "Outfitters", "Laboratories", "Consulting", "Printworks", "Robotics",
                    "Optics", "Supply", "Media", "Interiors", "Engineering", "Traders", "Studios",
                    "Brewing", "Pharma", "Networks", "Ventures"]
BUILDING_WORDS = ["Court", "Tower", "Plaza", "House", "Center", "Commons", "Place", "Exchange", "Yard",
                  "Point", "Square", "Hall"]
STREET_WORDS = ["Street", "Avenue", "Road", "Lane", "Boulevard", "Drive"]
CITIES = ["Columbus", "Dayton", "Pittsburgh", "Louisville", "Indianapolis", "Milwaukee", "Richmond",
          "Raleigh", "Omaha", "Tulsa", "Boise", "Spokane", "Albany", "Hartford", "Madison", "Toledo",
          "Knoxville", "Lexington", "Des Moines", "Wichita", "Syracuse", "Fresno", "Tacoma", "Savannah"]
ROLES = ["operations manager", "chief financial officer", "facilities director", "senior accountant",
         "head of procurement", "general counsel", "office manager", "lead engineer",
         "human resources director", "sales director", "compliance officer", "project coordinator"]
FIRST_NAMES = ["Amara", "Daniel", "Priya", "Tomas", "Leila", "Marcus", "Ingrid", "Kenji", "Sofia",
               "Andre", "Hannah", "Ravi", "Elena", "Samuel", "Yara", "Oliver", "Mei", "Jonas", "Farah",
               "Lucas", "Nadia", "Victor", "Chloe", "Isaac", "Zara", "Felix", "Grace", "Omar", "Ruth",
               "Emil", "Tessa", "Hugo", "Leah", "Mateo", "Nora", "Arjun", "Ivy", "Caleb", "Dina", "Theo"]
RENEWAL_OPTIONS = ["one five-year term", "two three-year terms", "one two-year term", "one year at a time"]
CONTENTS = ["machine parts", "packaged coffee", "ceramic tiles", "lab glassware", "bicycle frames",
            "printer toner", "cotton fabric", "solar panels", "medical gloves", "paper stock",
            "hand tools", "frozen fish"]
EQUIPMENT_CATEGORIES = ["projector", "laser printer", "server rack", "3D printer", "microscope",
                        "forklift", "espresso machine", "label printer", "oscilloscope", "air purifier"]
CONDITIONS = ["good", "fair", "needs repair", "like new"]
SKIES = ["clear", "overcast", "light rain", "fog", "scattered clouds", "snow showers", "thunderstorms"]
CARRIER_WORDS = ["Freight", "Cargo", "Express", "Haulage", "Shipping"]
STATION_WORDS = ["Station", "Observatory", "Weather Post"]
PRIORITIES = ["standard", "express", "economy", "overnight"]


def main() -> None:
    for family, types in (("BUSINESS", BUSINESS_TYPES), ("UNRELATED", UNRELATED_TYPES)):
        print(f"\n{family} records")
        for t in types:
            print(f"  {t}")
            for f in SCHEMA[t]:
                opt = "optional" if f.optional else "required"
                ref = f" -> {f.ref}" if f.ref else ""
                note = f"   ({f.note})" if f.note else ""
                print(f"    {f.name:<16}{f.kind:<10}{opt}{ref}{note}")
    print("\nQueryable facts:", ", ".join(f"{t}.{f}" for t, f in QUERYABLE))


if __name__ == "__main__":
    main()
