# Competition Analytics API

Analytics endpoints for competition metrics: participation tracking and fee collection.

**Base Path:** `/api/v1/analytics`  
**Tag:** `Analytics — Competition`  
**Authentication:** Admin required (`require_admin`)

---

## Endpoints

### 1. Get Competition Fee Summary
**GET** `/api/v1/analytics/competitions/fee-summary`

**Description:** Returns participation and fee summary for all competitions. Shows team count, member count, fees collected vs outstanding for each competition.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<CompetitionFeeSummaryResponse>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "competition_id": 1,
      "competition_name": "National Robotics Championship",
      "competition_date": "2026-05-15",
      "team_count": 8,
      "member_count": 24,
      "fees_collected": 12000.0,
      "fees_outstanding": 3000.0
    }
  ],
  "message": "Competition fee summary retrieved successfully."
}
```

---

## Schemas

### CompetitionFeeSummaryResponse
Participation and fee summary for a competition.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| competition_id | integer | Yes | Competition ID |
| competition_name | string | Yes | Competition name |
| competition_date | date | No | Competition date (YYYY-MM-DD) |
| team_count | integer | Yes | Number of teams registered |
| member_count | integer | Yes | Total team members across all teams |
| fees_collected | float | Yes | Total fees collected |
| fees_outstanding | float | Yes | Total fees still owed |

**Example:**
```json
{
  "competition_id": 1,
  "competition_name": "National Robotics Championship",
  "competition_date": "2026-05-15",
  "team_count": 8,
  "member_count": 24,
  "fees_collected": 12000.0,
  "fees_outstanding": 3000.0
}
```

---

## Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "success": false,
  "data": null,
  "message": "Not authenticated"
}
```

#### 403 Forbidden
```json
{
  "success": false,
  "data": null,
  "message": "Admin access required"
}
```

---

## Use Cases

### Fee Collection Tracking
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/competitions/fee-summary" \
  -H "Authorization: Bearer <token>"
```

**Use this to:**
- Identify competitions with high outstanding fees
- Track collection progress over time
- Compare participation vs fee collection rates
- Forecast revenue from upcoming competitions

---

[← Back to Analytics API Overview](../analytics.md)
