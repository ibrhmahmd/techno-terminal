# Implementation Plan: Groups Day Order & Search Filter

**Branch**: `020-groups-filter-day-order` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/020-groups-filter-day-order/spec.md`

## Summary

Two work items: (1) Fix the grouped-by-day endpoint to sort weekdays in Arabic/Islamic order (Friday→Thursday) instead of alphabetical, (2) Add a multi-criteria filter/search endpoint `GET /academics/groups/filter` following the student filter pattern (raw SQL with dynamic WHERE clauses, pagination, sorting, typed DTOs).

## Technical Context

**Language/Version**: Python 3.10+ (FastAPI 0.112+, SQLModel 0.0.16+)
**Primary Dependencies**: FastAPI, SQLModel/psycopg2, Pydantic, python-jose (JWT)
**Storage**: PostgreSQL (Supabase), pool_size=10+5, sslmode=require
**Testing**: pytest with TestClient, mock JWTs via `tests/utils/jwt_mocks.py`
**Target Platform**: Linux server (Leapcell/Railway), REST JSON API
**Project Type**: web-service (backend-only, FastAPI)
**Performance Goals**: Filter queries return <500ms for typical center (50-200 groups)
**Constraints**: Existing auth (Supabase JWT), typed DTOs only (no `-> dict`), D+ Hybrid slice structure
**Scale/Scope**: ~20-200 groups per center, single-tenant per deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Gate I (Layer Separation)**: ✅ PASS — Filter endpoint follows existing student filter pattern: router (HTTP/Pydantic) → service (raw SQL/text()) → typed DTOs. Day ordering fix lives in `directory/service.py`, using constant from `academics/constants.py`.

**Gate II (Module Organization)**: ✅ PASS — Day-order mapping constant added to existing `academics/constants.py`. Filter uses existing `group/directory/` slice (no new slices needed). No model changes.

**Gate III (Typed Contracts)**: ✅ PASS — `GroupFilterDTO` (Input), `GroupFilterResultDTO`/`GroupFilterItemDTO` (Output). All return types are named models with `from_attributes=True`.

**Gate IV (Response Envelope)**: ✅ PASS — Uses existing `ApiResponse`/`PaginatedResponse` envelope from `app/api/schemas/common.py`.

**Gate V (Auth)**: ✅ PASS — Filter endpoint guarded by `require_any` (consistent with all other directory endpoints in `group_directory_router.py`).

**Gate VI (Router Registration)**: ✅ PASS — No new router files needed; filter endpoint added to existing `group_directory_router` (registered before `groups_router` already).

## Project Structure

### Documentation (this feature)

```text
specs/020-groups-filter-day-order/
├── plan.md              # This file
├── research.md          # Phase 0 — resolved unknowns
├── data-model.md        # Phase 1 — DTO schemas + constants
├── quickstart.md        # Phase 1 — dev instructions
├── contracts/           # Phase 1 — API contracts
│   ├── filter_request.md
│   └── filter_response.md
└── tasks.md             # Task checklist
```

### Source Code (repository root)

```text
app/
├── modules/
│   └── academics/
│       ├── constants.py                        # + DAY_ORDER sort mapping
│       └── group/
│           └── directory/
│               ├── interface.py                # + filter_groups() method
│               ├── service.py                  # + filter_groups() impl + day-order sort fix
│               ├── repository.py               # + filter_groups_query() raw SQL function
│               └── schemas.py                  # + GroupFilterDTO + GroupFilterResultDTO
├── api/
│   ├── routers/
│   │   └── academics/
│   │       └── group_directory_router.py       # + GET /academics/groups/filter endpoint
│   └── dependencies.py                         # unchanged (existing factory used)
└── shared/
    └── constants.py                            # unchanged (DAY_ABBREV_MAP stays in crm router)

tests/
├── test_academics_groups.py                    # + test_groups_filter_* tests
└── conftest.py                                 # unchanged (existing fixtures suffice)
```

**Structure Decision**: Day-ordering fix touches 2 files (`constants.py` + `directory/service.py` line 147). Filter adds to 4 existing files in `group/directory/` slice + router. No new slices, modules, or models.

## Proposed Changes

### Fix 1 — Day Order Sort (1-line fix)

#### [MODIFY] constants.py
- Add `DAY_ORDER: dict[str, int]` — Arabic/Islamic week order: `{Friday:0, Saturday:1, Sunday:2, Monday:3, Tuesday:4, Wednesday:5, Thursday:6}`

#### [MODIFY] directory/service.py
- Line ~147: Replace `all_items.sort(key=lambda x: x.label)` with `all_items.sort(key=lambda x: DAY_ORDER.get(x.label, 99))`
- Import `DAY_ORDER` from `academics.constants`

### Fix 2 — Groups Filter Endpoint

#### [MODIFY] directory/schemas.py
- Add `GroupFilterDTO` — 24-field input DTO (q, course_ids, day, instructor_name, status, sort_by, sort_order, skip, limit, + advanced fields)
- Add `GroupFilterResultDTO` — output DTO with `groups: list[EnrichedGroupDTO]`, `total`, `skip`, `limit`

#### [MODIFY] directory/repository.py
- Add `filter_groups_query(session, filters: GroupFilterDTO) -> tuple[list[EnrichedGroupDTO], int]`
- Base: enriched groups SQL (same SELECT as `get_enriched_groups`)
- Dynamic WHERE: each filter param appends a clause only when not None
- Day normalization: uses `DAY_ABBREV_MAP` (replicated from crm router into `academics/constants.py`)
- Count query: `SELECT COUNT(*) FROM (base_query) AS sub`

#### [MODIFY] directory/service.py
- Add `filter_groups(filters: GroupFilterDTO) -> GroupFilterResultDTO`
- Thin delegation: `with get_session() as session: return repo.filter_groups_query(session, filters)`

#### [MODIFY] directory/interface.py
- Add `filter_groups(filters: GroupFilterDTO) -> GroupFilterResultDTO` to `GroupDirectoryServiceInterface` Protocol

#### [MODIFY] group_directory_router.py
- Add `GET /academics/groups/filter` before `/{group_id}` routes
- Query params mirror `GroupFilterDTO` fields (FastAPI auto-validates)
- Day param: accepts list, normalized via inline helper (same pattern as student filter)
- Auth: `require_any` (consistent with other directory endpoints)
- Response: `ApiResponse[GroupFilterResultDTO]`

## Complexity Tracking

No constitution violations. Complexity tracking not required.
