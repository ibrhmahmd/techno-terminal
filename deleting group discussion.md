# Spec 035 — Group Deletion Workflow Investigation

## Context

The client has experienced accidental group deletions. This spec is a **full-stack investigation** of the group deletion/deactivation workflow — from database foreign-key constraints, through the backend service layer, to the frontend confirmation UX — to document exactly what happens today, identify risks, and propose hardening.

---

## 1. Current Deletion Architecture (What Happens Today)

### 1.1 Frontend → API Call

| Surface | Action | Code Path |
|---------|--------|-----------|
| **GroupsPage** (listing) | 🗑️ Delete icon in row actions | [GroupsPage.tsx:148-178](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/src/pages/GroupsPage.tsx#L148-L178) — calls `deleteGroup(groupId)` |
| **GroupDetailPage** (detail view) | 🗑️ Trash2 button in header | [GroupDetailPage.tsx:80-88](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/src/pages/GroupDetailPage.tsx#L80-L88) — calls `deleteGroup()` via `useGroupMutations` |
| **GroupCard** (card view) | 🗑️ Delete menu item | [GroupCard.tsx:98](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/src/components/groups/GroupCard.tsx#L98) |

All three surfaces call the **same** API function:

```ts
// src/api/academics/groups/core.ts:175
export async function deleteGroup(groupId: number): Promise<void> {
  await client.delete(`/academics/groups/${groupId}`);
}
```

### 1.2 Confirmation Dialog

Both `GroupsPage` and `GroupDetailPage` show a `ConfirmDialog` before calling:

```tsx
// GroupDetailPage.tsx:287-295
<ConfirmDialog
  title="Delete Group"
  message="Are you sure you want to delete this group? This action cannot be undone."
  confirmText="Delete"
  variant="danger"
/>
```

> [!WARNING]
> **The message says "cannot be undone"** — but the backend operation is actually a **soft status change** (→ `'inactive'`). The dialog text is **misleading** and contributes to user panic after accidental clicks.

### 1.3 Backend Endpoint

```
DELETE /api/v1/academics/groups/{group_id}
```

Defined in [groups_router.py:135-153](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/academics/groups_router.py#L135-L153):

```python
@router.delete("/academics/groups/{group_id}")
def deactivate_group(group_id, svc=Depends(get_group_service)):
    group = svc.deactivate_group(group_id)     # ← status → 'inactive'
    return ApiResponse(data=GroupPublic.model_validate(group),
                       message="Group deactivated successfully.")
```

Auth guard: **`require_admin`** — only `admin` and `system_admin` roles.

### 1.4 Service Layer

[GroupCoreService.deactivate_group](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/core/service.py#L94-L109):

```python
def deactivate_group(self, group_id: int) -> Group:
    group.status = GROUP_STATUS_INACTIVE  # "inactive"
    apply_update_audit(group)
    session.commit()
    return group
```

> [!IMPORTANT]
> **This is NOT a hard delete.** It's a status flip to `'inactive'`. No rows are deleted from any table.

---

## 2. Database Foreign Key Constraint Map

This is what the DB would enforce if a `DELETE FROM groups WHERE id = X` were ever issued (it never is today):

### Tables with FK to `groups.id`

| Child Table | Column | ON DELETE | Impact |
|---|---|---|---|
| `group_levels` | `group_id` | **CASCADE** | All levels **hard-deleted** |
| `sessions` | `group_id` | **RESTRICT** | **Blocks** delete if any sessions exist |
| `enrollments` | `group_id` | **RESTRICT** | **Blocks** delete if any enrollments exist |
| `group_course_history` | `group_id` | **CASCADE** | All history records deleted |
| `teams` (competitions) | `group_id` | **SET NULL** | Team's `group_id` set to `NULL` |

### Cascade chain if hard-delete were possible

```
groups DELETE
 ├── group_levels CASCADE → deleted
 │    └── enrollment_level_history.group_level_id RESTRICT → ⛔ BLOCKED
 │    └── sessions.group_level_id SET NULL → sessions remain, level FK nulled
 ├── sessions.group_id RESTRICT → ⛔ BLOCKED
 ├── enrollments.group_id RESTRICT → ⛔ BLOCKED  
 │    └── attendance.enrollment_id RESTRICT → ⛔ BLOCKED
 │    └── payments.enrollment_id SET NULL → payment FK nulled
 │    └── enrollment_level_history.enrollment_id CASCADE → deleted
 └── group_course_history CASCADE → deleted
```

> [!NOTE]
> The RESTRICT constraints on `sessions` and `enrollments` mean a **real SQL DELETE is impossible** for any group that has ever had students enrolled or sessions scheduled. The database is correctly guarded at the schema level.

---

## 3. What the Soft Delete (Status → 'inactive') **Actually Affects**

### 3.1 Enrollment Operations — **BLOCKED**

[EnrollmentCoreService.enroll_student](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/enrollments/core/service.py#L51-L52):
```python
if group.status != "active":
    raise BusinessRuleError(f"Group '{group.name}' is not active...")
```

Also blocks transfers **to** an inactive group ([line 245](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/enrollments/core/service.py#L245)).

**Existing enrollments remain untouched** — no status changes, no drops.

### 3.2 Listing Visibility — **HIDDEN by default**

The [filter_groups_query](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/directory/repository.py#L219-L229) defaults to `WHERE g.status = 'active'`:

```python
if filters.status:
    where_clauses.append("g.status = ANY(:status)")
else:
    if filters.include_inactive:
        where_clauses.append("g.status = ANY(:default_status)")  # ['active','inactive']
    else:
        where_clauses.append("g.status = :default_status")        # 'active'
```

Frontend default: `useState<string[]>(['active'])` in [useGroups.ts:38](file:///e:/Users/ibrahim/Desktop/techno_terminal_UI/src/hooks/useGroups.ts#L38).

→ **Inactive groups vanish from the listing immediately.**

### 3.3 Sessions — **UNAFFECTED**

Sessions remain in `scheduled` status. No cancellation cascade. The attendance grid still works if accessed directly by group ID.

### 3.4 Payments — **UNAFFECTED**

All payment records linked via `payments → enrollments → groups` remain intact. No financial data is lost or modified.

### 3.5 Level Progression — **BLOCKED**

[GroupLifecycleService.add_level_to_existing_group](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/lifecycle/service.py#L342-L343):
```python
if group.status != GROUP_STATUS_ACTIVE:
    raise BusinessRuleError(f"Group {data.group_id} is not active")
```

### 3.6 Group Detail Page — **STILL ACCESSIBLE**

Direct navigation to `/groups/{id}` still loads the group. The enriched query has **no status filter** ([get_enriched_group_by_id](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/directory/repository.py#L27-L59)), so the detail page works fine.

### 3.7 Dashboard / Grouped Views — **HIDDEN**

The grouped-groups endpoint ([get_enriched_groups](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/directory/repository.py#L88)) filters `WHERE g.status = 'active'`.

---

## 4. Recovery Path — **MISSING**

> [!CAUTION]
> **There is NO UI or API endpoint to reactivate an inactive group.** Once deleted (deactivated), the only recovery paths are:
> 1. Direct database `UPDATE groups SET status = 'active' WHERE id = X` 
> 2. Using the generic `PATCH /academics/groups/{group_id}` with `{ "status": "active" }` — but the frontend has no UI for this

The backend `update_group` method ([service.py:47-59](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/group/core/service.py#L47-L59)) accepts arbitrary field updates including `status`, so the API already supports reactivation — the frontend simply doesn't expose it.

---

## 5. Root Cause Analysis of Accidental Deletions

| Risk Factor | Severity | Detail |
|---|---|---|
| **Delete button too accessible** | 🔴 HIGH | Trash icon is always visible in GroupInfoCard header next to Edit/Archive with no safeguards beyond a single confirm dialog |
| **Misleading dialog text** | 🟠 MEDIUM | "This action cannot be undone" is false — it's a soft delete that can be reversed |
| **No 'Type to confirm'** | 🟠 MEDIUM | A single "Delete" click confirms. No group name confirmation required |
| **No undo/toast with revert** | 🟠 MEDIUM | After deletion, user is redirected to `/groups` with no ability to undo |
| **No reactivation UI** | 🔴 HIGH | Admin cannot self-recover without DB access or API knowledge |
| **Delete on listing page** | 🟡 LOW | GroupsPage also has a delete action in row/card actions with the same weak confirmation |
| **No pre-flight warnings** | 🔴 HIGH | No check or display of "This group has X active enrollments, Y sessions, Z payments" before delete |

---

## 6. Summary: Status Transition Diagram

```
                ┌──────────────────────────────────────────────┐
                │              Group Status Machine            │
                │                                              │
     create     │  ┌────────┐    archive     ┌───────────┐    │
   ─────────────┤─►│ active │──────────────►│ completed │    │
                │  └────┬───┘                └───────────┘    │
                │       │                                      │
                │       │ deactivate (DELETE endpoint)         │
                │       ▼                                      │
                │  ┌──────────┐                                │
                │  │ inactive │  ← NO UI PATH TO REVERSE       │
                │  └──────────┘                                │
                └──────────────────────────────────────────────┘
```

---

## Open Questions for Discussion

> [!IMPORTANT]
> ### Q1: Should "Delete" continue to mean "soft deactivate"?
> The current mapping of HTTP `DELETE` → status flip is semantically fine, but the UI language ("Delete", "cannot be undone") creates a mismatch. Options:
> - **A)** Keep DELETE but fix the dialog text to say "Deactivate" and explain it's reversible
> - **B)** Remove the DELETE endpoint entirely and only use Archive (which already exists)
> - **C)** Add real "hard delete" that first checks for zero enrollments, zero sessions, zero payments

> [!IMPORTANT]
> ### Q2: Should we build a "Reactivate Group" UI?
> The backend already supports `PATCH /academics/groups/{group_id}` with `{ "status": "active" }`. We just need:
> - A filter toggle to show inactive groups in the listing
> - A "Reactivate" button on inactive group detail pages
> - Confirmation dialog with appropriate messaging

> [!IMPORTANT]
> ### Q3: Should we add pre-flight safety checks before deactivation?
> Before allowing a delete/deactivate, the backend should return (or the frontend should fetch and display):
> - Count of active enrollments
> - Count of scheduled (future) sessions
> - Count of unpaid balances
> - Whether the group has active competition teams
>
> This would let the admin understand the impact before confirming.

> [!IMPORTANT]
> ### Q4: Should we require "type group name to confirm" for destructive actions?
> A stronger confirmation pattern (like GitHub's repo deletion) would prevent accidental clicks.

---

## Proposed Next Steps

Once the above questions are answered, the implementation plan would cover:

1. **Backend**: Add a pre-flight check endpoint or enrich the DELETE response
2. **Backend**: Optionally add a dedicated `POST /academics/groups/{group_id}/reactivate` endpoint
3. **Frontend**: Fix dialog text and confirmation UX
4. **Frontend**: Add inactive groups visibility toggle
5. **Frontend**: Add reactivation flow
6. **Frontend**: Add pre-flight impact summary in the confirmation dialog
