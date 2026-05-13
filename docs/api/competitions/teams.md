# Teams Endpoints

Base path: `/api/v1/teams`

## List Teams
```
GET /teams
```

**Query Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| competition_id | int | Yes | Filter by competition |
| category | string | No | Filter by category |
| subcategory | string | No | Filter by subcategory |
| include_members | bool | No | Default: true |

**Response**: `list[TeamWithMembersDTO]` or `list[TeamDTO]`

---

## Register Team
```
POST /teams
```

**Request Body**: `RegisterTeamInput`

**Response**: `TeamRegistrationResultDTO`

**Business Rules**
- Team name must be unique within competition
- One student cannot be in multiple teams per competition
- If category has subcategories, subcategory is required

**Errors**: 400 (validation), 404 (student/competition not found), 409 (duplicate name/student enrolled)

---

## Get Team
```
GET /teams/{id}
```

**Response**: `TeamDTO`

---

## Update Team (Full)
```
PUT /teams/{id}
```

**Request Body**: `UpdateTeamInput`

**Response**: `TeamDTO`

---

## Update Team (Partial)
```
PATCH /teams/{id}
```

Same as PUT. Only provided fields are updated.

---

## Delete Team
```
DELETE /teams/{id}
```

Soft delete. Cannot delete if any member has paid fees.

**Response**: `bool`

**Errors**: 409 - Has paid members

---

## Restore Team
```
POST /teams/{id}/restore
```

**Response**: `bool`

---

## List Deleted Teams
```
GET /teams/deleted
```

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| competition_id | int | Filter by competition |

**Response**: `DeletedTeamListResponse`

---

## List Team Members
```
GET /teams/{id}/members
```

**Response**: `TeamMemberListResponse`

Each member entry includes `team_id` and `team_name` for display purposes. Team name is fetched efficiently in a single query (no extra round-trip).

---

## Add Team Member
```
POST /teams/{id}/members
```

**Request Body**: `AddTeamMemberInput`

**Response**: `AddTeamMemberResultDTO`

**Business Rules**
- Student cannot already be in another team for this competition
- Student must be active

---

## Remove Team Member
```
DELETE /teams/{id}/members/{student_id}
```

**Response**: `bool`

**Errors**: 400 - Cannot remove paid member

---

## Pay Competition Fee
```
POST /teams/{id}/members/{student_id}/pay
```

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| parent_id | int | Parent for payment attribution |

**Response**: `PayCompetitionFeeResponseDTO`

**Business Rules**
- Atomic: creates receipt + marks fee paid
- Auto-rollback on failure
- Cannot pay if fee already paid

**Errors**: 400 - Fee already paid

---

## Update Placement
```
PATCH /teams/{id}/placement
```

**Request Body**: `PlacementUpdateInput`

**Response**: `TeamDTO`

**Business Rules**
- Can only set after competition date has passed

**Errors**: 400 - Competition date not passed

---

## Get Student Competitions
```
GET /students/{id}/competitions
```

Returns all competitions a student is registered in.

**Response**: `StudentCompetitionsResponse`

Sorted by competition date descending.
