# Financial Analytics API

Endpoints for tracking revenue performance, payment methods, outstanding collections, and revenue forecasting.

---

## Endpoints

### 1. Get Revenue Breakdown by Date
`GET /analytics/finance/revenue-by-date`

Returns daily net revenue totals within a specified date range.

**Query Parameters:**
- `start` (required): Start date (YYYY-MM-DD).
- `end` (required): End date (YYYY-MM-DD). Date range cannot exceed 365 days.

**Response Body:** `ApiResponse[list[RevenueByDateDTO]]`
```json
[
  {
    "day": "2026-04-01",
    "net_revenue": 1250.75
  }
]
```

---

### 2. Get Revenue Breakdown by Method
`GET /analytics/finance/revenue-by-method`

Summarizes revenue and receipt counts grouped by the payment method (Cash, Card, Transfer, etc.) used.

**Query Parameters:**
- `start` (required): Start date (YYYY-MM-DD).
- `end` (required): End date (YYYY-MM-DD). Date range cannot exceed 365 days.

**Response Body:** `ApiResponse[list[RevenueByMethodDTO]]`
```json
[
  {
    "payment_method": "card",
    "net_revenue": 5200.0,
    "receipt_count": 15
  }
]
```

---

### 3. Get Outstanding Balances by Group
`GET /analytics/finance/outstanding-by-group`

Identifies groups with unpaid student balances, useful for targeting collection efforts.

**Response Body:** `ApiResponse[list[OutstandingByGroupDTO]]`
```json
[
  {
    "group_id": 10,
    "group_name": "Morning Group A",
    "course_name": "Robotics 101",
    "students_with_balance": 3,
    "total_outstanding": 1200.0
  }
]
```

---

### 4. Get Top Debtors
`GET /analytics/finance/top-debtors`

Returns an ordered list of students with the highest individual outstanding debts across the system.

**Query Parameters:**
- `limit` (optional): Maximum number of results to return (1-100, default: 15).

**Response Body:** `ApiResponse[list[TopDebtorDTO]]`
```json
[
  {
    "student_id": 50,
    "student_name": "Jane Smith",
    "parent_name": "Michael Smith",
    "phone_primary": "0123456789",
    "total_outstanding": -950.0
  }
]
```

---

### 5. Get Extended Revenue Metrics
`GET /analytics/finance/revenue-metrics`

Provides a comprehensive period-over-period revenue analysis, including trend direction and average revenue per receipt.

**Query Parameters:**
- `months` (optional): Number of months for trend analysis (1-24, default: 6).

**Response Body:** `ApiResponse[RevenueMetricsDTO]`
```json
{
  "period_start": "2026-01-01",
  "period_end": "2026-04-16",
  "total_revenue": 45000.0,
  "total_receipts": 120,
  "avg_revenue_per_receipt": 375.0,
  "previous_period_revenue": 42000.0,
  "revenue_change_pct": 7.14,
  "trend_direction": "up",
  "monthly_breakdown": [
    { "day": "2026-04-01", "net_revenue": 1200.0 }
  ]
}
```

---

### 6. Get Revenue Forecast
`GET /analytics/finance/revenue-forecast`

Uses historical trends to predict future revenue for a specified amount of months ahead, providing confidence intervals.

**Query Parameters:**
- `months_ahead` (optional): Number of months to forecast (1-12, default: 3).

**Response Body:** `ApiResponse[list[RevenueForecastDTO]]`
```json
[
  {
    "month": "2026-05",
    "predicted_revenue": 15000.0,
    "confidence_lower": 13500.0,
    "confidence_upper": 16500.0
  }
]
```
