# Implementation Plan: Groups Directory Module Audit

**Branch**: `021-groups-directory-audit` | **Date**: 2026-06-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/021-groups-directory-audit/spec.md`

## Summary

Refactor the Academics Groups Directory API by deleting unused and broken endpoints (`/search`, `/by-type`), routing legacy endpoints (`/`, `/archived`, `/by-course`) through the new `filter_groups` engine, adding pagination to `/enriched`, and extending `GroupFilterDTO` with capabilities like `max_capacity` and `include_inactive` along with an "Active" default status behavior. Fix typed contracts by removing `list[dict]` from `GroupedItem` and removing orphaned DTOs and repository methods.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, SQLModel, PostgreSQL
**Storage**: PostgreSQL
**Testing**: pytest
**Target Platform**: Leapcell / Linux Container
**Project Type**: Web API (Backend)
**Performance Goals**: Pagination required for endpoints returning large arrays (like `/enriched`).
**Constraints**: Follow existing `AGENTS.md` guidelines for dependency injection and typed contracts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Typed Contracts Rule**: Complies. Eliminates `list[dict]` in `GroupedItem` and replaces `PaginatedResponse[GroupListItem]` with DTO-backed returns.
- **Two-Layer Schema Rule**: Complies. DTOs in `modules/academics/group/directory/schemas.py` are distinct from `api/schemas/academics/group.py`.
- **D+ Hybrid Pattern**: Complies. Maintains the directory slice interface boundaries.
- **Dead Code Discipline**: Enforces the removal of broken router endpoints and orphaned functions.

## Project Structure

### Documentation (this feature)

```text
specs/021-groups-directory-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
└── contracts/           # Phase 1 output (/speckit.plan command)
```

**Structure Decision**: Standard Speckit feature directory structure.

## Proposed Changes

### app/api/schemas/academics/
#### [MODIFY] grouped.py
- Change the type of `groups` in `GroupedItem` from `list[dict]` to `list[EnrichedGroupPublic]`.
- Import `EnrichedGroupPublic` from `app.api.schemas.academics.group`.
- Delete `GroupByField` enum if unused elsewhere.

#### [MODIFY] group.py
- Delete `GroupListItem` class completely, as it will be orphaned.

### app/modules/academics/group/directory/
#### [MODIFY] schemas.py
- Add `has_instructor`, `max_capacity_min`, `max_capacity_max`, and `include_inactive` to `GroupFilterDTO`.

#### [MODIFY] repository.py
- Delete the orphaned `get_all_archived_groups()` method.
- Update `filter_groups_query` to implement `has_instructor`, `max_capacity_min`, `max_capacity_max`.
- Implement default "Active only" status filtering behavior when no explicit status is provided, taking `include_inactive` into account.

### app/api/routers/academics/
#### [MODIFY] group_directory_router.py
- Delete `GET /academics/groups/search` completely.
- Delete `GET /academics/groups/by-type/{group_type}` completely.
- Update `GET /academics/groups` to call `svc.filter_groups(GroupFilterDTO(status=["active"]))`. Return `ApiResponse[GroupFilterResultDTO]`.
- Update `GET /academics/groups/archived` to call `svc.filter_groups(GroupFilterDTO(status=["archived"]))`. Return `ApiResponse[GroupFilterResultDTO]`.
- Update `GET /academics/groups/by-course/{course_id}` to call `filter_groups(course_ids=[course_id], status=...)`.
- Update `GET /academics/groups/enriched` to accept `skip` and `limit`, and delegate to `filter_groups`.

## User Review Required

- No breaking changes for consumers of `/academics/groups` except that the response shape upgrades from `GroupListItem` to `EnrichedGroupPublic` (adding more data).
- The `/search` and `/by-type` endpoints will return 404. Clients must use `/filter`.

## Verification Plan

### Automated Tests
- Run `pytest tests/ -v` to ensure no test failures result from the endpoint removals.

### Manual Verification
- Test `GET /academics/groups/enriched` with `limit=5` to verify pagination.
- Test `GET /academics/groups/by-course/1` to verify it returns correctly filtered data.
- Test `GET /academics/groups/filter` with new params (`has_instructor`, `max_capacity_min`).
- Verify endpoints `/search` and `/by-type/{type}` return 404.
