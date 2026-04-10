# Analytics API Reference

Analytics and business intelligence endpoints for the Techno Future CRM.

**Base Path:** `/api/v1/analytics`  
**Authentication:** Admin Bearer token required for all endpoints

---

## Module Documentation

The Analytics API is organized into four domain-specific modules:

| Module | Description | Endpoints | Documentation |
|--------|-------------|-----------|---------------|
| **Academic** | Enrollments, sessions, attendance, progress | 6 | [academic.md](./analytics/academic.md) |
| **BI** | Trends, retention, performance, risk analysis | 9 | [bi.md](./analytics/bi.md) |
| **Competition** | Competition participation and fees | 1 | [competition.md](./analytics/competition.md) |
| **Financial** | Revenue, debts, forecasting | 6 | [financial.md](./analytics/financial.md) |

**Total: 22 endpoints**

[Module Overview & Common Patterns](./analytics/README.md)

---

## 🔐 Authentication

All analytics endpoints require admin authentication via Bearer token:

```http
Authorization: Bearer <jwt_token>
```

### Authorization Requirements

| Endpoint Type | Required Role |
|---------------|---------------|
| All Analytics | `admin` |

Tokens are obtained through the [Auth API](./auth.md).

---

## Response Format

All endpoints return data in a standardized envelope:

### Success Response (200)
```json
{
  "success": true,
  "data": { ... },
  "message": "Description of result"
}
```

### Error Response (4xx/5xx)
```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "errors": [
    {
      "loc": ["query", "parameter_name"],
      "msg": "validation error message",
      "type": "error_type"
    }
  ]
}
```

---

## HTTP Status Codes

| Code | Meaning | When Returned |
|------|---------|---------------|
| 200 | OK | Request successful |
| 401 | Unauthorized | Missing or invalid Bearer token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 422 | Unprocessable Entity | Validation error (invalid parameters) |
| 500 | Internal Server Error | Unexpected server error |

---

## Quick Reference

### Academic Endpoints
```
GET  /api/v1/analytics/dashboard/summary
GET  /api/v1/analytics/academics/unpaid-attendees
GET  /api/v1/analytics/academics/groups/{group_id}/roster
GET  /api/v1/analytics/academics/groups/{group_id}/heatmap
GET  /api/v1/analytics/academics/student-progress
GET  /api/v1/analytics/academics/course-completion
```

### BI Endpoints
```
GET  /api/v1/analytics/bi/enrollment-trend
GET  /api/v1/analytics/bi/retention
GET  /api/v1/analytics/bi/instructor-performance
GET  /api/v1/analytics/bi/retention-funnel
GET  /api/v1/analytics/bi/instructor-value
GET  /api/v1/analytics/bi/schedule-utilization
GET  /api/v1/analytics/bi/flight-risk
GET  /api/v1/analytics/bi/user-engagement
GET  /api/v1/analytics/bi/retention-analysis
```

### Competition Endpoints
```
GET  /api/v1/analytics/competitions/fee-summary
```

### Financial Endpoints
```
GET  /api/v1/analytics/finance/revenue-by-date
GET  /api/v1/analytics/finance/revenue-by-method
GET  /api/v1/analytics/finance/outstanding-by-group
GET  /api/v1/analytics/finance/top-debtors
GET  /api/v1/analytics/finance/revenue-metrics
GET  /api/v1/analytics/finance/revenue-forecast
```

---

## Common Schemas

### DashboardSummaryPublic
High-level dashboard aggregates for admin view.

| Field | Type | Description |
|-------|------|-------------|
| active_enrollments | integer | Total active enrollments |
| today_sessions_count | integer | Sessions scheduled today |

```json
{
  "active_enrollments": 150,
  "today_sessions_count": 8
}
```

---

## Cross-Domain Analytics

Some business questions require combining endpoints from multiple modules:

### Student Retention Analysis
1. `GET /analytics/bi/retention` - Course retention rates
2. `GET /analytics/bi/retention-funnel` - Level progression funnel
3. `GET /analytics/academics/student-progress` - Individual progress

### Revenue Optimization
1. `GET /analytics/finance/outstanding-by-group` - Collection by group
2. `GET /analytics/finance/top-debtors` - Targeted collection
3. `GET /analytics/bi/flight-risk` - Pre-dropout intervention

### Instructor Evaluation
1. `GET /analytics/bi/instructor-performance` - Load metrics
2. `GET /analytics/bi/instructor-value` - Revenue correlation
3. `GET /analytics/bi/schedule-utilization` - Efficiency

---

*For detailed endpoint documentation, see the module-specific files linked above.*
