\# shasta-db



Local-first archive browser + metadata editor for mixed media (videos, audio, PDFs, images, docs, text).  

Goal: make a chaotic repository searchable, previewable, and “triage-able” so you can later run OCR/transcription/LLM summaries and reorganize into a clean directory structure without losing provenance.



---



\## What this project does (current)



\### Ingest + index

\- Indexes files from one or more “roots” into a local SQLite database.

\- Stores file metadata: path, type (kind), extension, size, modified time, plus triage fields.



\### Web GUI

\- Two-pane layout: file list (left) + inline preview + metadata editor (right).

\- Filter/sort for large libraries:

&nbsp; - Filters: Category, Kind, Extension, Needs Review, search text

&nbsp; - Sort: newest/oldest, name, size

&nbsp; - Pagination

\- Inline preview:

&nbsp; - Video (`<video controls>`)

&nbsp; - Audio (`<audio controls>`)

&nbsp; - Images (`<img>`)

&nbsp; - PDFs (`<iframe>`)

&nbsp; - Other types: open/download link

\- Metadata edits (v1):

&nbsp; - Category (single-select)

&nbsp; - People (many-to-many, add/remove by name)

&nbsp; - Needs Review flag

&nbsp; - Optional display title override



\### API (current)

\- `POST /ingest` — scan a configured root and upsert file instances

\- `GET /search` — JSON results for quick testing/automation

\- `GET /file/{id}` — stream the original file (used by the UI)

\- `PATCH /instances/{id}` — update metadata

\- People:

&nbsp; - `GET /people`

&nbsp; - `POST /instances/{id}/people`

&nbsp; - `DELETE /instances/{id}/people/{person\_id}`

\- GUI:

&nbsp; - `GET /ui`

&nbsp; - `GET /ui/list`

&nbsp; - `GET /ui/preview/{id}`



---



\## Why Category + People



\- \*\*Category\*\* = where the item belongs (Government Meetings, Podcasts, Social Media, Public Records, Unknown).

\- \*\*People\*\* = the primary way to browse across categories.

&nbsp; - Example: select “Clint Curtis” and see everything linked to him (default newest → oldest).



This matches the long-term goal: files can live in separate “clean” category directories while the DB cross-links them through People/tags.



---



\## Project layout



app/

main.py

db.py

models.py

settings.py

templates/

ui.html

partials/

file\_list.html

preview.html

static/

ui.css

data/

.gitkeep

requirements.txt

Patch-ShastaDB-PersonFilter.ps1





---



\## Setup (Windows PowerShell)



\### 1) Create and activate a virtual environment

```powershell

cd E:\\0-Automated-Apps\\Shasta-DB

py -m venv .venv

.\\.venv\\Scripts\\Activate.ps1



\###2) Install dependencies

pip install -r requirements.txt



\###3) Configure paths



Edit app/settings.py:



sqlite\_path (example): E:\\0-Automated-Apps\\Shasta-DB\\data\\archive.sqlite



initial\_root\_path (example): D:\\Google Drive\\For Doni



Tip: you can change the root later without re-ingesting by updating the root path via API.



4\) Run the app

uvicorn app.main:app --reload --port 8844



Open:



GUI: http://127.0.0.1:8844/ui



API docs: http://127.0.0.1:8844/docs



First run



Start the server.



In /docs, run POST /ingest (defaults to the initial root).



Go to /ui:



Browse recent files



Click items to preview



Set Category, People, Needs Review



Roadmap (planned)

1\) Hashing + dedupe



Compute SHA-256 for each file



Collapse exact duplicates



Track “canonical” copies and derived/transcoded variants



2\) OCR for screenshots/images



Run OCR on image files



Store extracted text in DB with pointer to the original file



(Optional) local vision model to label non-text images



3\) Transcription for audio/video



Bulk transcription pipeline



Store transcripts + timestamps in DB



Diarization loop can be integrated as a separate pipeline later



4\) LLM summaries + tagging



Chunk content (OCR + transcripts + docs)



Write summaries back to DB



Generate candidate People/Category suggestions for human review



5\) Clean-library copier/reorganizer



Copy (not move) originals into a clean directory structure



Maintain DB references and provenance links back to the original root



Eventually add an FFmpeg batch transcoder pipeline to shrink storage



Notes on proprietary .exe public-records packages



Some .exe files are from public records requests for proprietary security footage viewers. These should be:



stored alongside their directory context



excluded from OCR/transcription/processing steps



kept for provenance and future conversion workflows (e.g., extracting MP4 clips)













