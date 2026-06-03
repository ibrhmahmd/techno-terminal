# Quickstart: Groups Day Order & Search Filter

## Day Ordering Fix

1. Add `DAY_ORDER` dict to `app/modules/academics/constants.py`
2. In `app/modules/academics/group/directory/service.py`, change the sort key in `get_groups_grouped()` from `x.label` to `DAY_ORDER.get(x.label, 99)`
3. Run existing `test_academics.py` tests to verify no regression

## Groups Filter

### Files to create/modify

| Action | File | Change |
|--------|------|--------|
| MODIFY | `app/modules/academics/group/directory/schemas.py` | Add `GroupFilterDTO`, `GroupFilterItemDTO`, `GroupFilterResultDTO` |
| MODIFY | `app/modules/academics/group/directory/interface.py` | Add `filter_groups()` to Protocol |
| MODIFY | `app/modules/academics/group/directory/service.py` | Add `filter_groups()` method with dynamic SQL |
| MODIFY | `app/modules/academics/group/directory/repository.py` | Expose enriched base query + any new helper queries |
| MODIFY | `app/api/routers/academics/group_directory_router.py` | Add `/filter` endpoint |
| MODIFY | `tests/test_academics.py` | Add filter tests |

### Filter Parameters (full list)

| Category | Parameters |
|----------|-----------|
| Text search | `q` (broad), `name`, `course_name`, `instructor_name` |
| Course | `course_ids`, `course_not` (historical exclusion) |
| Day | `day` (full name or abbreviation) |
| Instructor | `instructor_id`, `instructor_has_id` (ever had), `instructor_not_id` (never had) |
| Level | `level_number` (numeric rank) |
| Demographics | `gender`, `age_min`, `age_max` |
| Status | `status` |
| Pricing | `price_min`, `price_max` |
| Dates | `start_date_from`, `start_date_to` |
| Time | `time_from`, `time_to` |
| Session progress | `current_session_number`, `session_number_from`, `session_number_to` |
| Sort | `sort_by` (name/day/status), `sort_order` (asc/desc) |
| Pagination | `skip`, `limit` |

### Implementation order

1. DTOs first (schemas.py) — defines all input/output shapes
2. Repository — ensure base enriched query + history queries available
3. Service — `filter_groups()` with dynamic WHERE + ORDER BY + LIMIT/OFFSET
4. Interface — add method to Protocol
5. Router — wire `/filter` endpoint with `Depends(require_admin)`
6. Tests

### Test approach

- Use `mock_admin_headers` + `override_auth` fixtures (no real Supabase needed)
- Seed test groups via `db_session` fixture
- Test each filter parameter independently
- Test combined parameters (AND across params, OR within multi-value params)
- Test historical filters (course_not, instructor_has_id, instructor_not_id)
- Test empty results, pagination, sort order, day normalization
- Test day ordering fix: verify grouped-by-day endpoint returns correct order
