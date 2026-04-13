# Project Brief — Techno Terminal

## Core Requirements

**Techno Terminal** is a full-stack internal management system for a STEM education center.

### Key Capabilities
1. **Student & Parent Management** — Registration, profiles, M:M parent relationships
2. **Academic Operations** — Course catalogs, group scheduling, session tracking, attendance
3. **Enrollment Lifecycle** — Level-based enrollment with historical snapshots
4. **Financial Operations** — Receipts, payments, refunds, balance tracking
5. **Competitions** — Team registration, categories, fee management
6. **Analytics & Reporting** — Dashboards, trends, retention metrics, risk analysis
7. **Staff Management** — Employee directory, accounts, HR attendance

### Success Criteria
- [x] Backend API 100% complete (~85+ endpoints across 15 routers)
- [x] Testing coverage 94% (161 tests, 160 passing)
- [x] Frontend implementation (Complete - Vite + React 18 + TypeScript + TanStack Query) //the forntend have been implementated
- [x] Production deployment (Leapcell - stable with health checks)

## Current State
- **Backend:** FastAPI + SQLModel + PostgreSQL + Supabase Auth (15 routers, 10 modules)
- **Database:** 16 tables, 5 views, 21 migration files // review the db and migrations directory fir better context about the db or use the subabase mcp for quering 
- **Testing:** Pytest with 20 test modules, 161 tests, 94% coverage
- **UI:** Streamlit (internal), React frontend planned (Vite + React 18 + TanStack Query)
- **Deployment:** Leapcell with railpack.json (Gunicorn + Uvicorn workers)

## Next Major Phase
Frontend development with Vite + React 18 + TypeScript + TanStack Query + Zustand

## Recently Completed Modules
- **Finance Module:** Balance tracking, receipts, payments with triggers (migrations 015, 016, 019)
- **Student History:** Activity logging and enrollment history (migration 017)
- **Group Lifecycle:** Level progression and session generation (migration 012)
- **Analytics:** Modularized into academic, financial, competition, BI sub-domains
- **Deployment:** Fixed worker timeouts, read-only filesystem issues on Leapcell
