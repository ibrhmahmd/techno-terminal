# Analytics API Module

Analytics and reporting endpoints for the Techno Future CRM system.

---

## Module Overview

The Analytics API provides comprehensive business intelligence and operational metrics across four domains:

| Domain | File | Endpoints | Purpose |
|--------|------|-----------|---------|
| **Academic** | [academic.md](./academic.md) | 6 | Enrollments, sessions, attendance, student progress |
| **BI** | [bi.md](./bi.md) | 9 | Trends, retention, performance, risk analysis |
| **Competition** | [competition.md](./competition.md) | 1 | Competition participation and fees |
| **Financial** | [financial.md](./financial.md) | 6 | Revenue, debts, forecasting |

**Total: 22 endpoints**

---

## Common Patterns

### Response Envelope

All analytics endpoints return data wrapped in a standardized envelope:

```json
{
  "success": boolean,
  "data": T | null,
  "message": string,
  "errors": ErrorDetail[] | null  // only on error
}
```

### Authentication

All analytics endpoints require **Admin authentication** via Bearer token:

```bash
Authorization: Bearer <jwt_token>
```

### Error Handling

Standard HTTP status codes:
- `200 OK` - Success
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Token valid but insufficient permissions
- `422 Unprocessable Entity` - Validation error (invalid parameters)

---

## Cross-Domain Analytics

Some business questions require combining multiple analytics endpoints:

### Student Retention Analysis
1. `GET /analytics/bi/retention` - Course retention rates
2. `GET /analytics/bi/retention-funnel` - Level progression funnel
3. `GET /analytics/academics/student-progress` - Individual student progress

### Revenue Optimization
1. `GET /analytics/finance/outstanding-by-group` - Collection issues by group
2. `GET /analytics/finance/top-debtors` - Target collection efforts
3. `GET /analytics/bi/flight-risk` - Identify at-risk students before they drop

### Instructor Performance
1. `GET /analytics/bi/instructor-performance` - Group and student counts
2. `GET /analytics/bi/instructor-value` - Revenue correlation
3. `GET /analytics/bi/schedule-utilization` - Time slot efficiency

---

## Quick Reference

### Academic Endpoints
```
GET /api/v1/analytics/dashboard/summary
GET /api/v1/analytics/academics/unpaid-attendees
GET /api/v1/analytics/academics/groups/{group_id}/roster
GET /api/v1/analytics/academics/groups/{group_id}/heatmap
GET /api/v1/analytics/academics/student-progress
GET /api/v1/analytics/academics/course-completion
```

### BI Endpoints
```
GET /api/v1/analytics/bi/enrollment-trend
GET /api/v1/analytics/bi/retention
GET /api/v1/analytics/bi/instructor-performance
GET /api/v1/analytics/bi/retention-funnel
GET /api/v1/analytics/bi/instructor-value
GET /api/v1/analytics/bi/schedule-utilization
GET /api/v1/analytics/bi/flight-risk
GET /api/v1/analytics/bi/user-engagement
GET /api/v1/analytics/bi/retention-analysis
```

### Competition Endpoints
```
GET /api/v1/analytics/competitions/fee-summary
```

### Financial Endpoints
```
GET /api/v1/analytics/finance/revenue-by-date
GET /api/v1/analytics/finance/revenue-by-method
GET /api/v1/analytics/finance/outstanding-by-group
GET /api/v1/analytics/finance/top-debtors
GET /api/v1/analytics/finance/revenue-metrics
GET /api/v1/analytics/finance/revenue-forecast
```

---

[← Back to Analytics API Overview](../analytics.md)
