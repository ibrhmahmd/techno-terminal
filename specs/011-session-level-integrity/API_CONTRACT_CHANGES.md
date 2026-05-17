# API Contract Changes — Spec 011: Session Level Integrity

> Frontend teams: review each section below. **Breaking changes** are marked with ⚠️.

---

## ⚠️ GET `/academics/groups/{group_id}/sessions` — Session List

### What changed
When the `level` query parameter is **omitted**, the endpoint no longer returns **all** sessions across every level. It now returns only sessions belonging to the **group's current active level**.

### Before (old behavior)
```
GET /academics/groups/{group_id}/sessions
→ all sessions for the group, all levels
```

### After (new behavior)
```
GET /academics/groups/{group_id}/sessions
→ only sessions for the group's current active level

GET /academics/groups/{group_id}/sessions?level=2
→ only sessions for level 2 (unchanged)
```

### Migration
- If you need **all sessions across all levels**, either:
  - Call this endpoint multiple times with explicit `level` params, **or**
  - Use `GET /academics/groups/{group_id}/levels/detailed` which returns sessions nested under each level
- If you only need current-level sessions (most UI views), **omit the `level` param** and you now get the right data automatically.

---

## ⚠️ GET `/academics/groups/{group_id}/levels/detailed` — Level Details

### What changed
When the `level_number` query parameter is **omitted**, the endpoint no longer returns **all** levels. It now returns only the **current active level**.

### Before (old behavior)
```
GET /academics/groups/{group_id}/levels/detailed
→ all levels with their sessions and stats
```

### After (new behavior)
```
GET /academics/groups/{group_id}/levels/detailed
→ only the current active level with its sessions and stats

GET /academics/groups/{group_id}/levels/detailed?level_number=2
→ only level 2 (unchanged)
```

### Migration
- If you need **all levels**, pass `level_number=-1` or switch to the dedicated levels endpoint
- If you only need the active level's data (most dashboard views), omit the param

---

## ⚠️ POST `/academics/courses` — Create Course (Validation Limits)

### What changed
Two new validation limits on course creation:

| Field | Old Limit | New Limit | Break? |
|-------|-----------|-----------|--------|
| `sessions_per_level` | ≥ 1 | 1–100 | ⚠️ Yes — requests with >100 now fail with 422 |
| `max_levels` *(new)* | N/A | 1–100 (optional, nullable) | No — new field, defaults to `null` |

### New field: `max_levels`

```json
{
  "name": "Engineering with Scratch",
  "sessions_per_level": 12,
  "price_per_level": 250.00,
  "max_levels": 4
}
```

- `max_levels` is **optional** (`null` by default)
- When set, limits how many levels can be created for this course
- Validation error: `"Course cannot exceed 100 levels"` or `"Number of sessions per level must not exceed 100"`

---

## Summary of required frontend changes

| Endpoint | Action Required |
|----------|----------------|
| **Session list** (no `level` param) | Verify UI still works — now returns only current-level sessions. If you used this for a "show all sessions" view, pass explicit `level` param or use the levels/detailed endpoint. |
| **Levels detailed** (no `level_number` param) | Same — verify views that call this without `level_number` still display correctly with only one level. |
| **Create course** | Ensure `sessions_per_level` ≤ 100 to avoid 422 errors. Optionally add `max_levels` UI field. |
