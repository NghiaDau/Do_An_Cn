# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FastAPI backend + ChromaDB storing vectorized Job Descriptions (JD). README.md (in Vietnamese) has full setup/run details. No tests or linter are configured.

## Commands

All run from `back_end/` (use `.venv/bin/python` on macOS/Linux):

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/embed_jd.py --limit 1000      # embed JDs into ChromaDB (omit --limit for all; --reset wipes collection first)
.venv/Scripts/python run.py                                 # API on :8000, Swagger at /docs
.venv/Scripts/chroma run --path chroma_db                   # optional Chroma UI server
```

## Architecture

- `app/main.py` — FastAPI app (open CORS), mounts routers in `app/routers/` (`health`, `jobs`).
- `app/core/chroma.py` — single source of the Chroma client/collection (`job_descriptions`, cosine space). Uses `PersistentClient` on `back_end/chroma_db/` by default; if `CHROMA_HOST` (and optional `CHROMA_PORT`, default 8000) is set, uses `HttpClient` instead. Never have the ingest script and a `chroma run` server write to the same directory without `CHROMA_HOST`, or the data can corrupt. If running `chroma run` alongside FastAPI, move Chroma to another port (e.g. 8001) and set `CHROMA_PORT`.
- `scripts/embed_jd.py` — reads `back_end/data_set/job_descriptions/job_descriptions.csv` (gitignored; built from the parquet by `scripts/make_csv.py`) in chunks, embeds `Long Description` with `Alibaba-NLP/gte-modernbert-base` (8192-token context, 768-dim; config in `app/core/embedding.py`), and adds to Chroma with metadata (`position`, `company`, `keyword`, `exp_years`, `english_level`, `english_level_num`). Resumable: ids already in the DB are skipped.
- `routers/jobs.py`: `GET /jobs` and `/jobs/{id}` read via `col.get` (full `description`); `GET /jobs/search` is hybrid search — embeds `q` with `embed_query` (`app/core/embedding.py`, model cached via `get_model()`, loaded at startup in `main.py` lifespan before the server reports ready) then `col.query` with a `where` built from `keyword`, `company`, `min/max_exp` (`exp_years`) and `min/max_english` (`english_level_num`). `/jobs/search` must stay declared before `/jobs/{job_id}`.

## Gotchas

- `chroma_db/` and the dataset are not in git.
