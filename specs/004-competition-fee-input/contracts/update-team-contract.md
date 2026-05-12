# API Contract: PUT /api/v1/teams/{team_id}

## Request Body

```json
{
  "team_name": "RoboWarriors Updated",
  "category": "Robotics",
  "subcategory": "Senior",
  "group_id": null,
  "coach_id": 6,
  "notes": "Moved to senior category"
}
```

**Note**: `fee` field is removed from `UpdateTeamInput`. Team-level fee no longer exists.
