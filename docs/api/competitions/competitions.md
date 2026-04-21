# Competitions Endpoints

Base path: `/api/v1/competitions`

## List Competitions
```
GET /competitions
```

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| include_deleted | bool | Include soft-deleted (admin only) |

**Response**: `list[CompetitionDTO]`

---

## Create Competition
```
POST /competitions
```

**Request Body**: `CreateCompetitionInput`

**Response**: `CompetitionDTO`

---

## Get Competition
```
GET /competitions/{id}
```

**Response**: `CompetitionDTO`

**Errors**: 404 - Not found

---

## Update Competition (Full)
```
PUT /competitions/{id}
```

**Request Body**: `UpdateCompetitionInput`

**Response**: `CompetitionDTO`

**Errors**: 400 - No fields provided, 404 - Not found

---

## Update Competition (Partial)
```
PATCH /competitions/{id}
```

Same as PUT. Only provided fields are updated.

---

## Delete Competition
```
DELETE /competitions/{id}
```

Soft delete. Cannot delete if teams are registered.

**Response**: `bool`

**Errors**: 409 - Has teams

---

## Restore Competition
```
POST /competitions/{id}/restore
```

Restore soft-deleted competition.

**Response**: `bool`

---

## List Deleted Competitions
```
GET /competitions/deleted
```

Admin only.

**Response**: `list[CompetitionDTO]`

---

## Get Competition Summary
```
GET /competitions/{id}/summary
```

Full dashboard with teams nested by category.

**Response**: `CompetitionSummaryResponse`

Includes:
- `total_teams`: Count of all teams
- `total_participants`: Count of all members

---

## List Categories
```
GET /competitions/{id}/categories
```

Returns distinct categories and subcategories for autocomplete.

**Response**: `list[CategoryResponse]`

Derived from existing teams (3-table schema - no separate categories table).
