# SOLID Module Architecture Guide & Debugging Checklist

A comprehensive guide for designing and refactoring backend modules following clean architecture principles. Incorporates lessons from the CRM, Finance, and Academics module refactoring projects.

---

## Part 0: Architecture Pattern Selection

Before writing a single line, choose the structural pattern for your module. Wrong pattern choice is the most expensive mistake to fix later.

### The Four Patterns

| Pattern | Unit of Organization | Best For |
|---------|---------------------|----------|
| **A — Horizontal Layer (N-Tier)** | Technical layer (services/, repositories/, etc.) | Small modules, ≤3 entities, minimal complexity |
| **B — Vertical Slice** | Single entity or workflow | Modules with distinct entities that rarely share logic |
| **C — Bounded Context (DDD-Lite)** | Business capability (what the system does) | Large teams, stable domains, microservice candidates |
| **D+ — Hybrid Vertical Slice** | Entity namespace with sub-slices | Growing modules with 1 core entity having multiple workflow concerns |

### Pattern Selection Framework

Answer these questions in order:

```
1. How many distinct entities does this module manage?
   └─ ≤2 entities → Use Pattern A (Horizontal Layer)
   └─ 3+ entities → Continue to Q2

2. Do the entities share significant business logic or repositories?
   └─ No → Use Pattern B (Vertical Slice, one dir per entity)
   └─ Yes → Continue to Q3

3. Is there a single "core entity" with 5+ distinct workflow concerns around it?
   └─ Yes → Use Pattern D+ (Hybrid: entity namespace with sub-slices)
   └─ No → Use Pattern C (Bounded Context: group by capability)

4. Will separate teams own different parts of this module?
   └─ Yes → Use Pattern C (team-per-context)
   └─ No → D+ is preferred over C
```

### D+ Hybrid Vertical Slice — The Recommended Pattern for Complex Modules

When a module has one dominant entity (e.g., `Group`) with many distinct concerns, nest sub-slices under an entity namespace:

```
module/
├── models/                  ← Shared SQLModel entities (horizontal, cross-slice)
├── helpers/                 ← Pure utilities (horizontal, cross-slice)
├── constants.py
├── other_entity/            ← Simple entities get a flat slice
│   ├── interface.py
│   ├── service.py
│   ├── repository.py
│   └── schemas.py
└── core_entity/             ← Complex entity gets sub-slices
    ├── __init__.py
    ├── core/                ← CRUD + targeted writes on single record
    ├── directory/           ← Collection reads (list, search, filter, group-by)
    ├── lifecycle/           ← Atomic multi-entity orchestration
    ├── details/             ← Read-heavy composite views
    ├── analytics/           ← History and reporting reads
    └── domain_concern/      ← Any additional bounded concern
```

**Why `models/` stays horizontal (not sliced):**  
SQLModel entities are registered with the ORM at import time. If models live inside a slice, a foreign module importing the entity would need to know the slice path — creating coupling. Models are infrastructure, not domain logic.

---

## Part 1: Vertical Slice Anatomy

Every slice (directory) contains exactly these files:

```
{slice_name}/
├── __init__.py      ← slice-level exports (what's public from this slice)
├── interface.py     ← Protocol definitions ONLY (no logic)
├── service.py       ← Business logic class
├── repository.py    ← Database access functions (if slice has DB operations)
└── schemas.py       ← Input DTOs + Output DTOs for this slice
```

### File Responsibilities

| File | Contains | Must NOT Contain |
|------|----------|-----------------|
| `interface.py` | `Protocol` class with method signatures only | Imports from `services/`, logic, `__init__` |
| `service.py` | Business logic methods | SQL queries, `select()`, `session.exec()` |
| `repository.py` | SQL queries, ORM calls | Business rules, validation, orchestration |
| `schemas.py` | Pydantic `BaseModel` DTOs | ORM models, service logic |
| `__init__.py` | `from .service import X` re-exports | Logic, class definitions |

### The One Rule That Prevents All Circular Imports

```
interface.py  →  can import from: schemas.py, models/
schemas.py    →  can import from: models/, shared.constants
repository.py →  can import from: models/, constants.py, shared
service.py    →  can import from: repository.py, schemas.py, interface.py, helpers/, constants.py
                                  + other slices' schemas (NOT other slices' services)
```

Services in the same module **never import each other's service classes directly**. Cross-slice service communication goes through the module's root `__init__.py`.

---

## Part 2: Interface Design Standard

### File Structure

```python
"""
app/modules/{module}/{slice}/interface.py
─────────────────────────────────────────
Interfaces for the {SliceName} slice.
"""
from typing import Protocol, runtime_checkable
from app.modules.{module}.{slice}.schemas import OutputDTO


@runtime_checkable
class {Concept}ServiceInterface(Protocol):
    """Contract for {description of what this service does}."""

    def method_name(self, arg: InputDTO) -> OutputDTO: ...
    def another_method(self, id: int) -> EntityType | None: ...


@runtime_checkable  
class {Concept}RepositoryInterface(Protocol):
    """Contract for {description of what this repository does}."""

    def get_by_id(self, id: int) -> EntityType | None: ...
    def create(self, entity: EntityType) -> EntityType: ...
```

### Interface Rules

1. **`@runtime_checkable`** on every interface — enables `isinstance(service, Interface)` in tests.
2. **Method bodies are `...`** — no default implementations.
3. **Name suffix: `Interface`** — never `Protocol`, never `I` prefix (e.g., `GroupLifecycleServiceInterface` not `IGroupLifecycleService`).
4. **Import only from same slice's `schemas.py` or `models/`** — never from other slices' service files.
5. **Every public service method must appear in the interface** — the interface is the contract, not a subset.

---

## Part 3: The Dead Code Audit (Pre-Migration Mandatory Step)

Before any migration begins, audit for dead code. Every item found must be deleted with no migration path.

### Audit Checklist

```powershell
# 1. Find all methods defined but never called
grep -r "def method_name" ./app --include="*.py"     # Find callers

# 2. Find dict return types (all are tech debt)
grep -r "-> dict\|-> list\[dict\]" ./app/modules/{module} --include="*.py"

# 3. Find raw tuple returns (all are tech debt)
grep -r "-> tuple\b" ./app/modules/{module} --include="*.py"

# 4. Find inverted imports (service importing from API layer)
grep -r "from app.api.schemas" ./app/modules --include="*.py"

# 5. Find TODO markers (each is a confirmed debt item)
grep -r "#TODO\|# TODO" ./app/modules/{module} --include="*.py"

# 6. Find duplicate definitions
grep -r "class WeekDay\|WeekDay = Literal" ./app/modules/{module} --include="*.py"

# 7. Find Protocol/legacy aliases (shims kept for backward compat)
grep -r "get_by_id =\|create =\|list_all =" ./app/modules/{module} --include="*.py"
```

### Dead Code Taxonomy

| Category | Example | Decision |
|----------|---------|----------|
| **Dead method** | Method A is a subset of Method B; router calls B | Delete A |
| **Duplicate method** | Same name defined twice in same class | Delete older one |
| **Architectural violation** | Session service handling group lifecycle | Delete, no migration |
| **Legacy alias** | `get_by_id = get_course_by_id` | Delete |
| **Untyped return** | `-> dict`, `-> list[dict]`, bare `tuple` | Replace with typed DTO |
| **Inverted import** | Service importing from `app.api.schemas` | Move DTO to module layer |
| **Facade anti-pattern** | `repositories/__init__.py` re-exporting all functions | Delete after direct imports established |

### Zero Tolerance Rule

> Dead code is not "safe" to keep. It accumulates confusion, hides real logic, and becomes a breeding ground for bugs when future developers accidentally call it. **Delete it. Always. Immediately.**

---

## Part 4: Schema Layer Ownership

### Rule: Schemas Follow Their Slice

Every DTO lives in the `schemas.py` of the slice that **creates or owns** it.

```
group/lifecycle/schemas.py   ← owns ProgressLevelDTO, GroupCreationResult
group/directory/schemas.py   ← owns EnrichedGroupDTO, GroupedGroupsResult
group/details/schemas.py     ← owns LevelDetailDTO, AttendanceGridDTO
```

### The Two-Layer Rule

| Where | Contains | Never Contains |
|-------|----------|---------------|
| `modules/{module}/{slice}/schemas.py` | All module DTOs (input, output, internal) | Generic envelopes |
| `app/api/schemas/common.py` | `ApiResponse[T]`, `PaginatedResponse[T]` | Module-specific shapes |
| `app/api/schemas/{module}/` | API-specific shapes ONLY when they differ from service output | Module DTOs |

**Anti-pattern:** Service imports from `app.api.schemas.*` — this inverts the dependency direction. The service layer must be independent of the API layer.

### DTO Naming Convention

| Purpose | Pattern | Example |
|---------|---------|---------|
| Service input | `{Operation}{Entity}Input` | `ScheduleGroupInput`, `CreateGroupWithLevelDTO` |
| Service output / result | `{Entity}{Operation}Result` | `GroupCreationResult`, `LevelProgressionResult` |
| Read model / view | `{Entity}{Qualifier}DTO` | `EnrichedGroupDTO`, `GroupLevelDetailDTO` |
| Internal contract | `{Operation}DTO` | `ProgressLevelDTO`, `MigrateEnrollmentsDTO` |
| API adapter wrapper | `{Entity}{Operation}Response` (in `api/schemas/`) | `ProgressGroupLevelResponse` |

---

## Part 5: The 9-Phase Migration Playbook

### Phase 0 — Dead Code Deletion (MANDATORY FIRST)

Never migrate dead code into a new structure. Delete first.

1. Run the full dead code audit (Part 3).
2. Confirm zero callers for each item via `grep`.
3. Delete. No backward compatibility shims.
4. Run: `python -c "from app.modules.{module} import *"` — must not raise `ImportError`.

### Phase 1 — Directory Scaffolding

Create all slice directories and empty `__init__.py` files. No logic moved yet.  
The old layer folders (`services/`, `repositories/`, etc.) remain intact.

### Phase 2–N — Slice-by-Slice Migration

For each slice (bottom-up, from least-dependent to most-dependent):

1. `schemas.py` first — no dependencies inside the slice
2. `interface.py` second — depends only on `schemas.py`
3. `repository.py` third — depends on `models/` and `schemas.py`
4. `service.py` last — depends on `repository.py`, `schemas.py`, `interface.py`
5. `__init__.py` — re-export what external callers need

### Phase N+1 — Router Import Updates

Update all routers to import through the module root `__init__.py`.  
Never let routers import from internal slice paths (`from app.modules.academics.group.lifecycle.service import ...`).

### Phase N+2 — Module `__init__.py` Rebuild

Follow the finance module pattern: export everything from root.

```python
# Models
from .models import EntityA, EntityB

# Services (all slices)
from .slice_a.service import SliceAService
from .slice_b.service import SliceBService

# Schemas (all publicly-used DTOs)
from .slice_a.schemas import InputDTO, OutputDTO

# Interfaces (all)
from .slice_a.interface import SliceAServiceInterface

__all__ = [...]  # Explicit — no implicit star exports
```

### Phase N+3 — Old Layer Deletion

Delete `services/`, `repositories/`, `schemas/`, `interfaces/` (the old horizontal layers).  
Verify before deleting:

```powershell
# Must return zero results
grep -r "from app.modules.{module}.services" ./app --include="*.py"
grep -r "from app.modules.{module}.repositories" ./app --include="*.py"
grep -r "from app.modules.{module}.schemas" ./app --include="*.py"
```

### Phase N+4 — Final Verification

```powershell
# Module imports cleanly
python -c "from app.modules.{module} import *; print('OK')"

# Server starts
uvicorn app.api.main:app --reload

# No inverted imports
grep -r "from app.api.schemas" ./app/modules --include="*.py"

# No dict/tuple returns
grep -r "-> dict\|-> list\[dict\]" ./app/modules/{module} --include="*.py"

# All tests pass
pytest tests/ -v
```

---

## Part 6: Cross-Slice Dependency Rules

### What Slices Can Import From Each Other

```
group/analytics/service.py  →  CAN import from: group/lifecycle/repository.py (reads history)
group/lifecycle/service.py  →  CAN import from: group/level/repository.py, session/repository.py
group/details/service.py    →  CAN import from: session/repository.py, group/level/repository.py
```

**Repositories can be imported across slices** — they are stateless query functions.  
**Services cannot import other services in the same module** — that creates hidden orchestration and circular dependencies.

### Shared Repository Placement Decision

When a repository is used by multiple slices:
- Identify which slice **owns the write path** (creates/updates the data).
- Place the repository in that slice.
- Other slices import from the owning slice's `repository.py`.

```python
# group/analytics/service.py — reads history written by lifecycle
from app.modules.academics.group.lifecycle.repository import get_group_levels_with_details
```

This is an **explicit cross-slice import** — allowed at the repository level, visible, trackable.

---

## Part 7: Naming Conventions

| Layer | Convention | Example |
|-------|------------|---------|
| Models | `{Entity}` | `Group`, `GroupLevel`, `CourseSession` |
| Repository functions | `{verb}_{entity}_{qualifier}` | `get_group_by_id`, `list_all_active_groups`, `create_group` |
| Service classes | `{Entity}{Concern}Service` | `GroupCoreService`, `GroupDirectoryService`, `GroupLifecycleService` |
| Interface | `{Entity}{Concern}Interface` | `GroupLifecycleServiceInterface`, `GroupDirectoryInterface` |
| Input DTOs | `{Operation}{Entity}Input` or `{Operation}{Entity}DTO` | `ScheduleGroupInput`, `CreateGroupWithLevelDTO` |
| Output/Result DTOs | `{Entity}{Operation}Result` | `GroupCreationResult`, `LevelProgressionResult` |
| Read models | `{Entity}{Qualifier}DTO` | `EnrichedGroupDTO`, `GroupLevelDetailDTO` |
| Slice directory | `{entity_name}/` or `{entity}_{concern}/` | `group/`, `group/lifecycle/`, `group/directory/` |

**Suffix rules:**
- `Interface` — not `Protocol`, not `I`-prefix
- `DTO` — for input/internal contracts
- `Result` — for operation outcomes
- `Input` — for validated API entry points

---

## Part 8: Common Violations & Fixes

### Violation 1: Loose Return Types

**Bad:**
```python
def get_competitions(group_id: int) -> list[dict]:
def get_enrollment_stats(group_id: int) -> dict:
def get_instructors_summary(group_id: int) -> Sequence[tuple]:
```

**Good:**
```python
def get_competitions(group_id: int) -> list[CompetitionParticipationDTO]:
def get_enrollment_stats(group_id: int) -> GroupEnrollmentStatsDTO:
def get_instructors_summary(group_id: int) -> list[InstructorSummaryDTO]:
```

---

### Violation 2: Service Importing from API Layer

**Bad (inverted import):**
```python
# group_analytics_service.py
from app.api.schemas.academics.group_analytics import GroupAnalyticsDTO  # WRONG
```

**Good:**
```python
# group/analytics/service.py
from app.modules.academics.group.analytics.schemas import GroupAnalyticsDTO  # CORRECT
```

---

### Violation 3: Repositories/__init__.py Facade

**Bad (flat facade — encourages monolithic imports):**
```python
# repositories/__init__.py
from .group_repository import create_group, get_group_by_id, search_groups, ...
from .session_repository import create_session, list_sessions, ...
# 50+ functions from 8 files
```

**Good (direct slice imports):**
```python
# In service file
from app.modules.academics.group.core.repository import get_group_by_id
from app.modules.academics.session.repository import create_session
```

---

### Violation 4: Dead Code Preservation

**Bad:**
```python
def progress_group_level(self, ...):
    """
    DEPRECATED: Use GroupLifecycleService.progress_to_next_level() instead.
    Kept for backward compatibility.
    """
    ...  # 120 lines of dead logic
```

**Good:** Delete. Zero lines.

---

### Violation 5: Subset Method Overlap

**Symptom:** Method A does steps 1–3. Method B does steps 1–3 + 4 + 5. Both exist. Only B is called.

**Bad:**
```python
class GroupLevelService:
    def complete_current_level(self):  # steps 1-3 only
        ...

class GroupLifecycleService:
    def progress_to_next_level(self):  # steps 1-3-4-5 (superset)
        ...
```

**Good:** Delete `complete_current_level()`. It is dead — the router only calls `progress_to_next_level()`.

---

### Violation 6: Duplicate DTO Definitions

**Symptom:** `WeekDay = Literal[...]` defined in two schema files.

**Bad:**
```python
# scheduling_dtos.py
WeekDay = Literal["Monday", "Tuesday", ...]

# group_schemas.py
WeekDay = Literal["Monday", "Tuesday", ...]  # DUPLICATE
```

**Good:** Define once in the most foundational schema file (`group/core/schemas.py`). All other files import it:
```python
from app.modules.academics.group.core.schemas import WeekDay
```

---

## Part 9: Common Pitfalls

### Pitfall 1: SQLAlchemy 2.0 Aggregate Queries Return Row Tuples

**Error:** `pydantic_core.ValidationError: Input should be a valid integer [input_value=(5,)]`

**Root Cause:** `.one()` returns `Row` tuple `(5,)` not `int`.

**Fix:**
```python
# WRONG
total = session.exec(select(func.count())).one()

# CORRECT
total = session.exec(select(func.count())).scalar() or 0
```

**SQLAlchemy 2.0 Method Cheat Sheet:**

| Method | Returns | Use Case |
|--------|---------|----------|
| `.scalar()` | Single value | `func.count()`, `func.sum()` |
| `.scalars().all()` | `list[Model]` | List of ORM objects |
| `.scalars().first()` | `Model or None` | Optional single ORM result |
| `.one()` | `Row` tuple | Multi-column row |
| `.first()` | `Row or None` | Optional multi-column row |

---

### Pitfall 2: Inline Imports in Router Endpoints

**Error:** Ruff: `Module level import not at top of file`

**Fix:** All imports at file top. Use `TYPE_CHECKING` for circular-import-only cases.

---

### Pitfall 3: DTOs Without `from_attributes` Config

**Error:** `ValidationError: Input should be a valid dictionary [input_value=<OrmObject>]`

**Fix:**
```python
class GroupLevelDetailDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Required for ORM → DTO
    id: int
    ...
```

**Rule:** Every DTO that receives data from an ORM model needs `from_attributes=True`.

---

### Pitfall 4: Boolean Comparisons in SQLAlchemy

**Bad:** `stmt = select(Group).where(Group.is_active == True)`

**Good:** `stmt = select(Group).where(Group.is_active.is_(True))`

---

### Pitfall 5: Service Constructor Importing Concrete Implementations

**Bad (tight coupling):**
```python
class GroupLifecycleService:
    def __init__(self):
        self.level_svc = GroupLevelService()    # concrete import
        self.session_svc = SessionService()     # concrete import
```

**Good (injected, testable):**
```python
class GroupLifecycleService:
    def __init__(
        self,
        level_svc: GroupLevelServiceInterface | None = None,
        session_svc: SessionServiceInterface | None = None,
    ):
        self.level_svc = level_svc or GroupLevelService()    # injectable
        self.session_svc = session_svc or SessionService()   # injectable
```

---

### Pitfall 6: Migrating Dead Code Into New Structure

**Symptom:** You copy `GroupLevelService.complete_current_level()` into `group/level/service.py` because "it might be needed later."

**Prevention:** Run grep audit before every migration phase. If a method has zero callers, it does not move. It dies.

---

### Pitfall 7: Router Importing from Internal Slice Paths

**Bad:**
```python
# groups_router.py
from app.modules.academics.group.lifecycle.service import GroupLifecycleService
```

**Good:**
```python
# groups_router.py
from app.modules.academics import GroupLifecycleService
```

Routers import from the module root only. Internal slice paths are implementation details.

---

## Part 10: Decision Matrix

| Scenario | Pattern | Rationale |
|----------|---------|-----------|
| Module with ≤2 entities | Horizontal Layer (A) | Overhead not justified |
| Module with 3+ distinct entities | Vertical Slice (B) | Clear per-entity ownership |
| Single entity with 5+ workflow concerns | Hybrid D+ | Sub-slices under entity namespace |
| Large team, multiple owners | Bounded Context (C) | Team-per-context ownership |
| Service has only read operations | `directory/` or `query/` sub-slice | Read-write separation |
| Method exists but has zero callers | Delete | Zero tolerance for dead code |
| Return type is `dict` | Create typed DTO | Every return type must be a named model |
| Service imports from `app.api.schemas` | Move DTO to module layer | Inverted dependency — always fix |
| Two methods doing 80% the same thing | Delete the subset method | Duplication hides dead code |
| Repository used by two slices | Place in slice that owns write path | Other slices import explicitly |

---

## Part 11: Quick Reference Checklist

### Before Refactoring
- [ ] Run dead code audit (grep for callers of every method)
- [ ] Identify all `-> dict`, `-> list[dict]`, `-> tuple` returns
- [ ] Find all `from app.api.schemas` in module services
- [ ] Identify duplicate DTO definitions across schema files
- [ ] Choose the right architecture pattern (Part 0 framework)

### During Refactoring
- [ ] Delete dead code before migrating anything
- [ ] Migrate bottom-up: schemas → interface → repository → service
- [ ] Never copy a method without confirming it has callers
- [ ] Cross-slice service calls go through module `__init__.py`
- [ ] Every new DTO has `from_attributes=True` if it receives ORM data

### After Refactoring
- [ ] `python -c "from app.modules.{module} import *"` passes
- [ ] `grep -r "from app.api.schemas" ./app/modules` returns zero
- [ ] `grep -r "-> dict" ./app/modules/{module}` returns zero
- [ ] Old horizontal layer folders deleted
- [ ] All tests pass
- [ ] `uvicorn app.api.main:app --reload` starts without errors
