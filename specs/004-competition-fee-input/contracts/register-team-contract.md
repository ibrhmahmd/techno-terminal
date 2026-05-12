# API Contract: POST /api/v1/teams

## Request Body

```json
{
  "competition_id": 1,
  "team_name": "RoboWarriors",
  "category": "Robotics",
  "subcategory": "Junior",
  "student_ids": [1, 2, 3],
  "student_fees": {
    "1": 50.0,
    "2": 30.0
  },
  "coach_id": 5,
  "group_id": 10,
  "notes": "Strong team this year"
}
```

### student_fees behavior

| Condition | member_share |
|-----------|-------------|
| In `student_ids` and in `student_fees` | Value from `student_fees` |
| In `student_ids` but NOT in `student_fees` | 0 |
| `student_fees` is `null` or missing | 0 for all students |
| `student_fees` is `{}` (empty) | 0 for all students |
| Key exists in `student_fees` but NOT in `student_ids` | Ignored |

## Response (201 Created)

```json
{
  "success": true,
  "data": {
    "team": {
      "id": 1,
      "competition_id": 1,
      "category": "Robotics",
      "subcategory": "Junior",
      "group_id": 10,
      "team_name": "RoboWarriors",
      "coach_id": 5,
      "placement_rank": null,
      "placement_label": null,
      "notes": "Strong team this year",
      "created_at": "2026-05-12T12:00:00Z"
    },
    "members_added": 3
  },
  "message": "Team registered successfully."
}
```

**Note**: `fee` field is removed from TeamDTO in response.
