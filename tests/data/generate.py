"""Generate the Milestone 11 test data: three families, from a fixed seed.

    python tests/data/generate.py        rewrites happy.json, boundary.json, hostile.json
    ./script/seed-test-data              generates, then loads the happy family into a fresh database

Every entry is synthetic (marked "synthetic": true): invented streets, invented
unit names, no real people, addresses or phone numbers. Running this twice gives
byte-identical files, so a diff after regeneration means the generator changed.

  happy     realistic reports that should be accepted
  boundary  inputs sitting exactly on an edge (shortest/longest, earliest/latest, empty vs one
            character), each with the outcome the specification calls for
  hostile   inputs a careless or malicious sender might send: injection strings, markup, odd
            unicode, control characters, wrong types, huge values. The system must never crash
            (no HTTP 5xx) and must either reject the input or store it back exactly as sent

Each entry: {"name", "family", "synthetic": true, "payload", "expect"} where expect is
"accept" or "reject" (the specified outcome), or "safe" (hostile: either is fine, a 5xx is not).
Where the system does not yet do what the specification calls for, the matching test is
marked as an open defect in tests/integration/test_data_families_http.py.
"""
import json
import random
from pathlib import Path

SEED = 20261105
_UNSET = object()  # lets a case send a payload of JSON null
HERE = Path(__file__).resolve().parent

STREETS = ["Synthetic St", "Example Ave", "Sample Rd", "Testfield Blvd", "Mock Lane"]
UNITS = [f"synthetic-unit-{n}" for n in range(1, 9)]
HAPPY_TEXT = [
    "person fell, visible leg injury, conscious and talking",
    "child fell from a bike, bleeding from the knee",
    "driver hurt after a crash, pain in the neck",
    "elderly person dizzy, chest pain, conscious",
    "worker injured by falling equipment, bleeding",
    "bystander hurt in a fall on the stairs",
    "cyclist injured, conscious and talking, arm injury",
    "woman fainted, now conscious, no visible injury",
    "child hurt at the playground, crying, leg pain",
    "something happened, not sure how bad",
]


def base(rng, i):
    return {
        "location": f"{rng.randint(1, 999)} {rng.choice(STREETS)}",
        "severity_raw": rng.choice(HAPPY_TEXT),
        "timestamp_reported": f"2026-11-01T{12 + i // 60:02d}:{i % 60:02d}:00+00:00",
        "reporting_unit": rng.choice(UNITS),
    }


def entry(name, family, payload, expect):
    return {"name": name, "family": family, "synthetic": True, "payload": payload, "expect": expect}


def happy(rng):
    return [entry(f"happy-{i + 1:02d}", "happy", base(rng, i), "accept") for i in range(20)]


def boundary(rng):
    ok = base(rng, 0)
    out = []

    def case(name, expect, **changes):
        out.append(entry(name, "boundary", {**ok, **changes}, expect))

    case("one-character-location", "accept", location="a")
    case("one-character-severity-text", "accept", severity_raw="x")
    case("one-character-reporting-unit", "accept", reporting_unit="u")
    case("255-character-location", "accept", location="L" * 255)
    case("empty-location", "reject", location="")
    case("empty-severity-text", "reject", severity_raw="")
    case("empty-reporting-unit", "reject", reporting_unit="")
    case("empty-timestamp", "reject", timestamp_reported="")
    case("earliest-unix-time", "accept", timestamp_reported="1970-01-01T00:00:00+00:00")
    case("leap-day", "accept", timestamp_reported="2028-02-29T23:59:59+00:00")
    case("not-a-real-day", "reject", timestamp_reported="2027-02-29T10:00:00+00:00")
    case("latest-offset", "accept", timestamp_reported="2026-11-01T12:00:00+14:00")
    case("earliest-offset", "accept", timestamp_reported="2026-11-01T12:00:00-12:00")
    case("microseconds", "accept", timestamp_reported="2026-11-01T12:00:00.123456+00:00")
    case("no-offset-means-utc", "accept", timestamp_reported="2026-11-01T12:00:00")
    for field in ("location", "severity_raw", "timestamp_reported", "reporting_unit"):
        payload = {k: v for k, v in ok.items() if k != field}
        out.append(entry(f"missing-{field}", "boundary", payload, "reject"))
    return out


def hostile(rng):
    ok = base(rng, 0)
    out = []

    def case(name, expect, payload=_UNSET, **changes):
        out.append(entry(name, "hostile", {**ok, **changes} if payload is _UNSET else payload, expect))

    case("sql-injection-in-location", "safe", location="x'; DROP TABLE units; --")
    case("sql-injection-in-severity", "safe", severity_raw="1 OR 1=1; DELETE FROM incident_reports;")
    case("script-tag", "safe", location="<script>alert(1)</script>")
    case("html-entities", "safe", severity_raw="&lt;b&gt;bold&lt;/b&gt; &amp; more")
    case("emoji", "safe", severity_raw="chest pain \U0001f6a8\U0001f691")
    case("right-to-left-text", "safe", location="רחוב דוגמה 1")
    case("combining-characters", "safe", location="é" * 40)
    case("null-byte", "safe", location="before\x00after")
    case("newlines-and-tabs", "safe", severity_raw="line one\nline two\r\n\ttabbed")
    case("control-characters", "safe", severity_raw="".join(chr(c) for c in range(1, 9)))
    case("10k-character-severity", "safe", severity_raw="a" * 10_000)
    case("100k-character-location", "safe", location="b" * 100_000)
    case("whitespace-only-location", "reject", location="   ")
    case("whitespace-only-severity", "reject", severity_raw="\t \n")
    case("number-as-location", "reject", location=123)
    case("boolean-as-reporting-unit", "reject", reporting_unit=True)
    case("list-as-severity", "reject", severity_raw=["chest pain"])
    case("object-as-location", "reject", location={"street": "x"})
    case("null-severity", "reject", severity_raw=None)
    case("far-future-time", "safe", timestamp_reported="2099-01-01T00:00:00+00:00")
    case("far-past-time", "safe", timestamp_reported="0001-01-01T00:00:00+00:00")
    case("not-a-time", "reject", timestamp_reported="yesterday-ish")
    case("extra-unknown-fields", "safe", payload={**ok, "is_admin": True, "id": 1, "status": "classified"})
    case("json-list-instead-of-object", "reject", payload=[1, 2, 3])
    case("json-string-instead-of-object", "reject", payload="just a string")
    case("json-null-instead-of-object", "reject", payload=None)
    case("deeply-nested-values", "reject", payload={**ok, "location": [[[[[[["deep"]]]]]]]})
    shuffled = sorted(STREETS)
    rng.shuffle(shuffled)
    case("many-reports-same-second", "safe", location=" / ".join(shuffled))
    return out


def main():
    rng = random.Random(SEED)
    for name, build in (("happy", happy), ("boundary", boundary), ("hostile", hostile)):
        data = build(rng)
        (HERE / f"{name}.json").write_text(
            json.dumps(data, indent=1, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"{name:9} {len(data):3} entries")


if __name__ == "__main__":
    main()
