# Code Review — Dashboard, Groups, Directory Pages

**Reviewed:** April 2, 2026  
**Scope:** `DashboardPage.tsx`, `GroupsPage.tsx`, `DirectoryPage.tsx` + all directly consumed components and API modules.

---

## Severity Legend

| Label | Meaning |
|-------|---------|
| 🔴 **Critical** | Will break at runtime or corrupt data |
| 🟠 **High** | Visible bug or broken UX flow |
| 🟡 **Medium** | Silent misbehavior or bad pattern |
| 🔵 **Low** | Code quality / DX / minor UX |

---

## 1. Dashboard Page (`DashboardPage.tsx` + deps)

---

### 🔴 BUG-01 — `GroupSessionCard` prop contract broken (mock data mismatch)

**File:** `DashboardPage.tsx` line 212 / `GroupSessionCard.tsx` line 5–9  
**Root Cause:**  
`GroupSessionCard` is typed to accept:
```ts
interface GroupSessionCardProps {
  group: Group
  sessions: Session[]
  selectedDate: string
  // NO mockStudents prop
}
```
But `DashboardPage` passes `mockStudents` as a prop (line 212):
```tsx
mockStudents={useMockData ? MOCK_STUDENT_ATTENDANCE[group.id] : undefined}
```
TypeScript will **error** on this because `mockStudents` is not in the interface and `GroupSessionCard` never reads it. The mock student data is silently dropped — the attendance grid will always be empty when in mock mode.

**Fix:** Either add `mockStudents?: MockStudentAttendance[]` to `GroupSessionCardProps` and thread it into `AttendanceGrid`, or remove the prop from `DashboardPage`.

---

### 🔴 BUG-02 — `MOCK_STUDENT_ATTENDANCE` uses `number` IDs but `StudentAttendanceState` expects `number`; `AttendanceUpdate` sends `string`

**File:** `AttendanceGrid.tsx` line 104 / `attendance.ts` line 18  
**Root Cause:**  
```ts
// In AttendanceGrid.tsx
const updates: AttendanceUpdate[] = students.map(s => ({
  student_id: String(s.student_id),   // converts number → string ✅
  ...
}))
```
That part is fine. But the `SessionAttendanceRowDTO` type in `attendance.ts` line 4 says:
```ts
student_id: number
```
While the API might return integers (if it's a numeric PK), the rest of the CRM uses `string` UUIDs. This creates a **live type contract mismatch** that will silently coerce IDs. If the backend returns string UUIDs here too, `Number(studentId)` in `AttendanceGrid` row key (line 200) will produce `NaN`, causing React key collisions.

**Fix:** Align `SessionAttendanceRowDTO.student_id` to `string` to match the rest of the codebase.

---

### 🔴 BUG-03 — `AttendanceGrid` only loads ONE session's attendance but renders columns for up to FIVE sessions

**File:** `AttendanceGrid.tsx` lines 52–85  
**Root Cause:**  
```ts
const attendanceData = await getSessionAttendance(activeSessionId!)
```
Only the **active session** is fetched. All other session columns are initialized to `null` (line 62: `Array(displaySessions.length).fill(null)`).  
The grid then renders 5 columns, but 4 are always blank — they display empty `◻` cells that cannot be clicked. This gives the **false appearance** of historical data being loaded, when it never is.

**Fix:** Either fetch attendance for each session column in parallel (loop over `displaySessions`), or be explicit that columns 1–4 are "read-only history" and only the active column is editable — but actually load historical data.

---

### 🔴 BUG-04 — `markAttendance` sends wrong payload shape

**File:** `AttendanceGrid.tsx` line 109 / `attendance.ts` line 27  
**Root Cause:**  
`AttendanceGrid` calls:
```ts
await markAttendance(activeSessionId, updates)
```
But `markAttendance` in `attendance.ts` sends:
```ts
await client.post(`/attendance/session/${sessionId}/mark`, { attendance })
```
The API spec (from `frontend_handover.md` §11) requires:
```json
{ "student_statuses": { "101": "present", "102": "absent" } }
```
The actual payload sent is `{ attendance: [...] }` — **wrong field name and wrong format.** This will cause a **422 Unprocessable Entity** on every save.

**Fix:** Rebuild the payload to match the API contract, OR verify with the backend team that `{ attendance: [...] }` is the accepted format and update the docs.

---

### 🔴 BUG-05 — `DaySelectorBar` week calculation is wrong for Sunday

**File:** `DaySelectorBar.tsx` lines 12–16  
**Root Cause:**  
```ts
const dayOfWeek = today.getDay() // 0 = Sunday, 6 = Saturday
const saturday = new Date(today)
saturday.setDate(today.getDate() - ((dayOfWeek + 1) % 7))
```
`getDay()` returns `0` for Sunday and `6` for Saturday.  
- When `dayOfWeek = 0` (Sunday): `(0 + 1) % 7 = 1` → subtracts 1 → **lands on Saturday ✅**  
- When `dayOfWeek = 6` (Saturday): `(6 + 1) % 7 = 0` → subtracts 0 → **stays on same date ✅**  
- When `dayOfWeek = 5` (Friday): `(5 + 1) % 7 = 6` → subtracts 6 days → **lands 6 days back, on SATURDAY of previous week ✅**

Actually on inspection the formula is correct — but the **bigger problem** is the component uses `new Date(selectedDate)` (line 11), which parses an ISO `YYYY-MM-DD` string as **UTC midnight**. In Egypt (UTC+2), calling `.getDay()` on that will return the **previous day's** day-of-week during the night hours 00:00–01:59 local time, causing the wrong week to be highlighted.

**Fix:** Parse the date without timezone shift:
```ts
const [y, m, d] = selectedDate.split('-').map(Number)
const today = new Date(y, m - 1, d) // local date, no UTC shift
```

---

### 🟠 BUG-06 — Dashboard loading spinner overlaps the `DaySelectorBar`

**File:** `DashboardPage.tsx` lines 186–218  
**Root Cause:**  
The `DaySelectorBar` is rendered **before** the loading gate, so it's always visible even while loading new day data. But all group cards are replaced by a spinner, making the day selector feel disconnected — users can keep clicking days while the previous load is running, stacking multiple concurrent API calls with no abort controller.

**Fix:**
1. Add `AbortController` to cancel previous `getDailySchedule` calls when `selectedDate` changes.
2. Disable the day selector while `isLoading` is `true`.

---

### 🟠 BUG-07 — `getGroupSessions` is called with wrong session ordering

**File:** `DashboardPage.tsx` line 149  
```ts
sessionsMap[group.id] = sessions.slice(0, 5)
```
The API response from `/academics/groups/{id}/sessions` is not guaranteed to be ordered by date. The dashboard may display the wrong 5 sessions (e.g., first 5 created, not the 5 most recent). The active session for today may not even be in the slice.

**Fix:** Sort by `session.date` descending before slicing, or add `?order_by=date&direction=desc` to the API call.

---

### 🟠 BUG-08 — `getGroupProgress` uses `POST` instead of `GET`

**File:** `academics.ts` line 110  
```ts
const response = await client.post(`.../progress-level`)
```
This is a data-fetching operation that should be `GET`. Using `POST` to fetch data is semantically wrong and will fail on APIs that enforce HTTP method semantics. Additionally, `POST` requests are not cached and will bypass any HTTP-level caching.

**Fix:** Change to `client.get(...)`.

---

### 🟡 BUG-09 — `useEffect` dependency array in `AttendanceGrid` is unstable

**File:** `AttendanceGrid.tsx` line 85  
```ts
}, [activeSessionId, displaySessions.length, resolvedActiveIndex])
```
`resolvedActiveIndex` is derived from `displaySessions` and `activeSessionId` — it changes every render because `displaySessions` is a new array reference each time. This may cause **redundant API calls** on every parent re-render.

**Fix:** Memoize `displaySessions` with `useMemo` inside the component, or use `useRef` to track previous `activeSessionId`.

---

### 🟡 BUG-10 — `alert()` used for feedback in `AttendanceGrid`

**File:** `AttendanceGrid.tsx` lines 110, 113  
Calls `alert("Attendance saved successfully!")` and `alert("Failed to save changes.")`. This blocks the UI thread and is unacceptable in a professional admin interface.

**Fix:** Use a toast notification system or an inline success/error banner.

---

### 🟡 BUG-11 — Session time display shows raw API time strings (e.g., "15:00:00+00:00")

**File:** `GroupSessionCard.tsx` lines 19–20  
The `sessions[0].start_time` field coming from the API is a full ISO datetime or a time-with-timezone string like `15:00:00+00:00`. The `formatTime()` helper in `GroupSessionCard` doesn't handle the `+HH:MM` timezone suffix correctly (the regex `^\d{1,2}:\d{2}$` won't match), so it falls through to `new Date(timeStr)` which then formats in the **browser's local timezone**. This is actually the correct behavior for Egypt, but it's fragile and undocumented.

**Fix:** Add explicit handling for `HH:MM:SS+HH:MM` format strings, or normalize all time values at the API layer.

---

### 🟡 BUG-12 — `SESSION_DATES` hardcoded constant is dead code

**File:** `AttendanceGrid.tsx` line 40  
```ts
const SESSION_DATES = ['Dec 07', 'Dec 14', 'Dec 21', 'Dec 28', 'Jan 04']
```
This constant is used as a fallback in session headers when `session.start_time` is falsy (line 181). These are hardcoded 2024 dates from development. If `start_time` is missing, users will see "Dec 07" dates in 2026.

**Fix:** Remove the fallback or generate placeholder dates dynamically from the session's actual date field.

---

### 🔵 BUG-13 — "New Enrollment" button navigates to non-existent route

**File:** `TopNavbar.tsx` line 34  
```ts
onClick={() => navigate('/enrollments/new')}
```
The router in `App.tsx` only has `/enrollments` — there is no `/enrollments/new` route. This will render a 404/blank page on click.

**Fix:** Navigate to `/enrollments` or add `enrollments/new` as a route.

---

### 🔵 BUG-14 — Global search bar in TopNavbar is non-functional

**File:** `TopNavbar.tsx` lines 21–27  
The search input has no `onChange`, no `onSubmit`, no value binding. It's a pure visual placeholder with no behavior.

**Fix:** Either wire it up to a real search action or remove it to avoid user confusion.

---

## 2. Groups Page (`GroupsPage.tsx` + deps)

---

### 🔴 BUG-15 — `handleCreateGroup` uses a type-unsafe cast

**File:** `GroupsPage.tsx` line 98–100  
```ts
const handleCreateGroup = async (data: Partial<Omit<Group, 'id'>>) => {
  const newGroup = await createGroup(data as Omit<Group, 'id'>)
```
`createGroup` in `academics.ts` expects `CreateGroupInput`:
```ts
interface CreateGroupInput {
  name: string           // required
  course_name: string    // required
  instructor_name: string // required
  ...
}
```
But `data` is `Partial<...>` — all fields optional. The `as` cast suppresses TypeScript's safety check, meaning a form submission with a missing name will be sent to the API, returning a validation error that the user sees as a generic "Failed to create group."

**Fix:** Validate inside `handleCreateGroup` or change `GroupForm.onSubmit` prop type to require the full `CreateGroupInput`.

---

### 🔴 BUG-16 — `getGroupProgress` is never called but `progressGroupLevel` endpoint is wrong

**File:** `academics.ts` line 194  
```ts
export async function levelUpGroup(groupId: string): Promise<Group> {
  const response = await client.post(`/academics/groups/${groupId}/level-up`)
```
The API docs and `missing-features-implementation-plan.md` specify the endpoint as:
```
POST /api/v1/academics/groups/{group_id}/progress-level
```
The actual implementation uses `/level-up` — wrong path. When called, this will return a 404.

**Fix:** Change to `/academics/groups/${groupId}/progress-level`.

---

### 🟠 BUG-17 — Pagination "showing X to Y" counter is wrong when list is empty

**File:** `GroupsPage.tsx` line 168  
```tsx
Showing {processedGroups.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} to {Math.min(currentPage * pageSize, processedGroups.length)} of {processedGroups.length} entries
```
When `processedGroups.length = 0`, the "to" part renders `Math.min(10 * 10, 0) = 0`, yielding `"Showing 0 to 0 of 0 entries"`. Slightly cosmetic but confusing.

**Fix:** Guard the entire string: if length is 0, show `"No entries"`.

---

### 🟠 BUG-18 — `currentPage` not reset when search term changes

**File:** `GroupsPage.tsx` line 137  
```tsx
onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1) }}
```
`currentPage` IS reset on search change ✅. However, `currentPage` is NOT reset when `sortField` or `sortDirection` change in `handleSort` — actually it IS (line 52: `setCurrentPage(1)`). ✅  

The real issue: when `pageSize` is increased via the dropdown and the total page count drops below `currentPage`, the pagination shows a blank page. `processedGroups.slice((currentPage-1)*pageSize, ...)` where `start >= processedGroups.length` silently returns `[]`, rendering an empty table with no error.

**Fix:** Add a guard: `if (currentPage > totalPages && totalPages > 0) setCurrentPage(totalPages)` in a `useEffect`.

---

### 🟠 BUG-19 — `GroupForm` does not fetch real instructors or courses — uses free-text inputs

**File:** `GroupForm.tsx` lines 103–117  
The handover spec requires:
> Instructor — Dropdown (from `GET /api/v1/hr/employees`)  
> Course — Dropdown (from `GET /api/v1/academics/courses`)

Instead, the form uses free-text `<input>` fields. This means:
- Instructor names can be mistyped and won't link to any actual employee record
- Course names are not validated against real courses
- The API response for `createGroup` may fail FK constraint checks

**Fix:** Add `useEffect` in `GroupForm` to fetch courses and employees, and replace text inputs with `<select>` dropdowns.

---

### 🟡 BUG-20 — Sorting by `student_count` compares string vs number inconsistently

**File:** `GroupsPage.tsx` lines 63–77  
`student_count` is typed as `number` in the `Group` interface. The sort uses:
```ts
if (typeof aValue === 'number' && typeof bValue === 'number') {
  return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
}
```
This is correct for numeric sort. However, if the API returns `student_count` as a string (common in JSON APIs), both values will be of type `string`, falling through to `localeCompare`, producing **lexicographic sort** (e.g., "10" < "9").

**Fix:** Explicitly coerce: `Number(a[sortField])` before comparing.

---

### 🟡 BUG-21 — Error state and success state share the same `error` variable

**File:** `GroupsPage.tsx` lines 104–106  
```ts
} catch {
  setError('Failed to create group')
}
```
If a group is created successfully after a previous load error, `setError(null)` is called on line 103. But if create fails, the error banner **replaces** the existing load error text with "Failed to create group". There's no visual distinction between a loading error and a mutation error.

**Fix:** Use separate state: `loadError` and `mutationError`.

---

### 🔵 BUG-22 — `SortIndicator` is defined inside the component body on every render

**File:** `GroupsPage.tsx` lines 109–118  
```tsx
const SortIndicator = ({ field }: { field: SortField }) => { ... }
```
Defining a component inside another component causes React to **remount** it on every parent render (new component reference = new tree node). This is a performance anti-pattern.

**Fix:** Move `SortIndicator` outside `GroupsPage` or convert it to a pure functional expression.

---

## 3. Directory Page (`DirectoryPage.tsx` + deps)

---

### 🔴 BUG-23 — Double filtering: API search AND client-side filter run simultaneously

**File:** `DirectoryPage.tsx` lines 69–101  
There are TWO concurrent filtering mechanisms:

**Mechanism 1 — API search** (`useEffect` lines 69–93):  
When `searchTerm.length >= 2`, fires `searchStudents(searchTerm)` after 300ms debounce, **replaces** the `students` state with results.

**Mechanism 2 — Client-side filter** (lines 95–101):  
```ts
const filteredStudents = searchTerm.length < 2
  ? students
  : students.filter(s => s.full_name.toLowerCase().includes(searchTerm.toLowerCase()))
```
When the API search completes and sets `students`, the client filter runs **again** on the already-filtered API results. This is redundant and wasteful, but worse: if the API returns a partial match (e.g., fuzzy search), the client filter may hide valid results that don't contain the exact search string.

**Fix:** Use only ONE strategy. If the API supports search, trust the API results and render them directly (remove client-side filter). If the API doesn't support search well, use only client-side filter.

---

### 🔴 BUG-24 — Search clears when switching tabs

**File:** `DirectoryPage.tsx` line 93  
```ts
}, [searchTerm, activeTab])
```
When the user types "Ahmed" on the Students tab, then switches to Parents tab, the `useEffect` fires immediately with the same `searchTerm` for parents. But the `students` state is NOT reset — so switching back to Students renders the old search results with the original data.

More critically: switching tabs does **not** reload the base data for the new tab. If a user:
1. Starts on Students, loads 15 students
2. Searches "Ahmed" → `students` state is filtered to search results
3. Switches to Parents tab → search fires for parents
4. Switches back to Students → shows only the search results, NOT all students (no reload)
5. Clears search → `students.filter(...)` returns full results... but `students` state still has the old search result set from step 2

**Fix:** Reset the data for the tab being switched TO using a `useEffect` that depends on `[activeTab]`, and clear `searchTerm` on tab switch.

---

### 🔴 BUG-25 — `handleCreateStudent` has a broken type cast

**File:** `DirectoryPage.tsx` lines 103–111  
```ts
const handleCreateStudent = async (data: Partial<Omit<Student, 'id'>>) => {
  const newStudent = await createStudent(data as Omit<Student, 'id'>)
```
`createStudent` in `crm.ts` accepts `Omit<Student, 'id'>` which requires:
- `full_name: string` ← required
- `is_active: boolean` ← required

But `data` is `Partial<...>`, so `is_active` and `full_name` might be `undefined`. The `as` cast silently bypasses TypeScript's protection, and a missing `is_active` will cause the backend to return a validation error.

**Fix:** The `StudentForm` already constructs a proper `submitData` object with `is_active` — the `onSubmit` prop type should be `(data: Omit<Student, 'id'>) => Promise<void>` (non-partial).

---

### 🟠 BUG-26 — Search only queries 2 chars minimum but doesn't reset to full list when cleared

**File:** `DirectoryPage.tsx` lines 69–93  
When `searchTerm` is cleared (backspace to empty), the `useEffect` returns early (`if (searchTerm.length < 2) return`). But the `students`/`parents` state still holds the **last search results**, not the initial full list.

Users who type "Ali" → see filtered results → backspace to "" → still see only the "Ali" results with no way to get back the full list except refreshing the page.

**Fix:** When `searchTerm` becomes `< 2` characters, reload the initial paginated data (call `getStudents(0, 15)` again).

---

### 🟠 BUG-27 — No pagination for Directory lists

**File:** `DirectoryPage.tsx` lines 50–53  
```ts
const [studentsData, parentsData] = await Promise.all([
  getStudents(0, 15),
  getParents(0, 15),
])
```
Only the first 15 students and 15 parents are ever loaded. There's no "Load More", "Next Page", or infinite scroll. A center with 200 students would only see the first 15 with no way to browse further.

**Fix:** Add pagination controls (matching the pattern already implemented in `GroupsPage`), or implement infinite scroll.

---

### 🟠 BUG-28 — Newly created student/parent appears at top but won't survive a tab switch

**File:** `DirectoryPage.tsx` lines 104–107  
```ts
setStudents(prev => [newStudent, ...prev])
```
The new student is prepended to the **current filtered list** (which may be search results or mock data). When the user switches tabs and comes back, the student disappears because the list is not re-fetched.

**Fix:** After successful create, reload the full data, or store newly created items in a separate "optimistic" state that merges with the server state.

---

### 🟡 BUG-29 — `error` state is shown even after successful create

**File:** `DirectoryPage.tsx` lines 108, 120  
```ts
setError(null)  // clears error after create success
```
This correctly clears error. However, if a **load** error happened previously (e.g., API unreachable), the page shows mock data AND the error banner. The user then creates a student successfully → `setError(null)` hides the "API not available" banner, but the data on screen is still mock data.  
The visual feedback is misleading — it appears the system is working normally.

**Fix:** Track API availability separately from mutation errors.

---

### 🟡 BUG-30 — `isLoading` state is shared between initial load and search

**File:** `DirectoryPage.tsx` lines 38, 75  
The same `isLoading` flag is used for both initial data load and search operations. When search fires, `setIsLoading(true)` hides the entire list for 300ms (debounce) + API response time. This makes typing in the search field feel laggy.

**Fix:** Use separate loading states: `isInitialLoading` and `isSearching`. Show a subtle search spinner instead of hiding the whole list.

---

### 🔵 BUG-31 — `StudentForm` renders `gender: 'other'` option but `Student` type only allows `string | null`

**File:** `StudentForm.tsx` line 116  
```tsx
<option value="other">Other</option>
```
The backend API and `Student` interface don't document "other" as a valid gender. If the backend has an enum, this will cause a 422 error.

**Fix:** Confirm allowed gender values with the backend and remove unsupported options.

---

### 🔵 BUG-32 — `Parent` interface is missing `national_id` and `relation` fields

**File:** `crm.ts` lines 13–20  
```ts
export interface Parent {
  id: string
  full_name: string
  phone?: string | null
  email?: string | null
  address?: string | null
  is_active: boolean
}
```
The `frontend_handover.md` spec and `missing-features-implementation-plan.md` mention `national_id` and `relation` (Father/Mother/Guardian) fields. `ParentForm` likely doesn't capture these either.

---

## Cross-Cutting Issues

---

### 🔴 BUG-33 — No 401/403 redirect guard on page components

**File:** `client.ts` lines 20–28  
The Axios interceptor handles 401 globally. However, if the JWT expires mid-session (e.g., user leaves the page open), the interceptor fires `window.location.href = '/login'` as a **hard navigate**, wiping all React state without warning or saving drafts.

**Fix:** Use `navigate('/login')` from React Router's navigation context, and show a "Session expired" message before redirecting.

---

### 🟠 BUG-34 — `baseURL` is `/api` but actual FastAPI prefix is `/api/v1`

**File:** `client.ts` line 5 / all API modules  
```ts
baseURL: '/api',
```
But every API call uses paths like `/crm/students`, which means the actual URL becomes `/api/crm/students`. The FastAPI backend serves at `/api/v1/crm/students`.

This only works if Vite's proxy rewrites `/api` → `http://localhost:8000/api/v1`. This must be verified in `vite.config.ts` — if the proxy target is `http://localhost:8000` without path rewriting, all API calls will 404.

**Fix:** Either set `baseURL: '/api/v1'` and remove the proxy rewrite, or explicitly document the proxy rewrite requirement.

---

### 🟡 BUG-35 — No global error boundary

None of the three pages have React Error Boundaries. An uncaught render-time error (e.g., `group.name.toLowerCase()` when `name` is null) will crash the entire page tree with a blank white screen.

**Fix:** Wrap each page with an `<ErrorBoundary>` component.

---

## Summary Table

| ID | Page | Severity | Issue |
|----|------|----------|-------|
| BUG-01 | Dashboard | 🔴 Critical | `mockStudents` prop not in `GroupSessionCard` interface |
| BUG-02 | Dashboard | 🔴 Critical | student_id type mismatch number/string |
| BUG-03 | Dashboard | 🔴 Critical | AttendanceGrid only loads 1 of 5 session columns |
| BUG-04 | Dashboard | 🔴 Critical | `markAttendance` sends wrong payload shape |
| BUG-05 | Dashboard | 🔴 Critical | DaySelectorBar UTC date shift causes wrong week |
| BUG-06 | Dashboard | 🟠 High | No abort on concurrent day selection clicks |
| BUG-07 | Dashboard | 🟠 High | `getGroupSessions` slices unsorted data |
| BUG-08 | Dashboard | 🟠 High | `getGroupProgress` uses POST instead of GET |
| BUG-09 | Dashboard | 🟡 Medium | Unstable `useEffect` deps cause extra API calls |
| BUG-10 | Dashboard | 🟡 Medium | `alert()` used for save feedback |
| BUG-11 | Dashboard | 🟡 Medium | Time display fragile with timezone strings |
| BUG-12 | Dashboard | 🟡 Medium | Hardcoded 2024 dates as fallback |
| BUG-13 | Dashboard | 🔵 Low | "New Enrollment" navigates to missing route |
| BUG-14 | Dashboard | 🔵 Low | Global search bar is non-functional |
| BUG-15 | Groups | 🔴 Critical | `createGroup` type-unsafe Partial cast |
| BUG-16 | Groups | 🔴 Critical | `levelUpGroup` uses wrong endpoint path |
| BUG-17 | Groups | 🟠 High | Pagination counter wrong when empty |
| BUG-18 | Groups | 🟠 High | Blank table when pageSize > total results |
| BUG-19 | Groups | 🟠 High | Groups form uses free-text instead of dropdowns |
| BUG-20 | Groups | 🟡 Medium | Numeric sort broken if API returns string numbers |
| BUG-21 | Groups | 🟡 Medium | Load error and mutation error share same state |
| BUG-22 | Groups | 🔵 Low | `SortIndicator` defined inside component body |
| BUG-23 | Directory | 🔴 Critical | Double-filtering: API + client side both active |
| BUG-24 | Directory | 🔴 Critical | Tab switch doesn't reset data/search state |
| BUG-25 | Directory | 🔴 Critical | `createStudent` type-unsafe Partial cast |
| BUG-26 | Directory | 🟠 High | Clearing search doesn't restore full list |
| BUG-27 | Directory | 🟠 High | No pagination (only 15 records ever visible) |
| BUG-28 | Directory | 🟠 High | New record lost after tab switch |
| BUG-29 | Directory | 🟡 Medium | Error banner hidden after create, but data is still mock |
| BUG-30 | Directory | 🟡 Medium | Single `isLoading` flag causes jarring search UX |
| BUG-31 | Directory | 🔵 Low | `gender: 'other'` may fail backend validation |
| BUG-32 | Directory | 🔵 Low | Parent interface missing `national_id`, `relation` |
| BUG-33 | Global | 🔴 Critical | JWT expiry causes hard page reload instead of graceful redirect |
| BUG-34 | Global | 🟠 High | `baseURL` may not match actual API path `/api/v1` |
| BUG-35 | Global | 🟡 Medium | No React Error Boundary on any page |

**Total: 35 issues** — 9 Critical · 10 High · 9 Medium · 7 Low
