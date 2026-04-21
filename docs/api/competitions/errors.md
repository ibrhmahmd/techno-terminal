# Error Responses

## HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Validation error, business rule violation |
| 401 | Unauthorized | Missing/invalid Bearer token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate name, already enrolled, paid member |

## Error Response Body

```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

## Common Error Scenarios

### 400 - Business Rule Violations
- "Subcategory required for this category"
- "Cannot set placement before competition date"
- "Fee is already paid"
- "Student is not active"

### 404 - Not Found
- Competition not found
- Team not found
- Student not found
- Team member not found

### 409 - Conflicts
- "Team name already exists in this competition"
- "Student already enrolled in another team"
- "Cannot delete team with paid members"
- "Student already a member of this team"

### 401/403 - Auth
- Missing Authorization header
- Invalid/expired token
- User lacks admin role for admin endpoints
