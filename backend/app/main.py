from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field as PField, model_validator

load_dotenv()
from .generator import TYPES, Field, generate, to_csv, to_json, to_sql  # noqa: E402
from .llm import suggest_cases  # noqa: E402

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
app = FastAPI(title="AI Test Data Generator for Edge Cases")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "null"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class FieldIn(BaseModel):
    name: str = PField(min_length=1, max_length=60)
    type: Literal["string", "integer", "float", "email", "phone", "date", "boolean", "url"] = "string"
    required: bool = True
    min: float | None = None
    max: float | None = None
    max_length: int | None = PField(default=None, ge=1, le=100000)
    description: str = PField(default="", max_length=300)

    @model_validator(mode="after")
    def valid_range(self):
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"Minimum cannot be greater than maximum for field '{self.name}'")
        self.name = self.name.strip()
        return self


class GenerateIn(BaseModel):
    fields: list[FieldIn] = PField(min_length=1, max_length=20)
    valid_rows: int = PField(default=3, ge=0, le=50)
    seed: int | None = None
    table: str = PField(default="test_data", pattern=r"^[A-Za-z_][A-Za-z0-9_]{0,40}$")
    use_ai: bool = False

    @model_validator(mode="after")
    def names_must_be_unique(self):
        names = [field.name.strip() for field in self.fields]
        if any(not name for name in names):
            raise ValueError("Field names cannot be empty")
        if len(names) != len(set(names)):
            raise ValueError("Field names must be unique")
        return self


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/types")
def types():
    return {"types": TYPES}


@app.post("/api/generate")
def generate_data(req: GenerateIn):
    fields = [Field(**f.model_dump()) for f in req.fields]
    extra, ai_used = {}, False
    if req.use_ai:
        for f in fields:
            found = suggest_cases(f.name, f.type, f.description)
            if found:
                extra[f.name], ai_used = found, True
    rows = generate(fields, req.valid_rows, req.seed, extra)
    columns = [f.name for f in fields]
    summary: dict[str, int] = {}
    for r in rows:
        summary[r["_expected"]] = summary.get(r["_expected"], 0) + 1
    return {
        "columns": columns, "rows": rows, "total": len(rows), "summary": summary, "ai_used": ai_used,
        "exports": {"json": to_json(rows), "csv": to_csv(rows, columns), "sql": to_sql(rows, columns, req.table)},
    }


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
