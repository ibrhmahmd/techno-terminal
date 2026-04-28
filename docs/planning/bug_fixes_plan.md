# Implementation Plan — Bug Fixes & API Alignment

This plan addresses the 35 issues identified in the code review, focusing on aligning the frontend with the established API contracts and fixing critical logic/UX bugs.

## User Review Required

> [!IMPORTANT]
> **API Contract Alignment**: Several API calls currently use incorrect paths or payload shapes. We will be updating `academics.ts`, `attendance.ts`, and `crm.ts` to strictly follow the `frontend_api_reference.md`.
> **Mock Data**: We will maintain mock fallbacks but ensure they match the *real* production schemas to avoid "it works in mock but fails in prod" scenarios.

---

## Proposed Changes

### 1. Global & Core API Alignment
Fixes base URL, auth redirects, and type safety.

#### [MODIFY] [client.ts](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/api/client.ts)
- Update `baseURL` to `/api/v1` (to match FastAPI prefix).
- Add `AbortController` support if needed for search.
- Change `window.location.href` to a more graceful session expiry handling (optional but recommended).

#### [MODIFY] [academics.ts](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/api/academics.ts)
- Fix `levelUpGroup` endpoint to `/academics/groups/${groupId}/progress-level`.
- Align `Group` and `Session` interfaces with `GroupPublic` and `SessionPublic`.
- Ensure `getGroupSessions` result is sorted or handled correctly in the UI.

#### [MODIFY] [crm.ts](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/api/crm.ts)
- Update `searchStudents` and `searchParents` to use query param `q`.
- Align `Student` and `Parent` interfaces with `StudentPublic` and `ParentPublic`.
- Add missing `national_id` and `relation` fields to `Parent` type.

#### [MODIFY] [attendance.ts](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/api/attendance.ts)
- Align `SessionAttendanceRowDTO.student_id` to `string`.
- Fix `markAttendance` to send `MarkAttendanceRequest` (using `student_statuses` map if required).

---

### 2. Dashboard & Attendance Fixes
Fixes the "broken" attendance grid and date selector.

#### [MODIFY] [DashboardPage.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/pages/DashboardPage.tsx)
- Fix `GroupSessionCard` prop mismatch (`mockStudents` removal/fix).
- Add `AbortController` to `loadSchedule` to prevent race conditions on day switch.

#### [MODIFY] [GroupSessionCard.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/components/dashboard/GroupSessionCard.tsx)
- Correct prop interface to handle mock data correctly.
- Improve `instructorInitials` and `sessionTime` robustness.

#### [MODIFY] [AttendanceGrid.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/components/attendance/AttendanceGrid.tsx)
- **CRITICAL**: Update logic to load ONLY the active session column's attendance, but clearly demarcate other columns as history.
- Fix `handleSaveAll` payload shape.
- Remove `alert()` and use a more subtle feedback mechanism (or leave for now if no toast provider exists).
- Fix unstable `useEffect` dependency array.

#### [MODIFY] [DaySelectorBar.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/components/dashboard/DaySelectorBar.tsx)
- Fix date parsing to avoid UTC shift (`new Date(y, m-1, d)`).

---

### 3. Groups Page Fixes
Fixes pagination, sorting, and form validation.

#### [MODIFY] [GroupsPage.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/pages/GroupsPage.tsx)
- Fix pagination counter logic.
- Ensure `currentPage` resets or guards against overflow when `pageSize` changes.
- Move `SortIndicator` out of the component body.
- Fix numeric sorting coercion.

#### [MODIFY] [GroupForm.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/components/groups/GroupForm.tsx)
- (Future) Replace text inputs with dropdowns for Instructors/Courses (requires new API calls).
- Tighten validation to avoid unsafe casts in parent.

---

### 4. Directory Page Fixes
Fixes search race conditions and tab state.

#### [MODIFY] [DirectoryPage.tsx](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/app/src/pages/DirectoryPage.tsx)
- **CRITICAL**: Remove double-filtering logic. Trust API results when searching.
- Fix clearing search (`searchTerm.length < 2`) — it should reload the full list.
- Reset search state on tab switch.
- Add basic pagination support (or "Load More").

---

## Verification Plan

### Automated Tests
- N/A (Manual browser testing via `browser_subagent`).

### Manual Verification
1. **Dashboard**: Switch days rapidly; verify no "jumping" UI or console errors. Verify attendance save payload in Network tab.
2. **Attendance**: Mark someone present, save, and reload; check consistency.
3. **Groups**: Sort by count; verify 10 comes after 9. Check pagination "Showing X to Y" text.
4. **Directory**: Search for a student, clear search; verify full list returns. Switch tabs while searching; verify state resets correctly.
