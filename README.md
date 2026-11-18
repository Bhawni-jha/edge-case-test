# AI Test Data Generator for Edge Cases

This project is a beginner-friendly web application that automatically creates test data for forms and APIs. It is useful for software testing, quality assurance, and learning how edge cases can reveal bugs.

The application is built with:

- **FastAPI** for the backend and API
- **Python** for test-data generation
- **HTML, CSS and JavaScript** for the frontend
- **Pydantic** for request validation
- **Groq API** for optional AI-generated suggestions

## Table of Contents

1. [What the project does](#what-the-project-does)
2. [Key features](#key-features)
3. [How to use it](#how-to-use-it)
4. [How one-factor-at-a-time testing works](#how-one-factor-at-a-time-testing-works)
5. [Project structure](#project-structure)
6. [How the system works](#how-the-system-works)
7. [Windows installation](#windows-installation)
8. [Running the application](#running-the-application)
9. [Using the sample signup form](#using-the-sample-signup-form)
10. [Using the API](#using-the-api)
11. [Download formats](#download-formats)
12. [Supported field types](#supported-field-types)
13. [How the main Python files work](#how-the-main-python-files-work)
14. [Running the tests](#running-the-tests)
15. [Optional Groq AI setup](#optional-groq-ai-setup)
16. [Troubleshooting](#troubleshooting)
17. [Limitations and future ideas](#limitations-and-future-ideas)

## What the project does

For a form or database table, you describe its fields and limits. For example:

| Field | Type | Minimum | Maximum | Maximum length |
|---|---|---:|---:|---:|
| username | string | - | - | 20 |
| email | email | - | - | - |
| age | integer | 18 | 99 | - |
| phone | phone | - | - | - |

The project generates normal values and edge cases such as:

- Empty values
- `null` values
- Values immediately below or above a limit
- Very long text
- Unicode and emoji
- Invalid email addresses
- Invalid dates
- Overflow numbers
- SQL injection and XSS payloads

## Key features

- Presets for signup, product and order forms
- Custom field names, types and limits
- Required and optional fields
- One-factor-at-a-time test rows
- Valid, invalid and sanitise classifications
- Reproducible data using a seed
- JSON, CSV and SQL exports
- Interactive Swagger API documentation
- Optional AI-suggested cases
- Built-in signup playground
- Responsive white-and-blue interface

## How to use it

1. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).
2. Choose a preset or create fields using **Add field**.
3. Enter a field name.
4. Select a field type.
5. Mark it as required or optional.
6. Add minimum, maximum or maximum-length values where relevant.
7. Set the number of valid rows, optionally set a seed, and enter a table name.
8. Click **Generate edge cases**.
9. Filter rows using the **Show** selector.
10. Use **Try** to load a row into the sample signup form.
11. Download JSON, CSV or SQL using the export buttons.

## How one-factor-at-a-time testing works

Most generated rows change only one field. Every other field uses a normal valid value.

For example, for these fields:

```text
age = 18 to 99
email = valid email
username = maximum 20 characters
```

An age test row can contain:

```json
{
  "age": 17,
  "email": "user123@example.com",
  "username": "normaluser"
}
```

In this row, only `age` is an edge case. Therefore, if the row behaves unexpectedly, the age validation is the likely problem.

### Expected labels

| Label | Meaning |
|---|---|
| `valid` | The system should accept this value |
| `invalid` | The system should reject this value with a clear error |
| `sanitise` | The system may accept or reject it, but it must never execute script or SQL |

Every field also creates an empty and `null` case. Required fields expect `invalid`; optional fields expect `valid`.

## Project structure

```text
Test-Data-Generator/
|-- README.md
|-- frontend/
|   `-- index.html
`-- backend/
    |-- requirements.txt
    |-- .env.example
    |-- app/
    |   |-- __init__.py
    |   |-- main.py
    |   |-- generator.py
    |   `-- llm.py
    `-- tests/
        `-- test_generator.py
```

### File responsibilities

| File | Responsibility |
|---|---|
| `frontend/index.html` | Complete web interface, signup playground and API calls |
| `backend/app/main.py` | FastAPI application, validation, routes and frontend serving |
| `backend/app/generator.py` | Edge-case generation, baseline values and exports |
| `backend/app/llm.py` | Optional Groq API integration |
| `backend/tests/test_generator.py` | Basic generator assertions |
| `backend/requirements.txt` | Python dependencies |
| `backend/.env.example` | Optional environment-variable template |

## How the system works

```text
Browser
  |
  | HTTP POST /api/generate
  v
FastAPI main.py
  |
  | Validate fields with Pydantic
  v
generator.py
  |
  | Create baseline rows and edge-case rows
  v
Optional llm.py
  |
  | Add Groq AI suggestions
  v
JSON response
  |
  +--> Table in the browser
  +--> JSON download
  +--> CSV download
  `--> SQL INSERT statements
```

The browser sends a JSON request. FastAPI converts each requested field into a Python `Field` object. `generator.py` creates rows and export text. The browser receives JSON and displays it in the table.

## Windows installation

Open PowerShell and enter:

```powershell
cd C:\Users\user\Downloads\Test-Data-Generator\Test-Data-Generator
cd backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Installing dependencies is only required once, unless a new package is added or the environment is deleted.

## Running the application

Activate the environment and start the backend:

```powershell
cd C:\Users\user\Downloads\Test-Data-Generator\Test-Data-Generator\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open:

- Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

To stop the server, press `Ctrl+C` in the terminal.

Do not open `frontend/index.html` directly by double-clicking it if the browser receives API requests. Use the FastAPI URL so the browser and API run on the same origin.

## Using the sample signup form

The built-in playground appears below the generated-data table.

1. Generate data using the **User signup** preset.
2. Find a row in the table.
3. Click **Try** in that row.
4. The username, email, age, phone and birth-date fields are filled automatically.
5. Click **Check signup**.
6. Read the result in the right-side result panel.

Valid generated rows should show **Signup accepted**. Invalid generated rows should show **Signup rejected** along with the relevant validation messages.

The sample signup is local-only JavaScript validation. It does not create a real account or send data to a server.

## Using the API

The API can be tested from [Swagger UI](http://127.0.0.1:8000/docs) or from PowerShell.

### Health check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Supported types

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/types
```

### Generate test data

```powershell
$body = @{
  fields = @(
    @{ name = "username"; type = "string"; required = $true; max_length = 20 },
    @{ name = "email"; type = "email"; required = $true },
    @{ name = "age"; type = "integer"; required = $true; min = 18; max = 99 }
  )
  valid_rows = 3
  seed = 42
  table = "test_data"
  use_ai = $false
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/generate `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

$response.total
$response.rows
```

The request fields are:

| Field | Purpose |
|---|---|
| `fields` | List of fields to generate |
| `valid_rows` | Number of normal baseline rows |
| `seed` | Optional integer used for reproducible values |
| `table` | SQL table name |
| `use_ai` | Whether to request Groq suggestions |

## Download formats

### JSON

Contains complete rows, expected labels and metadata. It is suitable for API tests or custom scripts.

### CSV

Contains one row per test case. It can be imported into spreadsheets and data-driven test tools.

Example columns:

```text
age,email,username,_case,_expected
```

### SQL

Contains comments and `INSERT` statements.

```sql
-- age: min - 1 (expected: invalid)
INSERT INTO "test_data" ("age", "email", "username")
VALUES (17, 'user123@example.com', 'normaluser');
```

SQL values are escaped for quotes, but SQL export is intended for test data. Review generated statements before using them against a real database.

## Supported field types

| Type | Main test cases |
|---|---|
| `string` | Empty, whitespace, length limits, unicode, emoji, SQL and HTML payloads |
| `integer` | Minimum, maximum, zero, negative values, decimal text, overflow |
| `float` | Numeric boundaries, precision, negative zero, text, very large values |
| `email` | Missing `@`, multiple `@`, spaces, trailing dot, plus tags, long values |
| `phone` | Missing country code, spaces, letters, symbols and length limits |
| `date` | Invalid leap days, month 13, day 32, zero dates and wrong formats |
| `boolean` | `true`, `yes`, `1`, `maybe` and normal true/false values |
| `url` | Missing protocol, dangerous protocols, spaces and very long URLs |

## How the main Python files work

### `generator.py`

The `Field` dataclass stores a field's name, type, required state and limits.

The `baseline()` function creates normal valid values.

The `cases_for()` function creates edge cases for a field.

The `generate()` function:

1. Creates normal baseline rows.
2. Iterates through every field.
3. Adds one edge case at a time.
4. Copies all remaining baseline fields as valid values.

The export functions convert rows into JSON, CSV or SQL.

### `main.py`

`main.py` creates the FastAPI application. Pydantic validates request fields:

- Names must not be empty.
- Names must be unique.
- Maximum length must be positive.
- Minimum cannot be greater than maximum.
- Field count is limited to 20.
- Valid-row count is limited to 50.

It also serves the frontend and provides the `/api/health`, `/api/types` and `/api/generate` endpoints.

### `llm.py`

`llm.py` calls Groq only when:

- `GROQ_API_KEY` exists.
- The field has a description.
- AI mode is enabled.

Network or response errors are logged and ignored, so the rule-based generator continues to work.

## Running the tests

From the backend folder:

```powershell
cd C:\Users\user\Downloads\Test-Data-Generator\Test-Data-Generator\backend
python tests\test_generator.py
```

A successful result ends with:

```text
ok: 55 rows generated, all checks passed
```

The test verifies:

- Baseline rows are valid.
- Numeric boundaries are classified correctly.
- Optional fields accept `null`.
- Required fields reject `null`.
- String length limits work.
- SQL quotes are escaped.
- CSV headers are correct.
- The same seed produces the same rows.

## Optional Groq AI setup

Copy the environment template:

```powershell
copy .env.example .env
```

Set values in `backend/.env`:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

The key must belong to the user running the project and must not be committed to source control.

Enter a field description, enable **Add AI-suggested cases**, and generate rows. AI is optional and is not required for the project to run.

## Troubleshooting

### Port 8000 is already in use

Find the listening process:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

Then stop it using its exact process ID:

```powershell
Stop-Process -Id <process-id>
```

Start the app again:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Do not use the process name with `Stop-Process`, because that can stop unrelated processes.

### `requests` or another module is missing

Install the dependencies again:

```powershell
cd C:\Users\user\Downloads\Test-Data-Generator\Test-Data-Generator\backend
python -m pip install -r requirements.txt
```

### Unexpected token `<` or HTML received as JSON

This means a request expected JSON but received HTML.

Check that:

1. The backend is running at port `8000`.
2. You opened [http://127.0.0.1:8000](http://127.0.0.1:8000), not a different server or a file URL.
3. `/api/generate` is called with `POST`.
4. The request contains valid JSON.

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

### PowerShell activation is blocked

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### AI cases are not displayed

Check that:

- `GROQ_API_KEY` is present in `backend/.env`.
- The field has a description.
- The Groq key and model are valid.
- The **Add AI-suggested cases** checkbox is enabled.

AI failure does not stop the local generator.

## Limitations and future ideas

Current limitations:

- No cross-field relationship validation
- No database storage
- No real user registration
- No authentication
- No full international email or phone standards
- No automated browser test framework

Possible student projects:

- Add credit-card, PAN or Aadhaar-style field types
- Add start-date/end-date dependencies
- Import field definitions from JSON Schema or SQL `CREATE TABLE`
- Add Playwright or Selenium test export
- Save reusable templates
- Add CSV import
- Add login or signup persistence using a database
- Add unit tests for the FastAPI endpoints
