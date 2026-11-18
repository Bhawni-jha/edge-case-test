"""Rule-based edge-case library. Pure Python, no network: easy to test.

Method: one-factor-at-a-time. Every test row keeps all fields valid except ONE field,
which gets an edge-case value. If the row is rejected, you know which field caused it.
Expected values: "valid" (should be accepted), "invalid" (should be rejected),
"sanitise" (may be accepted, but must be escaped/cleaned and never executed).
"""
import csv
import datetime as dt
import io
import json
import random
import string
from dataclasses import dataclass
from typing import Any

TYPES = ["string", "integer", "float", "email", "phone", "date", "boolean", "url"]


@dataclass
class Field:
    name: str
    type: str = "string"
    required: bool = True
    min: float | None = None
    max: float | None = None
    max_length: int | None = None
    description: str = ""


Case = tuple[str, Any, str, str]  # label, value, expected, category


def baseline(f: Field, rnd: random.Random) -> Any:
    """A normal, valid value for the field."""
    if f.type == "integer":
        lo = int(f.min) if f.min is not None else 1
        hi = int(f.max) if f.max is not None else lo + 100
        return rnd.randint(lo, max(lo, hi))
    if f.type == "float":
        lo = f.min if f.min is not None else 1.0
        hi = f.max if f.max is not None else lo + 100.0
        return round(rnd.uniform(lo, max(lo, hi)), 2)
    if f.type == "email":
        return f"user{rnd.randint(1, 999)}@example.com"
    if f.type == "phone":
        return f"+1415555{rnd.randint(0, 9999):04d}"
    if f.type == "date":
        return (dt.date(2020, 1, 1) + dt.timedelta(days=rnd.randint(0, 1500))).isoformat()
    if f.type == "boolean":
        return rnd.choice([True, False])
    if f.type == "url":
        return f"https://example.com/p/{rnd.randint(1, 999)}"
    size = max(1, min(f.max_length or 12, 12))
    return "".join(rnd.choice(string.ascii_letters) for _ in range(size))


def _numeric_cases(f: Field) -> list[Case]:
    lo, hi = f.min, f.max
    is_int = f.type == "integer"
    num = (lambda v: int(v)) if is_int else (lambda v: float(v))
    out: list[Case] = []

    def ok(v):
        return (lo is None or v >= lo) and (hi is None or v <= hi)

    def add(label, v, cat="boundary"):
        out.append((label, v, "valid" if ok(v) else "invalid", cat))

    step = 1 if is_int else 0.01
    if lo is not None:
        add("min - 1", num(lo - step)); add("min", num(lo)); add("min + 1", num(lo + step))
    if hi is not None:
        add("max - 1", num(hi - step)); add("max", num(hi)); add("max + 1", num(hi + step))
    add("zero", num(0), "special"); add("negative one", num(-1), "special")
    if is_int:
        add("32-bit overflow (2^31)", 2**31, "overflow"); add("64-bit overflow (2^63)", 2**63, "overflow")
        out.append(("decimal given for integer", 1.5, "invalid", "format"))
    else:
        add("many decimals", 0.30000000000000004, "precision"); add("negative zero", -0.0, "special")
        add("very large (1e308)", 1e308, "overflow")
        out += [("NaN as text", "NaN", "invalid", "format"), ("Infinity as text", "Infinity", "invalid", "format")]
    out += [("text instead of number", "abc", "invalid", "format"), ("number as text", "42", "invalid", "format")]
    return out


def _string_cases(f: Field) -> list[Case]:
    n = f.max_length
    out: list[Case] = [
        ("single character", "a", "valid", "length"),
        ("whitespace only", "   ", "invalid" if f.required else "valid", "empty"),
        ("leading and trailing spaces", "  John  ", "valid", "whitespace"),
        ("unicode and emoji", "Zoë 😀 مرحبا 你好", "valid", "unicode"),
        ("special characters", "!@#$%^&*()_+-=[]{}|;:,.<>?", "valid", "special"),
        ("line break inside", "line1\nline2", "valid", "special"),
        ("SQL injection", "' OR '1'='1'; DROP TABLE users;--", "sanitise", "security"),
        ("XSS script tag", "<script>alert(1)</script>", "sanitise", "security"),
        ("HTML injection", "<img src=x onerror=alert(1)>", "sanitise", "security"),
        ("very long (10,000 chars)", "a" * 10000, "invalid" if n else "valid", "length"),
    ]
    if n:
        out += [(f"exactly {n} characters", "a" * n, "valid", "length"), (f"{n + 1} characters", "a" * (n + 1), "invalid", "length")]
    return out


FIXED: dict[str, list[Case]] = {
    "email": [
        ("plus tag", "user+tag@example.com", "valid", "format"), ("subdomain", "a@mail.example.co.in", "valid", "format"),
        ("missing @", "userexample.com", "invalid", "format"), ("double @", "a@@example.com", "invalid", "format"),
        ("no domain", "user@", "invalid", "format"), ("no local part", "@example.com", "invalid", "format"),
        ("space inside", "us er@example.com", "invalid", "format"), ("trailing dot", "user@example.com.", "invalid", "format"),
        ("very long (320+ chars)", "a" * 310 + "@example.com", "invalid", "length"),
        ("unicode local part", "üser@example.com", "valid", "unicode"),
    ],
    "phone": [
        ("without country code", "4155550123", "valid", "format"), ("with spaces", "+1 415 555 0123", "valid", "format"),
        ("too short", "+1415", "invalid", "length"), ("too long", "+14155550123456789", "invalid", "length"),
        ("letters inside", "+1415abc0123", "invalid", "format"), ("only symbols", "+()-", "invalid", "format"),
    ],
    "date": [
        ("leap day", "2024-02-29", "valid", "boundary"), ("invalid leap day", "2023-02-29", "invalid", "boundary"),
        ("month 13", "2024-13-01", "invalid", "format"), ("day 32", "2024-01-32", "invalid", "format"),
        ("zero date", "0000-00-00", "invalid", "format"), ("very old date", "1900-01-01", "valid", "boundary"),
        ("far future", "9999-12-31", "valid", "boundary"), ("wrong format (DD/MM/YYYY)", "31/12/2024", "invalid", "format"),
        ("text instead of date", "tomorrow", "invalid", "format"),
    ],
    "boolean": [
        ("string 'true'", "true", "invalid", "format"), ("yes", "yes", "invalid", "format"),
        ("number 1", 1, "invalid", "format"), ("maybe", "maybe", "invalid", "format"),
    ],
    "url": [
        ("no scheme", "example.com", "invalid", "format"), ("javascript: URL", "javascript:alert(1)", "sanitise", "security"),
        ("with query and fragment", "https://example.com/a?b=1#c", "valid", "format"), ("contains spaces", "https://exa mple.com", "invalid", "format"),
        ("very long URL", "https://example.com/" + "a" * 2100, "invalid", "length"),
    ],
}


def cases_for(f: Field) -> list[Case]:
    if f.type not in TYPES:
        raise ValueError(f"Unknown type: {f.type}")
    out: list[Case] = [("null value", None, "invalid" if f.required else "valid", "empty")]
    if f.type != "boolean":
        out.append(("empty string", "", "invalid" if f.required else "valid", "empty"))
    if f.type in ("integer", "float"):
        out += _numeric_cases(f)
    elif f.type == "string":
        out += _string_cases(f)
    else:
        out += FIXED[f.type]
    return out


def generate(fields: list[Field], valid_rows: int = 3, seed: int | None = None,
             extra: dict[str, list[Case]] | None = None) -> list[dict]:
    """Returns rows: valid baseline rows first, then one row per (field, edge case)."""
    rnd = random.Random(seed)
    rows: list[dict] = []
    for i in range(valid_rows):
        row = {f.name: baseline(f, rnd) for f in fields}
        row.update(_case=f"valid baseline #{i + 1}", _expected="valid", _category="baseline")
        rows.append(row)
    for f in fields:
        for label, value, expected, cat in cases_for(f) + (extra or {}).get(f.name, []):
            row = {g.name: baseline(g, rnd) for g in fields}
            row[f.name] = value
            row.update(_case=f"{f.name}: {label}", _expected=expected, _category=cat)
            rows.append(row)
    return rows


def to_json(rows: list[dict]) -> str:
    return json.dumps(rows, indent=2, ensure_ascii=False, default=str)


def to_csv(rows: list[dict], columns: list[str]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(columns + ["_case", "_expected"])
    for r in rows:
        w.writerow([("" if r[c] is None else r[c]) for c in columns] + [r["_case"], r["_expected"]])
    return buf.getvalue()


def _sql_value(v: Any) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def to_sql(rows: list[dict], columns: list[str], table: str = "test_data") -> str:
    cols = ", ".join(f'"{c}"' for c in columns)
    lines = []
    for r in rows:
        lines.append(f"-- {r['_case']} (expected: {r['_expected']})".replace("\n", " "))
        lines.append(f'INSERT INTO "{table}" ({cols}) VALUES ({", ".join(_sql_value(r[c]) for c in columns)});')
    return "\n".join(lines)
