# Health API Reference

Base path: `/`

---

## 🔐 Authentication
**Not Required** - Public endpoint for health checks

---

## Schemas

### Health Response
Returns a simple health status object. The exact schema is not formally defined but typically includes:

```json
{
  "status": "healthy",
  "timestamp": "2026-04-01T10:00:00Z"
}
```

Or may return a simple string/empty success response.

---

## Endpoints

### 1. Health Check
**GET** `/health`

**Response (200):** Simple health status

**Notes:**
- Used by load balancers and monitoring systems
- Returns 200 OK when API is operational
- No authentication required
- Quick lightweight check for service availability

**Example Response:**
```json
{
  "status": "healthy"
}
```

Or may return:
```
"OK"
```

---

## Usage Examples

### Kubernetes Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Docker Healthcheck
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1
```

### CI/CD Pipeline Check
```bash
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://api:8000/health)
if [ "$response" == "200" ]; then
  echo "API is healthy"
  exit 0
else
  echo "API health check failed"
  exit 1
fi
```
