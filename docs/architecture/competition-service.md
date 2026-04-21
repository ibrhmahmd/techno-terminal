# Competition Service Architecture

Comprehensive documentation of the Competitions module following the 3-table schema redesign.

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Database Schema](#2-database-schema)
3. [Service Layer Architecture](#3-service-layer-architecture)
4. [Functional Workflows](#4-functional-workflows)
5. [Business Rules](#5-business-rules)
6. [Integration Points](#6-integration-points)
7. [API to Service Mapping](#7-api-to-service-mapping)

---

## 1. Architecture Overview

### 1.1 System Context

The Competitions module manages robotics competitions, team registrations, fee payments, and result tracking. It integrates with CRM (students, parents), Finance (payments, receipts), and Notifications modules.

```mermaid
flowchart TB
    subgraph External["External Systems"]
        Admin["Admin UI"]
        Parent["Parent Portal"]
    end

    subgraph API["API Layer"]
        Router["competitions_router.py<br/>FastAPI Router"]
    end

    subgraph Services["Service Layer"]
        CompSvc["CompetitionService"]
        TeamSvc["TeamService"]
    end

    subgraph Repositories["Repository Layer"]
        CompRepo["competition_repository"]
        TeamRepo["team_repository"]
    end

    subgraph Models["Data Layer"]
        CompModel[(Competition)]
        TeamModel[(Team)]
        MemberModel[(TeamMember)]
    end

    subgraph Integrations["Cross-Module Integrations"]
        Activity["Activity Logging<br/>crm/activity_service"]
        Notify["Notifications<br/>notifications/competition_notifications"]
        Finance["Finance Desk<br/>finance/receipt_service"]
        CRM["CRM<br/>crm/student_models"]
    end

    Admin --> Router
    Parent --> Router
    Router --> CompSvc
    Router --> TeamSvc
    CompSvc --> CompRepo
    TeamSvc --> TeamRepo
    TeamSvc --> CompRepo
    CompRepo --> CompModel
    TeamRepo --> TeamModel
    TeamRepo --> MemberModel
    TeamSvc -.-> Activity
    TeamSvc -.-> Notify
    TeamSvc -.-> Finance
    TeamSvc -.-> CRM
```

### 1.2 Module Structure

```
app/modules/competitions/
├── __init__.py                    # Service exports
├── models/
│   ├── competition_models.py      # Competition SQLModel
│   └── team_models.py             # Team, TeamMember SQLModels
├── repositories/
│   ├── competition_repository.py  # Competition CRUD
│   └── team_repository.py         # Team & TeamMember CRUD
├── services/
│   ├── competition_service.py     # Competition business logic
│   └── team_service.py            # Team & member business logic
├── schemas/
│   ├── competition_schemas.py     # Competition DTOs
│   └── team_schemas.py            # Team & member DTOs
└── routers/  (in app/api/routers/competitions_router.py)
```

---

## 2. Database Schema

### 2.1 3-Table Schema Design

The redesigned schema eliminates the `competition_categories` junction table, storing category/subcategory directly on the `teams` table using PostgreSQL `citext` for case-insensitive text.

```mermaid
erDiagram
    COMPETITION {
        int id PK
        string name
        string edition
        int edition_year
        date competition_date
        string location
        text notes
        decimal fee_per_student
        timestamp created_at
        timestamp deleted_at
        int deleted_by
    }

    TEAM {
        int id PK
        int competition_id FK
        string team_name
        citext category
        citext subcategory
        int group_id FK
        int coach_id FK
        decimal fee
        int placement_rank
        string placement_label
        text notes
        timestamp created_at
        timestamp deleted_at
        int deleted_by
    }

    TEAM_MEMBER {
        int id PK
        int team_id FK
        int student_id FK
        decimal member_share
        boolean fee_paid
        int payment_id FK
    }

    COMPETITION ||--o{ TEAM : "has many"
    TEAM ||--o{ TEAM_MEMBER : "includes"
```

### 2.2 Schema Evolution

| Old Schema (4-table) | New Schema (3-table) | Benefit |
|---------------------|---------------------|---------|
| `competitions` → `categories` → `teams` | `competitions` → `teams` | Simpler hierarchy |
| `category_id` FK on teams | `category` citext on teams | Direct category naming |
| Separate categories table | Inline in teams | No category management needed |
| Case-sensitive names | PostgreSQL `citext` | Case-insensitive auto-handling |

---

## 3. Service Layer Architecture

### 3.1 CompetitionService

```mermaid
classDiagram
    class CompetitionService {
        +create_competition(cmd: CreateCompetitionInput) CompetitionDTO
        +list_competitions(include_deleted: bool) List~CompetitionDTO~
        +get_competition_by_id(id: int) CompetitionDTO
        +update_competition(id: int, **kwargs) CompetitionDTO
        +delete_competition(id: int, deleted_by: int) bool
        +restore_competition(id: int) bool
        +list_deleted_competitions() List~CompetitionDTO~
        +list_categories(competition_id: int) List~CategoryInfoDTO~
        +get_competition_summary(id: int) CompetitionSummaryDTO
    }

    class CategoryInfoDTO {
        +string category
        +List~string~ subcategories
    }

    class CompetitionSummaryDTO {
        +CompetitionDTO competition
        +List~CategoryWithTeamsDTO~ categories
    }

    CompetitionService --> CategoryInfoDTO : returns
    CompetitionService --> CompetitionSummaryDTO : returns
```

### 3.2 TeamService

```mermaid
classDiagram
    class TeamService {
        +get_student_competitions(student_id: int) List~StudentCompetitionDTO~
        +register_team(cmd: RegisterTeamInput, user_id: int) TeamRegistrationResultDTO
        +list_teams(comp_id: int, cat: str, sub: str) List~TeamDTO~
        +get_teams_with_members(comp_id: int, cat: str, sub: str) List~TeamWithMembersDTO~
        +update_team(team_id: int, **kwargs) TeamDTO
        +delete_team(team_id: int, deleted_by: int) bool
        +restore_team(team_id: int) bool
        +update_placement(team_id: int, rank: int, label: str, user_id: int) TeamDTO
        +add_team_member_to_existing(team_id: int, student_id: int, user_id: int) AddTeamMemberResultDTO
        +remove_team_member(team_id: int, student_id: int) bool
        +list_team_members(team_id: int) List~TeamMemberRosterDTO~
        +pay_competition_fee(cmd: PayCompetitionFeeInput) PayCompetitionFeeResponseDTO
        +unmark_team_fee_for_payment(payment_id: int) void
    }

    class TeamService_Private {
        -_log_team_registration_activity(db, team, student_ids, comp_name, user_id)
        -_log_payment_activity(db, student_id, payment_id, amount, comp_name, user_id)
        -_log_placement_activity(db, student_id, comp_id, comp_name, rank, label, user_id)
    }

    TeamService --> TeamService_Private : uses
```

---

## 4. Functional Workflows

### 4.1 Team Registration Workflow

```mermaid
flowchart TD
    Start(["POST /competitions/{id}/teams"]) --> ValidateInput["Validate Input<br/>• competition_id matches URL<br/>• team_name not empty<br/>• category not empty<br/>• at least 1 student"]

    ValidateInput --> CheckComp["Fetch Competition<br/>Check exists & active"]
    CheckComp -->|Not Found| Error404["Return 404"]

    CheckComp --> CheckSubcategory{"Subcategory<br/>provided?"}
    CheckSubcategory -->|No| CheckHasSubs{"Check if category<br/>has existing<br/>subcategories"}
    CheckHasSubs -->|Yes| Error400Sub["Return 400<br/>Subcategory required"]
    CheckHasSubs -->|No| Continue1[Continue]
    CheckSubcategory -->|Yes| Continue1

    Continue1 --> CheckTeamName{"Team name unique<br/>in competition?"}
    CheckTeamName -->|Duplicate| Error409["Return 409 Conflict"]
    CheckTeamName -->|Unique| Continue2[Continue]

    Continue2 --> LoopStudents["For each student_id:"]
    LoopStudents --> CheckStudent["Student exists &<br/>is_active?"]
    CheckStudent -->|Not Found| Error404Stu["Return 404"]
    CheckStudent -->|Inactive| Error400Stu["Return 400<br/>Student inactive"]
    CheckStudent -->|Active| CheckEnrolled{"Already enrolled<br/>in competition?"}

    CheckEnrolled -->|Yes| Error409Enr["Return 409<br/>Already enrolled"]
    CheckEnrolled -->|No| NextStudent{"More students?"}

    NextStudent -->|Yes| LoopStudents
    NextStudent -->|No| CalcFee["Calculate fee:<br/>• Use cmd.fee if provided<br/>• Else competition.fee_per_student"]

    CalcFee --> CreateTeam["Create Team<br/>with category/subcategory"]
    CreateTeam --> AddMembers["Add TeamMembers<br/>with equal share"]
    AddMembers --> LogActivity["Log Activity<br/>for each student"]
    LogActivity --> ReturnResult["Return TeamRegistrationResultDTO"]

    Error404 --> End1([End])
    Error400Sub --> End1
    Error409 --> End1
    Error404Stu --> End1
    Error400Stu --> End1
    Error409Enr --> End1
    ReturnResult --> End1
```

### 4.2 Payment Processing Workflow (with Atomic Rollback)

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant TeamSvc as TeamService
    participant FinanceUoW as FinanceUnitOfWork
    participant ReceiptSvc as ReceiptService
    participant TeamRepo as TeamRepository
    participant ActivityLog

    Client->>Router: POST pay fee<br/>{team_id, student_id, parent_id}
    Router->>TeamSvc: pay_competition_fee(cmd)

    TeamSvc->>TeamRepo: get_team(team_id)
    TeamRepo-->>TeamSvc: Team
    TeamSvc->>TeamRepo: get_team_member(team_id, student_id)
    TeamRepo-->>TeamSvc: TeamMember

    alt Fee already paid
        TeamSvc-->>Client: 400 BusinessRuleError
    else Fee not paid
        TeamSvc->>FinanceUoW: Create Receipt
        FinanceUoW->>ReceiptSvc: create(lines, payer_name, ...)
        ReceiptSvc-->>FinanceUoW: receipt_number, payment_id
        FinanceUoW-->>TeamSvc: receipt_number, payment_id

        TeamSvc->>TeamRepo: mark_fee_paid(team_id, student_id, payment_id)
        TeamRepo-->>TeamSvc: success

        TeamSvc->>ActivityLog: _log_payment_activity()
        ActivityLog-->>TeamSvc: logged

        TeamSvc-->>Client: 200 PayCompetitionFeeResponseDTO
    end

    opt Mark fee fails (Rollback)
        TeamSvc->>FinanceUoW: refund_payment(payment_id, "Failed to mark fee")
        FinanceUoW->>ReceiptSvc: refund_payment(...)
        ReceiptSvc-->>FinanceUoW: refund_receipt
        FinanceUoW-->>TeamSvc: refund_complete
        TeamSvc-->>Client: 400 "Payment refunded"
    end
```

### 4.3 Placement Update Workflow

```mermaid
flowchart TD
    Start(["PATCH /teams/{id}/placement"]) --> GetTeam["Get Team by ID"]
    GetTeam -->|Not Found| Error404["Return 404"]
    GetTeam -->|Found| GetComp["Get Competition"]

    GetComp --> CheckDate{"Competition date<br/>passed?"}
    CheckDate -->|No| Error400["Return 400<br/>Cannot set before date"]
    CheckDate -->|Yes| UpdateTeam["Update Team<br/>• placement_rank<br/>• placement_label"]

    UpdateTeam --> GetMembers["Get all team members"]
    GetMembers --> LoopStart["For each member:"]
    LoopStart --> LogPlacement["_log_placement_activity()<br/>Log for each student"]
    LogPlacement --> Notify["Send placement<br/>notification to parent"]
    Notify --> MoreMembers{"More members?"}
    MoreMembers -->|Yes| LoopStart
    MoreMembers -->|No| ReturnResult["Return TeamDTO"]

    Error404 --> End1([End])
    Error400 --> End1
    ReturnResult --> End1
```

### 4.4 Soft Delete Workflow (Team)

```mermaid
flowchart TD
    Start(["DELETE /teams/{id}"]) --> GetTeam["Get Team"]
    GetTeam -->|Not Found| Error404["Return 404"]
    GetTeam -->|Found| GetMembers["Get team members"]

    GetMembers --> CheckPaid{"Any member<br/>fee_paid?"}
    CheckPaid -->|Yes| Error409["Return 409<br/>Cannot delete: paid members"]
    CheckPaid -->|No| SoftDelete["Soft Delete:<br/>• deleted_at = now()<br/>• deleted_by = user_id"]

    SoftDelete --> LogDelete["Log deletion activity"]
    LogDelete --> ReturnResult["Return true"]

    Error404 --> End1([End])
    Error409 --> End1
    ReturnResult --> End1
```

### 4.5 Category Listing (3-Table Schema)

```mermaid
flowchart LR
    Request["GET /competitions/{id}/categories"] --> Query["team_repo.get_distinct_categories()"]

    Query --> SQL["SQL Query:<br/>SELECT DISTINCT category, subcategory<br/>FROM teams<br/>WHERE competition_id = {id}<br/>AND deleted_at IS NULL<br/>ORDER BY category, subcategory"]

    SQL --> Fetch["Fetch rows as<br/>List[tuple[str, Optional[str]]]"]
    Fetch --> Group["Group by category:<br/>Map[category] = Set[subcategories]"]
    Group --> BuildDTO["Build CategoryInfoDTO<br/>for each unique category"]
    BuildDTO --> Return["Return<br/>List[CategoryResponse]"]

    style SQL fill:#e1f5fe
```

---

## 5. Business Rules

### 5.1 Rule Enforcement Matrix

| Rule | Validation Point | Error Type | Service Method |
|------|-----------------|------------|----------------|
| **One student per competition** | `team_repo.check_student_in_competition()` | ConflictError | `register_team()`, `add_team_member_to_existing()` |
| **Subcategory required** | `team_repo.check_category_has_subcategories()` | BusinessRuleError | `register_team()` |
| **Team name uniqueness** | Case-insensitive comparison against existing teams | ConflictError | `register_team()` |
| **Student must be active** | `student.is_active` check | NotFoundError | `register_team()` |
| **Paid member protection** | `member.fee_paid` check before removal | BusinessRuleError | `remove_team_member()`, `delete_team()` |
| **Placement timing** | `competition.competition_date > today()` check | BusinessRuleError | `update_placement()` |
| **Competition has no teams** | `team_repo.list_teams()` empty check | BusinessRuleError | `delete_competition()` |

### 5.2 One Student Per Competition Validation

```mermaid
flowchart LR
    Input["student_id<br/>competition_id"] --> Query["SELECT tm.*<br/>FROM team_members tm<br/>JOIN teams t ON t.id = tm.team_id<br/>WHERE t.competition_id = {comp_id}<br/>AND tm.student_id = {student_id}<br/>AND t.deleted_at IS NULL"]

    Query --> Result{"Result?"}
    Result -->|NULL| ReturnFalse["Return False<br/>(not enrolled)"]
    Result -->|Record| ReturnTrue["Return True<br/>(already enrolled)"]

    style Query fill:#fff3e0
```

### 5.3 Member Share Calculation

```mermaid
flowchart LR
    TeamFee["team.fee"] --> CheckFee{"fee > 0?"}
    CheckFee -->|No| ZeroShare["share = 0.0"]
    CheckFee -->|Yes| Calc["share = fee /<br/>student_count"]

    ZeroShare --> Return["member_share"]
    Calc --> Return

    style Calc fill:#e8f5e9
```

---

## 6. Integration Points

### 6.1 Activity Logging Integration

Activity logging is performed asynchronously to not block the main transaction.

```mermaid
flowchart TD
    subgraph ServiceCall["Service Method"]
        Action["Main Action<br/>• Create team<br/>• Pay fee<br/>• Set placement"]
        Commit["db.commit()"]
    end

    subgraph ActivityLog["Activity Logging (Best Effort)"]
        CreateUoW["Create StudentUnitOfWork"]
        LogCall["activity_svc.log_*()"]
        ActivityCommit["uow.commit()"]
    end

    subgraph ErrorHandling["Error Handling"]
        TryCatch{"Try/Catch"}
        SilentFail["Silent Fail<br/>Don't block main flow"]
    end

    Action --> Commit
    Commit -.-> TryCatch
    TryCatch -->|Success| CreateUoW
    CreateUoW --> LogCall
    LogCall --> ActivityCommit
    TryCatch -->|Exception| SilentFail
```

### 6.2 Finance Module Integration

```mermaid
flowchart LR
    subgraph CompetitionModule["Competition Module"]
        TeamSvc["TeamService"]
    end

    subgraph FinanceModule["Finance Module"]
        FinanceUoW["FinanceUnitOfWork"]
        ReceiptSvc["ReceiptService"]
        PaymentModel[(Payment)]
    end

    TeamSvc -->|"create receipt<br/>lines=[{student_id, amount}]"| FinanceUoW
    FinanceUoW --> ReceiptSvc
    ReceiptSvc --> PaymentModel
    PaymentModel -->|"payment_id"| TeamSvc
    TeamSvc -->|"mark_fee_paid<br/>(payment_id)"| TeamSvc
```

### 6.3 Notification Integration

```mermaid
flowchart TD
    subgraph CompetitionSvc["Competition Service"]
        Register["register_team()"]
        Pay["pay_competition_fee()"]
        Place["update_placement()"]
    end

    subgraph NotificationSvc["Notification Service"]
        CompNotify["CompetitionNotificationService"]
        Templates["Templates:<br/>• competition_team_registration<br/>• competition_fee_payment<br/>• competition_placement"]
        Dispatch["Dispatch via<br/>• WhatsApp<br/>• Email"]
    end

    Register -.->|"background_tasks.add_task()"| CompNotify
    Pay -.->|"background_tasks.add_task()"| CompNotify
    Place -.->|"background_tasks.add_task()"| CompNotify

    CompNotify --> Templates
    Templates --> Dispatch
```

---

## 7. API to Service Mapping

### 7.1 Endpoint Reference

| Endpoint | Method | Service Method | Business Rules Applied |
|----------|--------|---------------|----------------------|
| `GET /competitions` | CompetitionService.list_competitions() | - |
| `POST /competitions` | CompetitionService.create_competition() | - |
| `GET /competitions/{id}` | CompetitionService.get_competition_by_id() | - |
| `GET /competitions/{id}/categories` | CompetitionService.list_categories() | - |
| `GET /competitions/{id}/teams` | TeamService.get_teams_with_members() | Filter by cat/subcat |
| `POST /competitions/{id}/teams` | TeamService.register_team() | One student/comp, subcategory required, name unique |
| `DELETE /competitions/{id}` | CompetitionService.delete_competition() | No teams allowed |
| `POST /competitions/{id}/restore` | CompetitionService.restore_competition() | - |
| `GET /competitions/deleted` | CompetitionService.list_deleted_competitions() | Admin only |
| `GET /teams/{id}` | - | - |
| `PATCH /teams/{id}/placement` | TeamService.update_placement() | Competition date passed |
| `DELETE /teams/{id}` | TeamService.delete_team() | No paid members |
| `POST /teams/{id}/restore` | TeamService.restore_team() | - |
| `POST /competitions/{cid}/teams/{tid}/members/{sid}/pay` | TeamService.pay_competition_fee() | Atomic rollback |

### 7.2 DTO Flow

```mermaid
flowchart LR
    subgraph InputDTOs["Input DTOs"]
        CreateComp["CreateCompetitionInput"]
        RegisterTeam["RegisterTeamInput<br/>• competition_id<br/>• team_name<br/>• category<br/>• subcategory<br/>• student_ids[]<br/>• fee (optional)"]
        PayFee["PayCompetitionFeeInput<br/>• team_id<br/>• student_id<br/>• parent_id<br/>• received_by_user_id"]
    end

    subgraph OutputDTOs["Output DTOs"]
        CompDTO["CompetitionDTO"]
        TeamRegResult["TeamRegistrationResultDTO<br/>• team: TeamDTO<br/>• members_added: int"]
        PayResponse["PayCompetitionFeeResponseDTO<br/>• receipt_number<br/>• payment_id<br/>• amount"]
    end

    CreateComp --> CompDTO
    RegisterTeam --> TeamRegResult
    PayFee --> PayResponse
```

---

## Appendix: Database Migration Summary

Migration: `035_competitions_3table_redesign.sql`

| Table | Changes |
|-------|---------|
| **competitions** | Add `edition_year` (int), `deleted_at` (timestamp), `deleted_by` (int) |
| **teams** | Add `competition_id` (FK), `category` (citext), `subcategory` (citext), `fee` (decimal), `placement_rank` (int), `placement_label` (varchar), `notes` (text), `deleted_at`, `deleted_by` |
| **New Indexes** | `idx_teams_competition_category_subcategory` for filtering |
| **Trigger** | `trim_team_category()` - auto-trims whitespace on insert/update |

---

*Document generated for the Competitions Module 3-Table Schema Redesign*
