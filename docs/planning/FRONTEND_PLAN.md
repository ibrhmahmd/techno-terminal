# Techno Terminal CRM — Frontend Development Plan

**Created:** 2026-04-02  
**Status:** 🟡 Ready to Start  
**Deadline:** 1 day (MVP delivery)  
**Base API:** `http://<server>:8000/api/v1`  
**Handover Spec:** [`docs/product/frontend_handover.md`](../product/frontend_handover.md)

---

## Executive Summary

The backend API is **100% complete** and ready for frontend consumption. This document is the single source of truth for the frontend developer picking up this project. The goal is to ship a working MVP in one day that covers the 5 highest-priority pages.

---

## 1. Agreed Technical Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| **Framework** | Vite + React 18 | Fastest scaffold, no SSR overhead, ideal for internal tools |
| **Language** | TypeScript | Type safety against API contracts |
| **Routing** | React Router v6 | Simple SPA routing |
| **Server State** | TanStack Query (React Query) | Caching, loading states, mutations for all API calls |
| **Auth State / Global** | Zustand | Lightweight store for JWT + user role |
| **Styling** | Vanilla CSS + CSS Variables | Full control, no config overhead |
| **HTTP Client** | Axios | Interceptors for auto-injecting JWT header |
| **Build** | Vite | Sub-second HMR |

> **NOT using:** Next.js (SSR overkill), Redux (too verbose), TailwindCSS (not requested)

---

## 2. Project Structure

```
frontend/
├── public/
├── src/
│   ├── api/                  # All API call functions (per domain)
│   │   ├── client.ts         # Axios instance with auth interceptor
│   │   ├── auth.ts
│   │   ├── crm.ts
│   │   ├── academics.ts
│   │   ├── attendance.ts
│   │   ├── enrollments.ts
│   │   └── finance.ts
│   ├── store/
│   │   └── authStore.ts      # Zustand: JWT, user role, login/logout
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   └── AppLayout.tsx
│   │   ├── common/
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   └── Modal.tsx
│   │   └── attendance/
│   │       ├── AttendanceGrid.tsx  ← Critical reusable component
│   │       └── EditSessionPopup.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── GroupsPage.tsx
│   │   ├── GroupDetailPage.tsx
│   │   ├── DirectoryPage.tsx
│   │   ├── StudentDetailPage.tsx
│   │   ├── ParentDetailPage.tsx
│   │   ├── EnrollmentsPage.tsx
│   │   └── FinancePage.tsx
│   ├── types/
│   │   └── api.ts            # TypeScript types mirroring API response DTOs
│   ├── App.tsx               # Router setup + protected routes
│   ├── main.tsx
│   └── index.css             # Global design tokens + CSS vars
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## 3. MVP Page Priority — Build Order

Build in this exact order. Each phase is independently deployable.

| Phase | Pages | Est. Time | Unblocked? |
|:-----:|-------|:---------:|:----------:|
| **0** | Scaffold + API client + Auth store + Layout | 1.5h | ✅ |
| **1** | Login Page | 30m | ✅ |
| **2** | Dashboard Page | 2h | ✅ |
| **3** | Group Detail + Attendance Grid | 2.5h | ✅ |
| **4** | Directory (Students + Parents) | 2h | ✅ |
| **5** | Enrollments Page | 1h | ✅ |
| **6** | Finance Page (Receipts) | 1.5h | ✅ |
| **7** | Reports stub | 30m | ⚠️ Partial API |

**Total MVP: ~11 hours**

---

## 4. Phase 0 — Scaffold Setup

### Commands to Run
```bash
# In project root
npx create-vite@latest frontend --template react-ts
cd frontend
npm install
npm install axios @tanstack/react-query zustand react-router-dom
```

### Vite Config (proxy to avoid CORS in dev)
```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### API Client with Auth Interceptor
```ts
// src/api/client.ts
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

export const apiClient = axios.create({
  baseURL: '/api/v1',
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### Auth Store (Zustand)
```ts
// src/store/authStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  user: { id: number; email: string; role: string } | null
  login: (token: string, user: AuthState['user']) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
)
```

---

## 5. Phase 1 — Login Page

### Endpoint
`POST /api/v1/auth/login`
```json
// Request
{ "email": "admin@techno.com", "password": "..." }

// Response
{ "success": true, "data": { "access_token": "...", "user": { "id": 1, "email": "...", "role": "admin" } } }
```

### Logic
1. Submit form → call login endpoint.
2. On success → store JWT + user in Zustand auth store.
3. Redirect to `/dashboard`.
4. If already logged in → redirect away from `/login`.

---

## 6. Phase 2 — Dashboard Page

### Key API Calls
| Action | Endpoint |
|--------|----------|
| Get today's scheduled groups | `GET /api/v1/academics/sessions/daily-schedule?day={dayName}` |
| Load attendance for a session | `GET /api/v1/attendance/session/{session_id}` |
| Save attendance | `POST /api/v1/attendance/session/{session_id}/mark` |

### Component Breakdown
```
DashboardPage
├── DaySelectorBar (Mon–Sun pills, defaults to today)
└── For each group in schedule:
    └── GroupSessionCard
        ├── Header (group name, time, instructor)
        ├── SessionNotes (expandable)
        └── AttendanceGrid (shared component — loaded lazily per card)
```

### Daily Schedule API Response Shape
```json
{
  "success": true,
  "data": [
    {
      "session_id": 42,
      "group_id": 5,
      "group_name": "Robotics A",
      "course_name": "Robotics",
      "instructor_name": "Ahmed Ali",
      "scheduled_time": "15:00",
      "end_time": "16:30",
      "session_notes": "Makeup session",
      "active_student_count": 8
    }
  ]
}
```

---

## 7. Phase 3 — Attendance Grid (Critical Component)

This is the **most complex reusable component**. Build it once, use it on Dashboard and Group Detail.

### Props Interface
```ts
interface AttendanceGridProps {
  sessions: Session[]        // Column headers
  enrollments: Enrollment[]  // Row headers (students)
  readOnly?: boolean         // Dashboard = read-only by default
  onSave?: (changes: AttendanceChanges) => void
}
```

### State Management Pattern
```
Local state: Map<sessionId, Map<studentId, AttendanceStatus>>
                    ↑
         Only updated on cell click (no network calls)
                    ↓
         "Save All" button → forEach session with changes → POST /attendance/session/{id}/mark
```

### Cell States
| Status | Display | Click Cycle |
|--------|---------|-------------|
| `null` | `◻️` | → `present` |
| `present` | `✅` | → `absent` |
| `absent` | `❌` | → `null` |
| `late` | `🕒` | → `null` (only set via popup) |
| `excused` | `➖` | → `null` (only set via popup) |

---

## 8. Phase 4 — Directory

### Parents Tab
- Search bar (min 2 chars) → `GET /api/v1/crm/parents?name={q}`
- Results table → click row → Parent Detail View
- "Register Parent" button → modal form → `POST /api/v1/crm/parents`

### Students Tab  
- Search bar → `GET /api/v1/crm/students?name={q}`
- "Browse All" → paginated `GET /api/v1/crm/students?skip=0&limit=15`
- Click row → Student Detail View

### Student Detail View (Most Data-Dense Page)
```
API calls to load:
  - GET /api/v1/crm/students/{id}
  - GET /api/v1/crm/students/{id}/parents
  - GET /api/v1/enrollments/student/{id}
  - GET /api/v1/finance/balance/student/{id}
```

---

## 9. Phase 5 — Enrollments Page

Three panels: **Enroll**, **Transfer**, **Drop**

### Enroll Panel
```
Student search → select
Group search → select  
Level → auto-filled
Amount Due → auto-calculated (editable)
Discount → number input
Notes → textarea
Submit → POST /api/v1/enrollments
```

### Transfer Panel
```
Select existing active enrollment
Select new group
Submit → POST /api/v1/enrollments/transfer
```

### Drop Panel
```
Select enrollment
Confirm dialog
Submit → DELETE /api/v1/enrollments/{id}
```

---

## 10. Phase 6 — Finance & Receipts

### Create Receipt
- Dynamic line items (add/remove rows).
- Each row: Student search + Enrollment select + Amount + Type.
- Overpayment preview: `POST /api/v1/finance/receipts/preview-risk`
- Submit: `POST /api/v1/finance/receipts`
- On success: show "Download PDF" button → `GET /api/v1/finance/receipts/{id}/pdf`

### Search Receipts
- Date range picker (required)
- Optional filters: payer name, student ID, receipt #
- `GET /api/v1/finance/receipts?from_date=&to_date=`

---

## 11. Design System Tokens (CSS Variables)

```css
/* src/index.css */
:root {
  /* Colors */
  --color-bg: #0f1117;
  --color-surface: #1a1d27;
  --color-surface-raised: #242736;
  --color-border: #2e3245;
  --color-accent: #6366f1;          /* Indigo */
  --color-accent-hover: #818cf8;
  --color-success: #22c55e;
  --color-danger: #ef4444;
  --color-warning: #f59e0b;
  --color-text: #e2e8f0;
  --color-text-muted: #94a3b8;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;

  /* Spacing */
  --radius: 8px;
  --radius-lg: 12px;
  --shadow: 0 4px 24px rgba(0,0,0,0.4);

  /* Sidebar */
  --sidebar-width: 240px;
  --sidebar-collapsed: 64px;
}
```

---

## 12. Protected Routes Pattern

```tsx
// src/App.tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}
```

---

## 13. TypeScript API Types

Key types to define in `src/types/api.ts`, mirroring backend Pydantic DTOs:

```ts
interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

interface DailyScheduleItem {
  session_id: number
  group_id: number
  group_name: string
  course_name: string
  instructor_name: string
  scheduled_time: string
  session_notes?: string
  active_student_count: number
}

interface StudentPublic {
  id: number
  full_name: string
  birth_date?: string
  gender?: string
  phone?: string
  is_active: boolean
  notes?: string
}

interface EnrollmentPublic {
  id: number
  student_id: number
  group_id: number
  level: number
  status: 'active' | 'completed' | 'dropped'
  amount_due: number
  discount: number
  enrolled_on: string
}

type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused' | null
```

---

## 14. Open Decisions for Next Session

> [!IMPORTANT]
> Clarify these at the START of the next chat before touching any code:
>
> 1. **Component Library?** Confirm: plain CSS only, or add a headless library (e.g., Radix UI or Headless UI for accessible modals/dropdowns)?
> 2. **Where to scaffold?** `frontend/` inside the existing workspace root, or a separate repository?
> 3. **Dev server port?** `5173` (Vite default) — confirm CORS is configured on the backend for this origin.
> 4. **PDF download button** — should it open in a new tab or force download? (Endpoint already returns `Content-Disposition: attachment`)

---

## 15. Backend API Checklist — Confirmed Ready

All endpoints consumed by the MVP frontend have been implemented and committed:

| Module | Status | Notes |
|--------|--------|-------|
| `POST /auth/login` | ✅ | Returns JWT + user |
| `GET /auth/me` | ✅ | Current user info |
| `GET /academics/sessions/daily-schedule` | ✅ | Dashboard power endpoint |
| `GET /academics/groups` | ✅ | Filter by day |
| `GET /academics/groups/{id}/sessions` | ✅ | |
| `GET /academics/groups/{id}/progress-level` | ✅ | |
| `GET/POST /attendance/session/{id}` | ✅ | Read + mark |
| `GET /crm/students` + `/{id}` | ✅ | Search + detail |
| `GET /crm/parents` + `/{id}` | ✅ | Search + detail |
| `GET/POST /enrollments` | ✅ | |
| `POST /enrollments/transfer` | ✅ | |
| `GET /finance/receipts` | ✅ | Search |
| `POST /finance/receipts` | ✅ | Create |
| `GET /finance/receipts/{id}/pdf` | ✅ | **New — just shipped** |
| `GET /finance/balance/student/{id}` | ✅ | For debt badges |
| `POST /finance/receipts/preview-risk` | ✅ | Overpayment check |

---

*Last Updated: 2026-04-02 — Ready to hand off to frontend developer*
