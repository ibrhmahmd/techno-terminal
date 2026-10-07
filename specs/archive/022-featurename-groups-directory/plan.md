# Implementation Plan: Academics Groups Directory Router Cleanup

## Background & Goal
During the refactor of the Groups Directory module (Spec 021), we consolidated all list/search queries into a single powerful backend function: `filter_groups`. As a result, several legacy convenience endpoints in the router became identical thin wrappers around `filter_groups`.

This plan proposes **Option C: Hybrid Cleanup**, which removes redundant wrappers to reduce API surface area and maintenance, while keeping endpoints that serve fundamentally different response structures or logic.

## Open Questions

> [!WARNING]
> **Frontend Breakage**
> The endpoints marked for deletion are currently part of the public API. Removing them will break any frontend code calling them. Are you comfortable with removing them from the backend now, or do you need me to identify and migrate their frontend call sites first?

## Proposed Changes

We will modify the routers to drop redundant routes and only keep the unified filter engine and distinct structural routes.

### `app/api/routers/academics/group_directory_router.py`

#### Keep (No changes needed)
- `GET /academics/groups/filter` (The core search engine)
- `GET /academics/groups/grouped` (Provides a grouped view matrix)
- `GET /academics/groups/{group_id}/enriched` (Single item fetch)

#### [DELETE] Redundant wrappers
- `GET /academics/groups` (Duplicate of `/filter?status=active`)
- `GET /academics/groups/enriched` (Identical to above)
- `GET /academics/groups/archived` (Duplicate of `/filter?status=archived`)
- `GET /academics/groups/by-course/{course_id}` (Duplicate of `/filter?course_ids=X`)

### `app/api/routers/academics/courses_router.py`

#### [DELETE] Redundant wrappers
- `GET /academics/courses/{course_id}/groups` (Duplicate of `/filter?course_ids=X`)

---

## Verification Plan

### Automated Tests
- Run `pytest tests/test_academics.py` (if environment permits) to ensure no routing conflicts remain.

### Manual Verification
1. Boot the server and check the OpenAPI `/docs` page to confirm the 5 endpoints have been cleanly removed.
2. Verify `GET /academics/groups/filter` properly handles all capabilities previously covered by the deleted endpoints.
