# Documentation Organization Plan & Naming Convention

## 1. Core Principles
1. **Agent Context Purity:** The `memory_bank/` is the absolute source of truth for the codebase. It must **not** contain outdated sprint plans, old refactoring backlogs, or chat logs. Those harm agent context length and accuracy.
2. **Clear Separation:** Active planning belongs in a `planning/` folder. Legacy history belongs in an `archive/` folder.
3. **Strict Naming:** All files and folders use `snake_case`, numeric prefixes for sequencing, and `YYYY_MM_DD` for dates.

---

## 2. Directory Structure & Naming Convention

### `docs/MEMORY_BANK.md`
The root index for AI agents. It maps the project and points to the `memory_bank/` directory.

### `docs/memory_bank/`
**Purpose:** Core domain knowledge, architecture, and current state. 
**Naming Convention:** Numbered prefixes (`01_`, `02_`) for logical reading order. No dates in filenames here, as these are living documents permanently maintained.
*   `01_business_domain/` (Business rules, glossaries)
*   `02_database_design/` (Schema conventions, views, data flow)
*   `03_etl_pipeline/` (Data migration/ETL standards)
*   `04_architecture/` (System design, component standards, backend service patterns)

*(Note: The old `05_reviews` folder here will be exiled to the archive, as it contains outdated SaaS analysis and refactoring backlogs).*

### `docs/planning/` (Replacing current root `reviews/`)
**Purpose:** Active sprint planning, QA backlogs, and design spikes for unresolved work.
**Naming Convention:** `<topic>_<type>.md` (e.g., `phase2_competition_fees_design.md`, `sprint_7_implementation_plan.md`). Tangible dates are appended if time-bound: `qa_backlog_YYYY_MM_DD.md`.
*   `sprint_roadmap_post_qa_2026.md`
*   `qa_backlog_2026_03_testing_findings.md`
*   `phase2_competition_fees_design.md`

### `docs/product/`
**Purpose:** Executive briefs and high-level product requirements.
**Naming Convention:** Descriptive snake_case.

### `docs/archive/` (NEW!)
**Purpose:** The graveyard for completed sprints, legacy documentation, and old agent chat logs. Agents should **ignore** this folder unless specifically asked to dig up history.
**Naming Convention:** Grouped by category, preserving original filenames so history isn't broken.
*   `docs/archive/legacy_reviews/` (Moves `memory_bank/05_reviews` here)
*   `docs/archive/legacy_plans/` (Moves `docs/plans/` here)
*   `docs/archive/agent_sessions/` (Moves `docs/agent_sessions/` here, including huge dumped chat logs)
*   `docs/archive/completed_sprints/` (For completed architecture spikes like the sprint 5 B8 balance spike, once implemented).

---

## 3. Action Items (Execution Plan)

If approved, the agent will run the following commands to reshape the `docs/` directory:

1. **Create Archive Directories:**
   * `mkdir docs/archive`
   * `mkdir docs/archive/legacy_reviews`
   * `mkdir docs/archive/legacy_plans`
   * `mkdir docs/archive/agent_sessions`
2. **Relocate Legacy Files:**
   * Move `docs/memory_bank/05_reviews/*` -> `docs/archive/legacy_reviews/`
   * Remove empty `docs/memory_bank/05_reviews`
   * Move `docs/plans/*` -> `docs/archive/legacy_plans/`
   * Remove empty `docs/plans`
   * Move `docs/agent_sessions/*` -> `docs/archive/agent_sessions/`
   * Remove empty `docs/agent_sessions`
3. **Rename & Clean Active Planning:**
   * Rename `docs/reviews/` -> `docs/planning/`
   * Edit `docs/MEMORY_BANK.md` and `docs/planning/README.md` to reflect the new paths.
4. **Final Result:** Agents will only ingest `MEMORY_BANK.md`, `memory_bank/`, and `planning/`, reducing token waste and hallucinated "todo" items from 2024/2025.
