# Financial Analytics API

Analytics endpoints for financial metrics: revenue tracking, outstanding balances, and debtors analysis.

**Base Path:** `/api/v1/analytics`  
**Tag:** `Analytics — Financial`  
**Authentication:** Admin required (`require_admin`)

---

## Endpoints

### 1. Get Revenue by Date
**GET** `/api/v1/analytics/finance/revenue-by-date`

**Description:** Returns daily revenue totals within the specified date range.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| start | string (date) | Yes | Start date (YYYY-MM-DD) |
| end | string (date) | Yes | End date (YYYY-MM-DD) |

**Response (200):** `ApiResponse<list<RevenueByDateDTO>>`

**Error Responses:**
- 422 Validation Error - Invalid date format or start > end

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "day": "2026-04-01",
      "net_revenue": 15000.0
    },
    {
      "day": "2026-04-02",
      "net_revenue": 12000.0
    }
  ],
  "message": "Revenue by date retrieved successfully."
}
```

---

### 2. Get Revenue by Method
**GET** `/api/v1/analytics/finance/revenue-by-method`

**Description:** Returns revenue totals grouped by payment method within the date range.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| start | string (date) | Yes | Start date (YYYY-MM-DD) |
| end | string (date) | Yes | End date (YYYY-MM-DD) |

**Response (200):** `ApiResponse<list<RevenueByMethodDTO>>`

**Error Responses:**
- 422 Validation Error - Invalid date format or start > end

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "payment_method": "cash",
      "net_revenue": 8000.0,
      "receipt_count": 12
    },
    {
      "payment_method": "card",
      "net_revenue": 5000.0,
      "receipt_count": 8
    },
    {
      "payment_method": "transfer",
      "net_revenue": 4000.0,
      "receipt_count": 5
    }
  ],
  "message": "Revenue by method retrieved successfully."
}
```

---

### 3. Get Outstanding by Group
**GET** `/api/v1/analytics/finance/outstanding-by-group`

**Description:** Returns outstanding balance totals grouped by academic group. Useful for identifying which groups have the most collection issues.

**Authentication:** Admin required

**Response (200):** `ApiResponse<list<OutstandingByGroupDTO>>`

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "group_id": 1,
      "group_name": "Sat 2PM Robotics",
      "course_name": "Robotics Fundamentals",
      "students_with_balance": 5,
      "total_outstanding": 2500.0
    }
  ],
  "message": "Outstanding by group retrieved successfully."
}
```

---

### 4. Get Top Debtors
**GET** `/api/v1/analytics/finance/top-debtors`

**Description:** Returns students with highest outstanding balances for targeted collection efforts.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| limit | integer | No | 15 | ge=1, le=100 | Number of results to return |

**Response (200):** `ApiResponse<list<TopDebtorDTO>>`

**Error Responses:**
- 422 Validation Error - limit must be between 1 and 100

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "student_id": 1,
      "student_name": "Omar Mohamed",
      "parent_name": "Ahmed Mohamed",
      "phone_primary": "01123456789",
      "total_outstanding": -500.0
    }
  ],
  "message": "Top debtors retrieved successfully."
}
```

---

### 5. Get Revenue Metrics
**GET** `/api/v1/analytics/finance/revenue-metrics`

**Description:** Returns extended revenue metrics including trend analysis, monthly breakdown, and comparisons to previous periods.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| months | integer | No | 6 | ge=1, le=24 | Number of months to analyze |

**Response (200):** `ApiResponse<RevenueMetricsDTO>`

**Error Responses:**
- 422 Validation Error - months must be between 1 and 24

**Example Response:**
```json
{
  "success": true,
  "data": {
    "period_start": "2026-01-01",
    "period_end": "2026-06-30",
    "total_revenue": 450000.0,
    "total_receipts": 320,
    "avg_revenue_per_receipt": 1406.25,
    "previous_period_revenue": 420000.0,
    "revenue_change_pct": 7.14,
    "trend_direction": "up",
    "monthly_breakdown": [
      {"day": "2026-01-01", "net_revenue": 75000.0},
      {"day": "2026-02-01", "net_revenue": 72000.0}
    ]
  },
  "message": "Revenue metrics retrieved successfully."
}
```

---

### 6. Get Revenue Forecast
**GET** `/api/v1/analytics/finance/revenue-forecast`

**Description:** Returns revenue forecast for future months based on historical trends and scheduled payments.

**Authentication:** Admin required

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| months_ahead | integer | No | 3 | ge=1, le=12 | Number of months to forecast |

**Response (200):** `ApiResponse<list<RevenueForecastDTO>>`

**Error Responses:**
- 422 Validation Error - months_ahead must be between 1 and 12

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "month": "2026-07",
      "predicted_revenue": 480000.0,
      "confidence_lower": 384000.0,
      "confidence_upper": 576000.0
    },
    {
      "month": "2026-08",
      "predicted_revenue": 495000.0,
      "confidence_lower": 396000.0,
      "confidence_upper": 594000.0
    }
  ],
  "message": "Revenue forecast retrieved successfully."
}
```

---

## Schemas

### RevenueByDateDTO
Daily revenue total.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| day | date | Yes | Date (YYYY-MM-DD) |
| net_revenue | float | Yes | Net revenue for the day |

**Example:**
```json
{
  "day": "2026-04-01",
  "net_revenue": 15000.0
}
```

---

### RevenueByMethodDTO
Revenue grouped by payment method.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| payment_method | string | Yes | Payment method (cash, card, transfer, online) |
| net_revenue | float | Yes | Revenue for this method |
| receipt_count | integer | Yes | Number of receipts |

**Example:**
```json
{
  "payment_method": "cash",
  "net_revenue": 8000.0,
  "receipt_count": 12
}
```

---

### OutstandingByGroupDTO
Outstanding balance summary per group.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_id | integer | Yes | Group ID |
| group_name | string | Yes | Group name |
| course_name | string | Yes | Course name |
| students_with_balance | integer | Yes | Count of students owing money |
| total_outstanding | float | Yes | Total outstanding amount |

**Example:**
```json
{
  "group_id": 1,
  "group_name": "Sat 2PM Robotics",
  "course_name": "Robotics Fundamentals",
  "students_with_balance": 5,
  "total_outstanding": 2500.0
}
```

---

### TopDebtorDTO
Student with high outstanding balance.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student full name |
| parent_name | string | No | Parent/guardian name |
| phone_primary | string | No | Primary phone number |
| total_outstanding | float | Yes | Outstanding balance (negative = debt) |

**Example:**
```json
{
  "student_id": 1,
  "student_name": "Omar Mohamed",
  "parent_name": "Ahmed Mohamed",
  "phone_primary": "01123456789",
  "total_outstanding": -500.0
}
```

---

### RevenueMetricsDTO
Extended revenue metrics with trend analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| period_start | date | Yes | Analysis period start |
| period_end | date | Yes | Analysis period end |
| total_revenue | float | Yes | Total revenue in period |
| total_receipts | integer | Yes | Total receipt count |
| avg_revenue_per_receipt | float | Yes | Average per receipt |
| previous_period_revenue | float | Yes | Previous comparable period revenue |
| revenue_change_pct | float | Yes | Percentage change vs previous |
| trend_direction | string | Yes | "up", "down", or "stable" |
| monthly_breakdown | list[RevenueByDateDTO] | Yes | Monthly revenue details |

**Example:**
```json
{
  "period_start": "2026-01-01",
  "period_end": "2026-06-30",
  "total_revenue": 450000.0,
  "total_receipts": 320,
  "avg_revenue_per_receipt": 1406.25,
  "previous_period_revenue": 420000.0,
  "revenue_change_pct": 7.14,
  "trend_direction": "up",
  "monthly_breakdown": [
    {"day": "2026-01-01", "net_revenue": 75000.0},
    {"day": "2026-02-01", "net_revenue": 72000.0}
  ]
}
```

---

### RevenueForecastDTO
Revenue forecast for a future month.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| month | string | Yes | Month (YYYY-MM) |
| predicted_revenue | float | Yes | Predicted revenue |
| confidence_lower | float | Yes | Lower bound (80% confidence) |
| confidence_upper | float | Yes | Upper bound (80% confidence) |

**Example:**
```json
{
  "month": "2026-07",
  "predicted_revenue": 480000.0,
  "confidence_lower": 384000.0,
  "confidence_upper": 576000.0
}
```

---

## Revenue Calculation Methodology

### Net Revenue Definition
Net revenue = Total payments received - Total refunds issued

### Forecasting Method
Revenue forecast uses historical trends combined with:
1. **Historical Average**: Mean revenue from comparable months
2. **Trend Component**: Linear regression on recent months
3. **Scheduled Revenue**: Confirmed future payments

**Confidence Intervals:**
- Lower/Upper bounds represent 80% confidence interval
- Based on historical variance and seasonal adjustments

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

#### 422 Validation Error
```json
{
  "success": false,
  "data": null,
  "message": "Validation error",
  "errors": [
    {
      "loc": ["query", "start"],
      "msg": "invalid date format",
      "type": "value_error.date"
    }
  ]
}
```

---

## Use Cases

### Monthly Revenue Report
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/finance/revenue-by-date?start=2026-04-01&end=2026-04-30" \
  -H "Authorization: Bearer <token>"
```

### Identify Collection Issues by Group
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/finance/outstanding-by-group" \
  -H "Authorization: Bearer <token>"
```

### Top 20 Debtors for Collection Campaign
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/finance/top-debtors?limit=20" \
  -H "Authorization: Bearer <token>"
```

---

[← Back to Analytics API Overview](../analytics.md)
