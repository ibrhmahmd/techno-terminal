# Academics Module Architectural Audit

Date: 2026-03-25  
Scope: `app/modules/academics/*` + boundary check against `app/shared/*`  
Baseline references: `docs/MEMORY_BANK.md` (module-per-feature), `docs/memory_bank/04_architecture/01_architecture_decision.md`

## Audit Checklist Results

| Check | Status | Findings |
|---|---|---|
| One service file contains exactly one service class with single responsibility | ❌ Fail | No service class exists; service module is function-based and mixes Course, Group, Session, and analytics responsibilities |
| Repository file is not subdivided by entity blocks | ❌ Fail | Repository is split into Course, Group, Session, and analytics sections in one file |
| DTOs/schemas are separated into one file per entity | ❌ Fail | All academics DTOs are colocated in one schema file |
| Service/repository use strongly-typed DTOs only (no dict contracts) | ❌ Fail | Input unions accept `dict`; several functions return `dict`/`list[dict]` |
| Hard-coded constants extracted into dedicated constants file | ❌ Fail | Time limits, weekdays, status literals, and SQL label literals are hard-coded across service/repository/schema |
| No academics business logic leaks into shared module | ✅ Pass (with boundary risk) | No direct academics rule implementation in shared; shared holds cross-domain helpers. Boundary risk: academics-specific constants are split between module and shared |
| Helper utilities isolated to dedicated helpers directory outside core logic layers | ❌ Fail | Internal helper functions are embedded in service; no helpers directory exists |

## Violations Catalog

| ID | Rule | Severity | File | Lines | Evidence | Recommended Refactor |
|---|---|---|---|---|---|---|
| A-001 | Single service class + SRP | Critical | `app/modules/academics/academics_service.py` | 55-388 | One module orchestrates course creation, group scheduling, session lifecycle, level progression, and analytics projections | Introduce explicit services: `CourseService`, `GroupService`, `SessionService` under `services/`; keep each class focused and injectable |
| A-002 | Single service class required | High | `app/modules/academics/academics_service.py` | 1-388 | No service class present; functional API cannot enforce class-level responsibility boundaries | Create one service class per responsibility area and keep module exports as facades only for backward compatibility |
| A-003 | Repository not subdivided by entity segments | High | `app/modules/academics/academics_repository.py` | 6, 35, 123, 208 | File is explicitly partitioned into course/group/session/analytics repository blocks | Split into `course_repository.py`, `group_repository.py`, `session_repository.py`, `course_stats_repository.py` or unify behind a single class with cohesive boundaries |
| A-004 | Repository layering consistency | Medium | `app/modules/academics/academics_repository.py` | 125 | Mid-file import of `CourseSession` indicates non-cohesive structure and layering drift | Move imports to top and isolate repository per entity to avoid intra-file phase ordering |
| A-005 | DTO/schema per-entity file | High | `app/modules/academics/academics_schemas.py` | 17-112 | Course, Group, Session create/update DTOs all share one file | Split into `course_dto.py`, `group_dto.py`, `session_dto.py` (or `schemas/course.py`, `schemas/group.py`, `schemas/session.py`) |
| A-006 | DTO layer must not depend on service layer (DIP/SOLID) | Critical | `app/modules/academics/academics_schemas.py` | 52-53 | `ScheduleGroupInput` imports `_validate_times` from service, creating reverse dependency from DTO to service | Move time-window validation into DTO-local validator helper (or `academics/helpers/time_rules.py`) and let service depend on DTO/helpers, not vice versa |
| A-007 | Strongly typed contracts only (no dict inputs) | High | `app/modules/academics/academics_service.py` | 55-59, 162, 170-171 | `add_new_course` and `schedule_group` accept `... | dict` and branch with `isinstance(data, dict)` | Remove dict unions; enforce DTO-only signatures and convert at call sites (UI/API boundary) |
| A-008 | Strongly typed contracts only (no dict outputs) | High | `app/modules/academics/academics_service.py` | 104, 114, 222, 228 | Service returns `list[dict]` / `dict | None` for stats/enriched data | Define typed read DTOs (`CourseStatsDTO`, `EnrichedGroupDTO`) and return those instead |
| A-009 | Strongly typed contracts only (repository) | High | `app/modules/academics/academics_repository.py` | 74, 95, 98, 120, 211, 228, 231, 249 | Repository maps rows to dictionaries and exposes dict contracts | Introduce row-mapper DTOs and repository return types as typed models/dataclasses |
| A-010 | Extract hard-coded constants into dedicated constants file | Medium | `app/modules/academics/academics_service.py` | 14-25, 45-46 | Time window (`11:00 AM-9:00 PM`) and weekdays hard-coded in service | Create `app/modules/academics/constants.py` with `ACADEMICS_EARLIEST_START`, `ACADEMICS_LATEST_END`, `ACADEMICS_WEEKDAYS`, and message templates |
| A-011 | Extract hard-coded constants into dedicated constants file | Medium | `app/modules/academics/academics_repository.py` | 48, 58, 81, 91, 105, 116, 224, 244 | Status and fallback literals (`"active"`, `"Unassigned"`, `v_course_stats`) are embedded in SQL/query logic | Replace repeated literals with module-level constants and query-builder constants object |
| A-012 | Extract hard-coded constants into dedicated constants file | Low | `app/modules/academics/academics_schemas.py` | 11-14 | Weekday literals duplicated in schema while service keeps a separate weekday list | Reuse one canonical weekday constant/type alias from `academics/constants.py` |
| A-013 | Helpers isolated outside core logic files | Medium | `app/modules/academics/academics_service.py` | 30-42, 127-159 | `_fmt_12h`, `_next_weekday`, `_validate_times`, `_create_sessions_in_session` are embedded in service module | Move pure helpers to `app/modules/academics/helpers/` (`time_helpers.py`, `session_planning.py`) and keep orchestration in service classes |

## Shared Module Boundary Check

- No direct academics business rules were found in `app/shared/audit_utils.py`, `app/shared/validators.py`, or `app/shared/exceptions.py`.
- Shared code currently remains cross-domain and generic.
- Boundary risk to monitor:
  - `app/shared/constants.py` includes academics constant aliases (`GroupStatus`) while academics module also carries local hard-coded constants. This split weakens single-source-of-truth for academics rules.

## SOLID-Oriented Findings Summary

- **SRP violated**: one service module handles multiple business subdomains and read-model shaping.
- **DIP violated**: DTO layer imports service helper (`academics_schemas.py` -> `academics_service.py`).
- **OCP pressure**: adding new scheduling rules currently requires touching service internals and schema cross-import paths.
- **ISP/LSP**: not directly violated by current evidence in this module.

## Refactor Steps (Recommended Sequence)

1. Create module boundaries:
   - `app/modules/academics/services/`
   - `app/modules/academics/repositories/`
   - `app/modules/academics/schemas/`
   - `app/modules/academics/helpers/`
   - `app/modules/academics/constants.py`
2. Introduce typed read DTOs for enriched/statistical queries; remove all `dict` return contracts.
3. Remove dict input unions from service signatures and normalize conversion only at UI/API edge.
4. Decouple schema validators from service helpers (eliminate reverse imports).
5. Keep temporary compatibility adapters in `academics/__init__.py`, then deprecate once call sites are migrated.

## Discussion Outcomes (Assumptions Validated)

- **Enforcement scope**: academics-first rollout.
- **Compatibility strategy**: adapter transition (temporary facade functions during migration).
- **Typed read-model standard**: Pydantic DTOs for enriched/statistical projections.
- **Primary performance focus**: query efficiency first (indexes, SQL shape, N+1 prevention).

## Trade-offs and Impact Analysis

### Short-term trade-offs

- Slower feature throughput in academics during migration windows due to contract and file-boundary updates.
- Temporary dual-path complexity while adapter facades and new typed DTO signatures coexist.
- Additional review overhead for strict architecture compliance checks.

### Long-term trade-offs

- Lower coupling and clearer responsibility boundaries, reducing regression risk for future feature work.
- Better API-readiness because service/repository boundaries expose explicit typed contracts.
- Improved maintainability and onboarding due to predictable per-entity file layout.

### Feature-development impact

- Existing features remain stable via adapters while call sites migrate incrementally.
- New academics features can be developed directly against class-based services and typed DTOs without further legacy expansion.
- Cross-module integrations become safer because dictionary-shaped implicit contracts are replaced with explicit DTO models.

### Performance implications

- Minor runtime overhead from Pydantic DTO validation.
- Major performance outcomes still depend on SQL/query shape; this remains the top optimization axis.
- Repository split does not materially degrade runtime if import graph remains clean and query plans stay optimized.

## Finalized Refactoring Roadmap

1. **Foundation**: add `academics/constants.py`, `academics/helpers/`, and DTO read models (Pydantic).
2. **Boundary cleanup**: remove schema -> service reverse import; move time validation helper into helpers/constants.
3. **Contract migration**: remove dict input unions from services; migrate UI/API call sites through adapter functions.
4. **Repository split**: separate entity repositories and stats repository; preserve query behavior and transaction semantics.
5. **Service split**: introduce `CourseService`, `GroupService`, `SessionService`; keep public compatibility exports temporarily.
6. **Adapter retirement**: remove deprecated function signatures after all call sites use typed DTO contracts.

## Severity Legend

- **Critical**: Architecture rule violation with immediate maintainability/coupling risk.
- **High**: Strong deviation from target architecture or typing contract.
- **Medium**: Structural drift with manageable short-term impact.
- **Low**: Consistency or duplication issue with limited immediate risk.
