# API Contracts

## `GET /academics/groups`
Delegates to `filter_groups` using `status=["active"]`. Returns a paginated list of `EnrichedGroupPublic`.

## `GET /academics/groups/archived`
Delegates to `filter_groups` using `status=["archived"]`. Returns a paginated list of `EnrichedGroupPublic`.

## `GET /academics/groups/by-course/{course_id}`
Delegates to `filter_groups` using `course_ids=[course_id]`. Returns a paginated list of `EnrichedGroupPublic`. The query parameter `include_inactive` works seamlessly with the new default active-only behavior.

## `GET /academics/groups/enriched`
Paginated version of active groups, delegates to `filter_groups(status=["active"])`.

## Removed APIs
- `GET /academics/groups/search` -> **404 NOT FOUND**
- `GET /academics/groups/by-type/{type}` -> **404 NOT FOUND**
