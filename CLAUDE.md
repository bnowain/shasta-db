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
