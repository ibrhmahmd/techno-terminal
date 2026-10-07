# Research

**Feature**: Groups Directory Audit
**Date**: 2026-06-03

## Background
The audit discovered broken routing links (`GET /academics/groups/search` and `GET /academics/groups/by-type/{type}`) calling service functions that were deleted in the prior feature branch `020-groups-filter-day-order`. Also, some code was identified as dead or untyped.

## Technical Decisions

### Decision: API Endpoint Reductions
- **Rationale**: Since `GET /academics/groups/filter` provides an inclusive superset of the capabilities provided by `/search` and `/by-type/{type}`, maintaining multiple parallel routing structures violates DRY and creates unnecessary overhead.
- **Outcome**: `/search` and `/by-type/{type}` will be deleted and return HTTP 404, pointing consumers towards `/filter`.

### Decision: Active Default Status
- **Rationale**: If `filter_groups` query provides no `status`, the default behavior should be to return active groups. To show inactive groups, the `include_inactive=true` flag needs to be set. To show archived groups, `status=["archived"]` must explicitly be passed. This maps properly to typical business assumptions (end users generally only want to see active items).
- **Outcome**: The repository's `filter_groups_query` logic will enforce this status boundary.

### Decision: Pagination on `/enriched`
- **Rationale**: The previous unpaginated endpoint posed a long-term risk of large memory usage as the number of active groups increases.
- **Outcome**: The endpoint is refactored to consume pagination query params `skip` and `limit`, returning `PaginatedResponse[EnrichedGroupPublic]`.
