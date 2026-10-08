"""nullscale/render.py

Turns each record into ordinary written text.

* Every record type has at least three main templates (chosen at random per record) plus
  one or more wordings for each optional field.
* A fact appears in the text if and only if the field is present in the record. Main
  templates use exactly the required fields; an optional field adds its own sentence
  only when present. absence_check.py relies on this.
* No model is involved: the same record and seed always give the same text.

Run  `python -m nullscale.render`  to print 10 readable fake records.
"""
from __future__ import annotations

import random
from datetime import date

from nullscale import schema as S
from nullscale.records import Record, World


def fmt_date(d: date) -> str:
    return f"{d:%B} {d.day}, {d.year}"


def fmt_money(v: int) -> str:
    return f"${v:,}"


def _values(r: Record) -> dict:
    out = {}
    for k, v in r.fields.items():
        if isinstance(v, date):
            out[k] = fmt_date(v)
        elif k in ("monthly_rent", "deposit", "insured_value"):
            out[k] = fmt_money(v)
        elif isinstance(v, int) and k in ("employees", "parking_spaces"):
            out[k] = f"{v:,}"
        else:
            out[k] = str(v)
    return out


# ----------------------------------------------------------------------------- templates

MAIN = {
    "lease": [
        "Lease {lease_id}. {tenant} leases space on floor {floor} of {building}. The term runs from "
        "{start_date} to {end_date}, and the monthly rent is {monthly_rent}.",
        "Under lease {lease_id}, {tenant} occupies floor {floor} at {building} from {start_date} until "
        "{end_date}. Rent is set at {monthly_rent} per month.",
        "{building}, floor {floor}: lease {lease_id} with {tenant}. Start date {start_date}; end date "
        "{end_date}. Monthly rent: {monthly_rent}.",
        "Lease {lease_id} records that {tenant} rents floor {floor} of {building}. It began on {start_date}, "
        "ends on {end_date}, and carries a monthly rent of {monthly_rent}.",
    ],
    "company": [
        "{name} is a {industry} company founded in {founded_year}. It is headquartered in {headquarters} "
        "and employs {employees} people.",
        "Company profile: {name}. Industry: {industry}. Founded: {founded_year}. Headquarters: "
        "{headquarters}. Staff: {employees}.",
        "Founded in {founded_year}, {name} works in {industry} from its head office in {headquarters}, "
        "with a workforce of {employees}.",
    ],
    "person": [
        "{name} works as {role} at {employer} and joined in {start_year}.",
        "Staff record: {name}, {role}, {employer}, since {start_year}.",
        "Since {start_year}, {name} has served as {role} for {employer}.",
    ],
    "building": [
        "{name} stands at {address} in {city}. The building has {floors} floors and was completed in "
        "{year_built}.",
        "Building record: {name}, {address}, {city}. Floors: {floors}. Year built: {year_built}.",
        "Completed in {year_built}, {name} is a {floors}-floor building located at {address}, {city}.",
    ],
    "shipment": [
        "Shipment {tracking_code} of {contents} left {origin} for {destination} on {ship_date} with "
        "{carrier}. It weighed {weight_kg} kg in {packages} packages and was sent {priority}.",
        "Tracking {tracking_code}: {carrier} carried {weight_kg} kg of {contents} from {origin} to "
        "{destination}, shipped {ship_date} as {priority} freight in {packages} packages.",
        "On {ship_date}, {carrier} moved shipment {tracking_code} ({contents}, {weight_kg} kg) from "
        "{origin} to {destination}. The {packages} packages travelled at {priority} priority.",
    ],
    "equipment": [
        "Asset {asset_tag} is a {category}, model {model}, bought in {purchase_year} and kept in {room}. "
        "Condition: {condition}. Serial number {serial_number}, under warranty until {warranty_until}.",
        "Inventory entry {asset_tag}: {category} ({model}), purchased {purchase_year}, located in {room}, "
        "currently {condition}; serial {serial_number}, warranty through {warranty_until}.",
        "The {category} tagged {asset_tag} is a {model} unit from {purchase_year}. It sits in {room} and "
        "is in {condition} condition. Its serial number is {serial_number} and the warranty runs until {warranty_until}.",
    ],
    "weather": [
        "{station} reported {sky} weather on {date}, with a high of {high_c} C, a low of {low_c} C and "
        "{precipitation_mm} mm of precipitation. Humidity was {humidity_pct} percent and visibility {visibility_km} km.",
        "Weather log, {station}, {date}: {sky}. High {high_c} C, low {low_c} C, precipitation "
        "{precipitation_mm} mm. Humidity {humidity_pct} percent, visibility {visibility_km} km.",
        "On {date}, readings at {station} showed {sky} skies, temperatures between {low_c} C and {high_c} C, "
        "{precipitation_mm} mm of rain or snow, {humidity_pct} percent humidity and {visibility_km} km visibility.",
    ],
}

OPTIONAL = {
    "lease": {
        "deposit": ["A security deposit of {deposit} was paid.", "The deposit on file is {deposit}."],
        "signed_by": ["It was signed by {signed_by}.", "{signed_by} signed on behalf of the tenant."],
        "renewal_option": ["The lease can be renewed for {renewal_option}.",
                           "Renewal option: {renewal_option}."],
    },
    "company": {
        "ceo": ["Its chief executive is {ceo}.", "The company is led by {ceo}."],
        "website": ["Website: {website}.", "It can be found online at {website}."],
    },
    "person": {
        "email": ["Email: {email}.", "{name} can be reached at {email}."],
        "phone": ["Phone: {phone}.", "Direct line: {phone}."],
    },
    "building": {
        "manager": ["The property manager is {manager}.", "{manager} manages the property."],
        "parking_spaces": ["It offers {parking_spaces} parking spaces.", "Parking: {parking_spaces} spaces."],
    },
    "shipment": {"insured_value": ["It was insured for {insured_value}.", "Declared value: {insured_value}."]},
    "equipment": {"last_service": ["Last serviced on {last_service}.", "Its last service was on {last_service}."]},
    "weather": {"wind_kmh": ["Wind reached {wind_kmh} km/h.", "Peak wind: {wind_kmh} km/h."]},
}


def _check_templates() -> None:
    """Main templates must use every required field and nothing else."""
    import string
    for t, fields in S.SCHEMA.items():
        required = {f.name for f in fields if not f.optional}
        optional = {f.name for f in fields if f.optional}
        assert len(MAIN[t]) >= 3, f"{t}: fewer than 3 templates"
        for tpl in MAIN[t]:
            used = {n for _, n, _, _ in string.Formatter().parse(tpl) if n}
            assert used == required, f"{t} template uses {sorted(used)} but required is {sorted(required)}"
        assert set(OPTIONAL.get(t, {})) == optional, f"{t}: optional wordings do not match schema"


_check_templates()


def render(r: Record, rng: random.Random) -> str:
    v = _values(r)
    parts = [rng.choice(MAIN[r.type]).format(**v)]
    for fname, wordings in OPTIONAL.get(r.type, {}).items():
        if fname in r.fields:
            parts.append(rng.choice(wordings).format(**v))
    return " ".join(parts)


def main() -> None:
    w = World(seed=11)
    rng = random.Random(11)
    kinds = ["lease", "lease", "company", "person", "building", "lease", "shipment", "equipment",
             "weather", "building"]
    for i, k in enumerate(kinds, 1):
        r = w.make(k)
        print(f"[{i}] {k.upper()}")
        print("    " + render(r, rng) + "\n")


if __name__ == "__main__":
    main()
