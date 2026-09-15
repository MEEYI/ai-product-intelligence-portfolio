# AI Product Intelligence

**An engineering portfolio prototype for organizing product evidence and exploring AI-assisted research.**

[中文说明](README.zh-CN.md) · [Architecture](docs/architecture.md) · [Public-data policy](docs/privacy.md) · [Security boundaries](SECURITY.md)

Product research combines several kinds of information: brand records, source links, reference products, images, and analysis. This project models those relationships in a small FastAPI backend and keeps local evidence retrieval separate from optional AI calls. The example domain is headwear; the demonstration brand, **Northstar**, and its `northstar.example` URLs are fictional.

This repository demonstrates implementation choices and testable behavior. It does not claim real customer adoption, measured business impact, production readiness, or validated AI accuracy.

## What you can explore

| Capability | Implementation |
| --- | --- |
| Product-development records | Customers, brands, their relationships, projects, and project items |
| Traceable reference data | Brand sources, assets, product references, and stored product analyses |
| Local brand lookup | Literal, case-insensitive name matching with whitespace handling and explicit ambiguity errors |
| Evidence assembly | Active sources and products, plus active assets enabled for analysis, returned in one response |
| Optional brand research | Web-search summaries with source links, retrieval metadata, and an explicit review flag |
| Optional product analysis | Product text and an optional image mapped into structured headwear attributes |
| Offline review | Fictional fixtures, an in-memory demonstration, and mocked AI tests |

**Stack:** Python 3.13 · FastAPI · Pydantic · SQLAlchemy · SQLite · optional OpenAI SDK.

## Quick start

Run commands from the repository root. Installing dependencies needs network access; the demonstration and tests use local fixtures and simulated AI responses.

### 1. Create an environment

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS / Linux:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Leave the API key empty to explore local functionality. The resolved dependency versions are in `requirements.txt`; direct dependencies are listed in `requirements.in`.

### 2. Run the offline demonstration

```bash
python scripts/demo.py
```

The demonstration uses fictional Northstar records in an isolated, in-memory SQLite database. AI responses are simulated; no API key, paid model call, real customer record, or external brand research is needed. Its records are discarded when the process ends and do not populate the server database.

### 3. Run the checks

```bash
python -m unittest discover -s tests -v
python scripts/check_public_release.py
```

Tests exercise behavior such as literal name matching, ambiguous names, evidence filtering, citation handling, cache behavior, and upstream failures using isolated data and mocked services. The release check looks for excluded files and suspicious text patterns; it is a heuristic, not proof that every possible disclosure has been detected.

### 4. Explore the local API

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open [interactive API documentation](http://127.0.0.1:8000/docs). The server creates `portfolio_demo.db` in the working directory. It starts without the demonstration's in-memory records; use the API documentation to create your own fictional records. Uploaded files are stored under `uploads/`. Both the database and uploads are excluded from version control.

Useful routes:

| Route | Purpose |
| --- | --- |
| `GET /` | Check that the application is running |
| `GET /brands/by-name?brand_name=Northstar` | Look up an existing local brand |
| `GET /brand-intelligence/by-name/evidence?brand_name=Northstar` | Assemble that brand's local evidence without AI |
| `GET /brand-research?brand_name=...` | Request optional live, source-linked research |
| `POST /product-analyses/product/{product_reference_id}/analyze` | Request and persist an optional live product analysis |

The local lookup returns `404` until the requested brand exists in the server database.

## Optional live AI

Configure `.env` locally before calling AI routes:

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=
```

Supply your own key and explicitly select a model available to your API account. Live brand research requires a model that supports web search; product-image analysis requires image input support. Restart the server after changing configuration. The offline demonstration remains simulated even when credentials are present.

Live requests can incur API charges. Brand research sends the requested brand name to the provider. Product analysis sends product text and, when supplied, an image URL or image content. Review [data handling](docs/privacy.md) before enabling these routes.

Source links make a research result inspectable; they do not establish its correctness. Research previews carry `needs_review: true` and are not written to the database. Product analysis results are persisted by their explicit analysis route and also require human review. Any model-produced confidence value is uncalibrated.

## Engineering decisions

- **Separate local evidence from live research.** Users can inspect stored material without a network call or an AI dependency.
- **Make ambiguous names visible.** A name matching multiple records returns `409` with candidates instead of silently picking one.
- **Preserve research provenance.** Source URLs, retrieval time, model, and cache status travel with the preview.
- **Test service boundaries offline.** Mocked upstream responses cover failure paths without spending API credits or depending on a provider's current output.
- **Keep the public release small.** Source, tests, documentation, and synthetic examples are selected through an allowlist; runtime files and private material are excluded.

See [architecture and tradeoffs](docs/architecture.md) for the request flows and data model.

## Current limits

This is a backend portfolio prototype. It has no authentication, authorization, rate limiting, or complete product frontend. SQLite, startup table creation, and process-local caching are suitable for a small local demonstration; migrations, concurrency behavior, deployment controls, and operational recovery need further work. The test suite covers selected workflows and is not a complete security or performance assessment.

AI output quality has not been independently evaluated or calibrated. Uploads, external URLs, model output validation, and errors need further hardening before accepting untrusted input. Keep the example server bound to localhost. Publishing source code does not make the application safe to deploy publicly.

## Repository map

```text
backend/
  database/    SQLite engine and request-scoped sessions
  models/      SQLAlchemy records and relationships
  schemas/     Request and response schemas
  routers/     API endpoints
  services/    Local lookup and optional AI integrations
tests/         Isolated behavioral tests
scripts/       Offline demonstration and public-release checks
docs/          Architecture and data-handling notes
```
