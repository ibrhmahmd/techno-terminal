# Product Context — Why This Exists

## Problem Statement
STEM education centers need integrated management of:
- Student enrollment across multiple courses and levels
- Complex parent-student relationships (multiple children, multiple parents)
- Financial tracking with receipts, payments, and refunds
- Competition team registration and fee collection
- Staff coordination and attendance

## User Experience Goals
1. **Single Source of Truth** — All data in PostgreSQL, accessed via consistent API
2. **Role-Based Access** — Admin-only operations, simplified from 4 roles to 2 (admin, system_admin)
3. **Audit Trail** — Created/updated timestamps with actor tracking
4. **Responsive UI** — Streamlit for internal, React for future scalability

## Key Workflows
1. **Student Registration** → Parent linking → Course enrollment → Payment
2. **Daily Operations** → Attendance marking → Session management
3. **Financial** → Receipt creation → Payment recording → Balance tracking
4. **Competitions** → Team registration → Category assignment → Fee collection

## Differentiators
- Deep-SOLID architecture with clear separation (models → repo → service)
- Dual-path UI (Streamlit + API-ready for React)
- Comprehensive analytics (BI trends, retention, flight-risk)
- Supabase auth integration with local user mapping
