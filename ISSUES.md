# Issues

The tracker is **GitHub Issues** (`ibrhmahmd/techno-terminal`); the roadmap is #111.

This file holds only the security item below. The repo is public, and the item moves to GitHub only after the credentials are rotated.

## #2 — Production DB password exposed in public repo

**Status:** 🔴 OPEN (rotation postponed by the owner: it affects production)
**Type:** bug (security)
**Created:** 2026-09-25

### Description
`scratch/apply_074.py`, `apply_075.py` and `apply_076.py` (added in `63ae7ad`, 2026-07-10, removed in `f3f34dc`) hardcoded the production Supabase connection string, including its password. The GitHub repo is public. The testing project uses the same password. `archieve/` (student attendance spreadsheets) is also in public history.

### Actions (operational, owner-only)
1. Change the database password on both Supabase projects (production and testing). Update `.env`, `.env.test` and the FastAPI Cloud env.
2. Decide: make the repo private, rewrite history (`git filter-repo`), or both.
