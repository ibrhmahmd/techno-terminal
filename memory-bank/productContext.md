# Product Context — Why This Exists

## Problem Statement
STEM education centers need integrated management of:
- Student enrollment across multiple courses and levels
- Complex parent-student relationships (multiple children, multiple parents)
- Financial tracking with receipts, payments, refunds, and real-time balance calculation
- Student waiting lists for popular courses
- Competition team registration and per-student fee collection
- Staff coordination, attendance, and user account management
- Comprehensive audit trail for all student activities

## User Experience Goals
1. **Single Source of Truth** — All data in PostgreSQL, accessed via consistent API (~85 endpoints)
2. **Role-Based Access** — Admin-only operations, simplified from 4 roles to 2 (admin, system_admin)
3. **Audit Trail** — Created/updated timestamps with actor tracking, plus dedicated activity logging
4. **Responsive UI** — Streamlit for internal, React for future scalability
5. **Financial Accuracy** — Real-time balance calculation with database triggers
6. **Operational Efficiency** — Automated session generation, waiting list management, group lifecycle

## Key Workflows
1. **Student Registration** → Parent linking → Course enrollment → Payment
2. **Daily Operations** → Attendance marking → Session management
3. **Financial** → Receipt creation → Payment recording → Automated balance tracking with triggers
4. **Competitions** → Team registration → Category assignment → Per-student fee tracking
5. **Group Lifecycle** → Level progression → Session generation → Completion tracking
6. **Student History** → Activity logging → Enrollment history → Audit trail

## Differentiators
- Deep-SOLID architecture with clear separation (models → repo → service)
- Dual-path UI (Streamlit + API-ready for React)
- Comprehensive analytics (BI trends, retention, flight-risk, instructor performance)
- Supabase auth integration with local user mapping
- Real-time balance tracking via PostgreSQL triggers
- Modular API documentation (15+ markdown files across domains)
- Production-ready deployment on Leapcell with health checks

## Recent Capabilities Added

### Student Balance Management (Migration 015, 016, 019)
- Automated balance calculation via triggers
- Payment allocation tracking
- Receipt generation with PDF support
- Per-enrollment balance views

### Student Activity Logging (Migration 017)
- Audit trail for all student actions
- Activity history with timestamps and actors
- Filterable activity reports

### Group Lifecycle Management (Migration 012)
- Level progression tracking
- Automatic session generation (5 sessions per level)
- Group status workflow (active, inactive, completed, archived)

### Waiting List Management (Migration 013)
- Student waiting status tracking
- Priority-based enrollment from waitlist
- Course capacity management
