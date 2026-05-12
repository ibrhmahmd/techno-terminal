# API Contract: POST /api/v1/teams/{team_id}/members

## Request Body

```json
{
  "student_id": 4,
  "fee": 25.0
}
```

### fee behavior

| Condition | member_share |
|-----------|-------------|
| `fee` provided | Value of `fee` |
| `fee` missing or `null` | 0 |
| `fee` is 0 | 0 |

## Response (201 Created)

```json
{
  "success": true,
  "data": {
    "team_member_id": 10,
    "student_id": 4,
    "student_name": "John Doe"
  },
  "message": "Member added successfully."
}
```
