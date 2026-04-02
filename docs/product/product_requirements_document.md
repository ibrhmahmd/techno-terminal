# Techno Terminal — Frontend MVP PRD

**Document Type:** Project PRD (1-Day MVP Focus)
**Version:** 1.0 (Draft)
**Date:** 2026-04-02
**Author(s):** AI Assistant & Product Owner

---

## 2. Executive Summary
Techno Terminal needs a modern frontend decoupling from the old Streamlit UI to a dedicated web application. Given the strict **1-day deadline**, this MVP will exclusively focus on the top 3 priority features: **Group Management (Dashboard), Session Management, and the Directory UI**. The frontend will consume the newly built FastAPI REST endpoints.

---

## 3. Goals & Objectives
**Business Goals:**
- Deliver a working, compiled frontend application within 24 hours.
- Completely replace Streamlit for the daily operational workflows of Admins.

**User Goals:**
- Admins logging in must immediately see today's active groups and sessions.
- Admins must be able to take attendance, edit session statuses, and view/add notes rapidly without navigating deep into menus.

---

## 4. Proposed Technical Stack (For 1-Day Deadline)

Given we have literally 24 hours, we must optimize for speed, pre-built components, and easy data-fetching:

1. **Framework:** **Vite + React (TypeScript)** 
   *Why?* Much faster local dev server than Next.js, and we don't need SEO for an internal CRM. No server-side rendering complexity.
2. **UI Library:** **Tailwind CSS + shadcn/ui**
   *Why?* Shadcn provides pre-built, gorgeous Data Tables, Dialogs (popups for editing), and Dropdowns that we can just copy-paste and wire to our API without writing custom CSS.
3. **Data Fetching:** **TanStack Query (React Query) + Axios**
   *Why?* Auto-handles caching, loading states (`isLoading`), and re-fetching data automatically when an admin updates attendance or edits a session.

---

## 5. Scope (In-Scope for 1-Day MVP)

### Feature 1: The Active Dashboard (Group & Session Management)
*This is the core landing page instead of KPI cards.*
- **Top Bar:** A dropdown/date-picker to select the Day (defaults to Today).
- **Main View:** A list of all Groups active on that day.
- **Per Group:** Displays the "Attendance Table" matching the selected day's session.
- **Actions available directly on the table:**
  - Toggle attendance checkboxes (Present/Absent).
  - "Edit Session Info" button: Opens a `shadcn` Dialog (pop-up) to change `status` (completed/cancelled), edit the session `notes`.

### Feature 2: Directory UI
- A clean data table listing all Students/Parents/Staff.
- Search bar to quickly find users.
- Click to view basic details (Full profile/Finance routing can be deferred to Phase 2 if time runs out).

### Explicitly Out-of-Scope (for tomorrow)
- Financial Desk / Receipt creation.
- Complex Analytics/reports.
- Setting up new courses or complex scheduling algorithms.

---

## 6. UX & Design Requirements
- **Aesthetic:** Clean, high-contrast, modern UI. Glassmorphism or extremely refined minimalist borders.
- **UX Rule:** Avoid page reloads. Expanding a group, editing a session, and saving attendance should all happen inline or via instant Dialog pop-ups.

---

## 7. Open Questions for You

To finalize this plan and write the actual code, please clarify:

1. **Framework Confirmation:** Are you happy with **React + Vite + Tailwind + shadcn/ui**? (It is objectively the fastest way to hit a 1-day deadline for a dashboard). Or do you strongly prefer Vue/Next.js/Flutter?
2. **API Alignment:** For the Dashboard, we need an endpoint that returns "All groups and their sessions for Date X". Does our current `academics_router.py` or `attendance_router.py` have a `GET /api/v1/academics/daily-schedule?date=...` endpoint ready, or do we need to quickly build that API route first?
3. **Authentication:** Should we hardcode an "Admin" login bypass for tomorrow to save time, or do we need to wire up the real Supabase JWT login screen immediately?