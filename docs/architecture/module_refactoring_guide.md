# Module Refactoring Guide & Architectural Template

This document serves as the **Standard Operating Procedure (SOP)** for refactoring monolithic/legacy modules in the Techno Kids CRM into the robust, per-entity, SOLID architecture. It is heavily derived from the highly successful `academics` module refactoring in March 2026.

## 1. The Core Philosophy (Target Architecture)
The module architecture strictly enforces:
1.  **Single Responsibility Principle (SRP):** Files should rarely exceed 300 lines. If a file manages multiple domain entities (e.g. Courses, Groups, Sessions), it must be split into dedicated, per-entity files.
2.  **Strict Type Safety & DTO Contracts:** Python dictionaries `{"key": "value"}` are strictly prohibited as input arguments and return types for Service and Repository functions. Validated Pydantic DTOs must be used instead.
3.  **Boundary & UI Insulation:** Refactoring the inner workings (Services/Repos) of a module must **not** break downstream UI imports. A facade layer (`__init__.py`) is used to maintain backward compatibility.
4.  **No Circular Dependencies:** The import hierarchy is strictly: Models → Schemas → Repositories → Services → `__init__.py` Facade. Schemas must never import from Services, and Services must never import the UI.

---

## 2. The Refactoring Playbook (7 Phases)

Follow these phases sequentially when tackling any other monolithic module (like `crm`, `finance`, or `hr`).

### Phase 1: Foundation (Constants & Helpers)
1.  Create a `constants.py` file within the module.
2.  Extract all hard-coded strings, domain enums, status lists, and view names from the module's code and move them to `constants.py`.
3.  Create a `helpers/` folder.
4.  Move any pure algorithmic or utility functions (e.g. date math, list formatting) into `helpers/`. **Helpers should not interact with the database.**

### Phase 2: Schema Decoupling
1.  Create a `schemas/` folder.
2.  Analyze the module's models and split schemas into per-entity files (e.g., `course_schemas.py`, `group_schemas.py`).
3.  Define strict Pydantic `BaseModel` classes for every Input and Output (DTO) you will need.
4.  **Crucial:** Ensure these schemas *only* import from standard libraries, `constants.py`, or `helpers/`. They must be at the very bottom of the dependency chain.
5.  Export all schemas through `schemas/__init__.py`.

### Phase 3: Contract Migration (The DTO Enforcement)
1.  Identify every Service and Repository function that currently accepts or returns raw dictionaries (e.g., `def create_thing(data: dict) -> list[dict]:`).
2.  Update the function signatures to strictly require the new Pydantic DTOs (e.g., `def create_thing(data: CreateThingInput) -> list[ThingDTO]:`).
3.  *Note: At this stage, the module is still in large files, but its signatures are now 100% typed.*

### Phase 4: Data Access Layer Split (Repositories)
1.  Create a `repositories/` folder.
2.  Take the monolithic `[module]_repository.py` and rip it apart into distinct files per entity (e.g., `course_repository.py`, `group_repository.py`).
3.  Ensure each repository class/file only accesses the database for its specific domain entity.
4.  Export all repo functions via `repositories/__init__.py` to make imports cleaner.

### Phase 5: Business Logic Split (Services)
1.  Create a `services/` folder.
2.  Take the monolithic `[module]_service.py` and rip it apart into distinct Object-Oriented Service classes (e.g., `CourseService`, `GroupService`).
3.  These service classes should receive a DB session implicitly via context managers (`with get_session()`), do their validation, and then call the newly split Repositories.

### Phase 6: Model Split & Compatibility Facade
1.  Create a `models/` folder.
2.  Take the monolithic `[module]_models.py` and split the `SQLModel` definitions into per-entity files (e.g., `course_models.py`). 
3.  Delete the old monolithic Service, Repository, Schema, and Model files entirely.
4.  **The Facade:** Open the module's root `__init__.py`. Instantiate the new Service classes here and bind their methods to module-level variables. 
    *Example:*
    ```python
    from .services.group_service import GroupService
    _group_svc = GroupService()
    schedule_group = _group_svc.schedule_group  # Re-exports the function identically
    ```
5.  This guarantees 100% backward compatibility. The UI won't crash because it thinks it's still calling the old functions.

### Phase 7: UI & Frontend Update (Adapter Retirement)
1.  Do a global Find and Replace across the `app/ui/` folder.
2.  Find any instance where the UI was expecting a dictionary from this module and using `item.get("key")` or `item["key"]`.
3.  Change those instance to standard Python object attribute access: `getattr(item, "key", default)` or simply `item.key` (since the backend now returns safe DTOs).
4.  Update UI imports from the obsolete monolithic files directly to the root package (`import app.modules.[module] as module_srv`).

---

## 3. Immediate Bug Patches & Edge Cases
*   **Database Views Going Missing:** If your module leverages PostgreSQL `CREATE OR REPLACE VIEW` logic, placing it in a manual `.sql` migration is risky if the DB is ever reset. You must ensure the actual raw SQL string is included inside `app/db/init_db.py` under the `RAW_VIEWS_SQL` string so SQLModel re-applies it during database wipes.
*   **SQLModel Sync Errors:** If you hallucinate/add a field to a `SQLModel` class (e.g. `status = Field()`) that doesn't actually exist in the physical PostgreSQL table, the application will throw `psycopg2.errors.UndefinedColumn` errors the moment it queries that table. The SQLModel class must perfectly mirror the DB table.
*   **Streamlit Hot-Reloading Caches:** Mass-renaming folders and importing files will sometimes crash Streamlit with JS bundle errors (`Failed to fetch dynamically imported module...`). The user simply needs to Hard Refresh (Ctrl+F5) their browser tab to clear the obsolete file hashes.
