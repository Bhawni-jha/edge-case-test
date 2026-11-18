"""Run from the backend folder:  python tests/test_generator.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.generator import Field, generate, to_csv, to_sql  # noqa: E402


def by_case(rows, text):
    return next(r for r in rows if r["_case"] == text)


def main() -> None:
    fields = [Field("age", "integer", min=18, max=60), Field("email", "email"),
              Field("name", "string", max_length=20), Field("nick", "string", required=False)]
    rows = generate(fields, valid_rows=2, seed=1)
    assert rows[0]["_expected"] == "valid" and rows[0]["_category"] == "baseline"
    assert by_case(rows, "age: min - 1")["age"] == 17 and by_case(rows, "age: min - 1")["_expected"] == "invalid"
    assert by_case(rows, "age: max")["age"] == 60 and by_case(rows, "age: max")["_expected"] == "valid"
    assert by_case(rows, "age: max + 1")["_expected"] == "invalid"
    assert by_case(rows, "name: 21 characters")["_expected"] == "invalid"
    assert by_case(rows, "nick: null value")["_expected"] == "valid"      # optional field
    assert by_case(rows, "name: null value")["_expected"] == "invalid"    # required field
    assert by_case(rows, "name: SQL injection")["_expected"] == "sanitise"
    assert "@" in by_case(rows, "age: min")["email"]                      # other fields stay valid
    assert generate(fields, 2, seed=5) == generate(fields, 2, seed=5)     # same seed, same data
    assert "''" in to_sql([by_case(rows, "name: SQL injection")], ["age", "email", "name", "nick"])
    assert to_csv(rows, ["age", "email", "name", "nick"]).startswith("age,email,name,nick,_case,_expected")
    print(f"ok: {len(rows)} rows generated, all checks passed")


if __name__ == "__main__":
    main()
