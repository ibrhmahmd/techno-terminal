# API Contracts: Notifications Module Audit

## Changed Contracts

### POST /api/v1/notifications/bulk

**Change**: Response type from `ApiResponse[dict]` to `ApiResponse[BulkSendResultDTO]`:

```json
{
  "success": true,
  "data": {"queued_count": 5},
  "message": null
}
```

## Unchanged Contracts

All other notification endpoints keep their existing contracts.
