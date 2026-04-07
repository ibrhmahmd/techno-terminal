# Plan: MEMORY_BANK indexing and refresh (completed)

## Goal

Keep [docs/MEMORY_BANK.md](../MEMORY_BANK.md) as the **single agent handoff** reference by reconciling it with:

- The real `app/` tree (modules, UI pages, API)
- Supabase-backed auth and the FastAPI scaffold
- HR / staff management and consolidated Directory UX
- `db/schema.sql`, migrations, and entrypoints (`run_ui.py`, `run_api.py`)

## Outcome

- `MEMORY_BANK.md` describes **dual transport** (Streamlit → services; FastAPI parallel), current sidebar pages, `1_Directory.py`, staff management, and points to `db/README.md` for hybrid SQL + Alembic workflow.
- Subdocs under `docs/memory_bank/**` remain **background**; where they lag the repo, MEMORY_BANK + code win (see MEMORY_BANK §13 drift policy).

## Maintenance

When you change auth, schema version, or primary navigation, update MEMORY_BANK header (date, schema version) and the affected sections in one pass.
