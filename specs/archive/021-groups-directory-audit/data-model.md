# Data Model Updates

## Modified Schemas (Pydantic DTOs)

### `GroupFilterDTO`
Added filtering parameters to cover all previously fragmented search criteria.
- **Added Fields**:
  - `has_instructor: Optional[bool]`
  - `max_capacity_min: Optional[int]`
  - `max_capacity_max: Optional[int]`
  - `include_inactive: bool = False`

### `GroupedItem`
Fixed a loosely typed constraint violating Constitution §III.
- **Modified Fields**:
  - `groups: list[dict]` -> `list[EnrichedGroupPublic]`

## Deleted Schemas
### `GroupListItem`
- Obsoleted by standardizing the list results to `EnrichedGroupPublic`, which includes more data (e.g., instructor names, course names) and prevents UI from receiving two distinct types of groups.
