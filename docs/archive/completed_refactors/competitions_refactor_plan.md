# Competitions Module Refactoring Plan

This plan tracks the Deep-SOLID refactoring of the `competitions` module, upgrading it from a legacy monolithic state into a strictly-typed, domain-segregated architecture.

## Phase 1 & 2: DTO Enforcement & Schema Separation
- [x] Create `schemas/` directory.
- [x] Create `schemas/competition_schemas.py` and move `CompetitionCreate`, `CompetitionRead`, `CompetitionCategoryCreate`, `CompetitionCategoryRead` and input DTOs over.
- [x] Create `schemas/team_schemas.py` and move `TeamCreate`, `TeamRead`, `TeamMemberCreate`, `TeamMemberRead` and input DTOs (`RegisterTeamInput`, `PayCompetitionFeeInput`) over.
- [x] Define **new strict return DTOs** bridging the gap where dictionaries are currently returned: 
  - `StudentCompetitionDTO` (for `get_student_competitions`)
  - `TeamRegistrationResultDTO` (for `register_team`)
  - `AddTeamMemberResultDTO` (for `add_team_member_to_existing`)
  - `TeamMemberRosterDTO` (for `list_team_members`)
  - `PayCompetitionFeeResponseDTO` (for `pay_competition_fee`)
  - `CompetitionSummaryDTO` (for `get_competition_summary`)
- [x] Define/Refine **Input Command DTOs** bridging the gap where long parameter lists are used:
  - Enforce `CreateCompetitionInput` for `create_competition`
  - Enforce `AddCategoryInput` for `add_category`
  - Enforce `RegisterTeamInput` for `register_team`
  - Enforce `PayCompetitionFeeInput` for `pay_competition_fee`
- [x] Create `schemas/__init__.py` to export all schemas.

## Phase 3: Model Separation
- [x] Create `models/` directory.
- [x] Split `competition_models.py` into:
    - `models/competition_models.py` (`CompetitionBase`, `Competition`, `CompetitionCategoryBase`, `CompetitionCategory`)
    - `models/team_models.py` (`TeamBase`, `Team`, `TeamMemberBase`, `TeamMember`)
- [x] Update `init_db.py` to import models from the new separated directories to prevent table vanishing issues.

## Phase 4: Repository Layer Separation
- [x] Create `repositories/` directory.
- [x] Split `competition_repository.py` into:
    - `repositories/competition_repository.py` (Handling Competitions and Categories)
    - `repositories/team_repository.py` (Handling Teams and TeamMembers)
- [x] Create `repositories/__init__.py` to re-export repository functions.

## Phase 5: Service Layer Separation
- [x] Create `services/` directory.
- [x] Split `competition_service.py` into Object-Oriented Service classes:
    - `services/competition_service.py` (`CompetitionService` encapsulating CRUD and summary for Competitions/Categories)
    - `services/team_service.py` (`TeamService` encapsulating team registration, roster reading, team member addition/removal, fee payment).
- [x] Refactor all service methods to strictly return the new DTO objects created in Phase 1 instead of raw python dictionaries.

## Phase 6 & 7: Facade Reconstitution & UI Update
- [x] Delete monolithic files: `competition_models.py`, `competition_schemas.py`, `competition_repository.py`, `competition_service.py`.
- [x] Reconfigure `app/modules/competitions/__init__.py` to globally instantiate `CompetitionService` and `TeamService` and map all legacy function calls to the new service singletons (backward compatibility).
- [x] Inspect UI files parsing `dict` payloads and modify their data access layers to handle DTO attribute fetching (`.key` instead of `.get("key")`).
