# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FastAPI backend + ChromaDB storing vectorized Job Descriptions (JD). README.md (in Vietnamese) has full setup/run details. No linter is configured; the only tests are pytest tests for the taxonomy module (`back_end/tests/`, run `.venv/Scripts/python -m pytest` from `back_end/`).

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
- `app/core/taxonomy.py` + `app/data/taxonomy.json` — standalone in-memory IT skill/position taxonomy (NetworkX `DiGraph`, edges general -> specific, nodes with the same name merge so it can be a DAG). `get_taxonomy()` caches the graph; `resolve()` maps names/aliases to node ids; `relation()`, `skill_match_score()` (specialist covers generalist 0.9^(d-1), generalist vs specialist 0.5^d, siblings 0.5/steps) and `match_skills()` do the graph matching. `extract_terms(text)` pulls taxonomy terms out of free text (longest non-overlapping alias match; short/ambiguous aliases are case-sensitive, see `_UPPER_ONLY_EXTRA`/`_CAPITALIZED`). Taxonomy content comes from `scripts/build_taxonomy.py` (ESCO + curated `JD_TREE` in `scripts/jd_tree.py`) — add aliases there and rebuild instead of editing the JSON. Not wired to any router yet. Alias/name collisions or cycles raise at load time.

## Gotchas

- `chroma_db/` and the dataset are not in git.
