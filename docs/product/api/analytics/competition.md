# Competition Analytics API

Endpoints for monitoring competition participation, team formation, and financial performance.

---

## Endpoints

### 1. Get Competition Fee Summary
`GET /analytics/competitions/fee-summary`

Returns a high-level overview of all competitions, including team/student counts and a summary of collected vs. outstanding fees.

**Response Body:** `ApiResponse[list[CompetitionFeeSummaryDTO]]`
```json
[
  {
    "competition_id": 5,
    "competition_name": "Regional Robotics Olympiad 2026",
    "competition_date": "2026-05-20",
    "team_count": 12,
    "member_count": 45,
    "fees_collected": 9000.0,
    "fees_outstanding": 1500.0
  }
]
```
