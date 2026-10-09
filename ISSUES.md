# Issues

The tracker is **GitHub Issues** (`ibrhmahmd/techno-terminal`). The architecture migration epic is #9.

Migrated on 2026-10-09:
- **#1** "Scheduled daily report email does not send" → GitHub **#37**, folded into the notifications migration.
- **#3** "Attendance/group-progression 500s" → GitHub **#38** (closed, fixed in `c678197`). The dependency-pinning follow-up is **#29**.

The entry below stays here on purpose: the repo is public, and it moves to GitHub only after the credentials are rotated.

## #2 — Production DB password exposed in public repo

**Status:** 🔴 OPEN
**Type:** bug (security)
**Created:** 2026-09-25

### Description
`scratch/apply_074.py`, `apply_075.py` and `apply_076.py` (added in `63ae7ad`, 2026-07-10, removed in `f3f34dc`) hardcoded the production Supabase connection string, including its password. The GitHub repo is public. The testing project uses the same password. `archieve/` (student attendance spreadsheets) is also in public history.

### Actions (operational, user-only)
1. Change the database password on both Supabase projects (production and testing `qugffjtucavdseczbata`). Update `.env`, `.env.test` and the FastAPI Cloud env.
2. Decide: make the repo private, rewrite history (`git filter-repo`), or both.
