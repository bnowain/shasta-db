# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shasta-DB is a local-first archive browser and metadata editor for mixed media files. It indexes files from configured directory roots into SQLite and provides a web UI for browsing, previewing, and tagging content with categories and people.

## Running the App

```bash
# Option 1: With venv activated
uvicorn app.main:app --reload --port 8844

# Option 2: Without activating venv (uses .venv/Scripts/python.exe)
python start.py [--port 8850]
```

- GUI: http://127.0.0.1:8844/ui
- API docs (Swagger): http://127.0.0.1:8844/docs
- First run: POST /ingest via /docs to scan the configured root directory

## Setup

```bash
py -m venv .venv
.venv/Scripts/Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
```

Configure `app/settings.py` with the SQLite path and initial root directory path before first run.

## Architecture

**Stack:** FastAPI + async SQLAlchemy (aiosqlite) + SQLite + Jinja2 templates + HTMX

**All application logic lives in `app/`:**

- `main.py` — Single-file FastAPI app containing all routes (API + UI endpoints), file ingestion logic, filter/sort helpers, and the `CATEGORIES` list. This is the primary file for most changes.
- `models.py` — SQLAlchemy ORM models: `Root`, `Instance`, `Person`, `InstancePerson` (junction table)
- `db.py` — Async engine setup, session factory (`SessionLocal`), schema migrations, WAL mode + foreign key pragmas
- `settings.py` — Pydantic `Settings` with `sqlite_path`, `initial_root_name`, `initial_root_path`
- `templates/ui.html` — Main page shell (two-pane layout, filter form)
- `templates/partials/file_list.html` — HTMX partial for file list with pagination
- `templates/partials/preview.html` — HTMX partial for file preview + metadata editor
- `static/ui.css` — All styling

**Key patterns:**
- All DB operations are async (`async with SessionLocal() as db`)
- The UI is server-rendered HTML with HTMX for dynamic loading (no JS framework)
- File type detection uses extension mapping via `guess_kind()` in main.py
- Ingestion uses upsert logic: INSERT new files, UPDATE existing on IntegrityError
- `_apply_filters()` and `_apply_sort()` compose SQLAlchemy WHERE/ORDER clauses for both UI list and search
- Path traversal protection on `/file/{instance_id}` endpoint

**Database schema (SQLite, WAL mode):**
- `roots` — Physical directories to scan (name is unique key)
- `instances` — Indexed files with metadata (unique on root_id + rel_path)
- `people` — Named entities for cross-file tagging
- `instance_people` — Many-to-many junction with `source` field (manual|llm|path|ocr|transcript)
- Migrations in `db.py._migrate()` add columns/tables for backward compatibility

## Categories

Defined in `main.py` as `CATEGORIES`: Government Meetings, Podcasts, Social Media, Public Records, Unknown (plus empty string for unset).

## Roadmap Context

Planned features include: file hashing/dedup, OCR, audio/video transcription, LLM summaries + auto-tagging, and a clean-library reorganizer. The `skip_processing` flag on Instance exists to exclude .exe files from future processing pipelines.

## Atlas Integration

This project is a spoke in the **Atlas** hub-and-spoke ecosystem. Atlas is a central orchestration hub that routes queries across spoke apps. It lives in a sibling directory (`E:\0-Automated-Apps\Atlas`).

**Rules:**

1. Only modify **this** project by default. Do not modify other spoke projects or Atlas unless explicitly asked.
2. If approved, changes to other projects are allowed — but always propose first and wait for approval.
3. Suggest API endpoint changes in other spokes if they would improve integration, but never write code in another project without explicit approval.
4. This app must remain **independently functional** — it works on its own without Atlas or any other spoke.
5. **No spoke-to-spoke dependencies.** All cross-app communication goes through Atlas.
   **Approved exceptions** (documented peer service calls):
   - `Shasta-PRA-Backup → civic_media POST /api/transcribe` — Transcription-as-a-Service
   New cross-spoke calls must be approved and added to this exception list.
6. If modifying or removing an API endpoint that Atlas may depend on, **stop and warn** before proceeding.
7. New endpoints added for Atlas integration should be general-purpose and useful standalone, not tightly coupled to Atlas internals.

**Spoke projects** (sibling directories, may be loaded via `--add-dir` for reference):

- **civic_media** — meeting transcription, diarization, voiceprint learning
- **article-tracker** — local news aggregation and monitoring
- **Shasta-DB** — civic media archive browser and metadata editor (this project)
- **Facebook-Offline** — local personal Facebook archive for LLM querying (private, local only)
- **Shasta-PRA-Backup** — public records requests browser
- **Shasta-Campaign-Finance** — campaign finance disclosures from NetFile
- **Facebook-Monitor** — automated public Facebook page monitoring

## Testing

No formal test suite exists yet. Use Playwright for browser-based UI testing and pytest for API/service tests.

### Setup

```bash
pip install playwright pytest pytest-asyncio httpx
python -m playwright install chromium
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only Playwright browser tests
pytest tests/ -v -k "browser"

# Run only API tests
pytest tests/ -v -k "api"
```

### Writing Tests

- **Browser tests** go in `tests/test_browser.py` — use Playwright to verify the HTMX UI (file list, preview panel, filtering, sorting, category/people tagging)
- **API tests** go in `tests/test_api.py` — use httpx against FastAPI endpoints (`/ingest`, file listing, metadata editing)
- **Service tests** go in `tests/test_services.py` — unit tests for file ingestion, kind detection, filter composition
- The server must be running at localhost:8844 for browser tests
- HTMX partial responses can be tested by checking for correct HTML fragments

### Key Flows to Test

1. **Ingestion**: POST /ingest scans directory and creates Instance records
2. **File browsing**: file list renders, pagination works, filters apply
3. **Preview**: clicking a file shows preview with correct metadata
4. **Tagging**: assigning categories and people updates the database
5. **Search**: search returns relevant results across all indexed files

### Lazy ChromaDB Sync (Atlas RAG)
Atlas maintains a centralized ChromaDB vector store. This project does NOT need its
own vector DB. Atlas fetches candidate records from this spoke's search API, chunks
deterministically, validates against ChromaDB cache, and embeds only new/stale chunks.
ChromaDB is a cache — this spoke's SQLite DB is the source of truth.

See: `Atlas/app/services/rag/deterministic_chunking.py` for this spoke's chunking strategy.

## Master Schema & Codex References

**`E:\0-Automated-Apps\MASTER_SCHEMA.md`** — Canonical cross-project database
schema and API contracts. **HARD RULE: If you add, remove, or modify any database
tables, columns, API endpoints, or response shapes, you MUST update the Master
Schema before finishing your task.** Do not skip this — other projects read it to
understand this project's data contracts.

**`E:\0-Automated-Apps\MASTER_PROJECT.md`** describes the overall ecosystem
architecture and how all projects interconnect.

> **HARD RULE — READ AND UPDATE THE CODEX**
>
> **`E:\0-Automated-Apps\master_codex.md`** is the living interoperability codex.
> 1. **READ it** at the start of any session that touches APIs, schemas, tools,
>    chunking, person models, search, or integration with other projects.
> 2. **UPDATE it** before finishing any task that changes cross-project behavior.
>    This includes: new/changed API endpoints, database schema changes, new tools
>    or tool modifications in Atlas, chunking strategy changes, person model changes,
>    new cross-spoke dependencies, or completing items from a project's outstanding work list.
> 3. **DO NOT skip this.** The codex is how projects stay in sync. If you change
>    something that another project depends on and don't update the codex, the next
>    agent working on that project will build on stale assumptions and break things.
