# Competitions API

Base paths:
- `/api/v1/competitions/*` - Competition lifecycle
- `/api/v1/teams/*` - Team lifecycle

Authentication: Bearer token required for all endpoints.

## Directory

| File | Contents |
|------|----------|
| [schemas.md](./schemas.md) | All DTOs and request/response schemas |
| [competitions.md](./competitions.md) | Competition endpoints |
| [teams.md](./teams.md) | Team and member endpoints |
| [errors.md](./errors.md) | Error codes and responses |

## 3-Table Schema

- Categories stored as `citext` on teams table (case-insensitive)
- Soft delete via `deleted_at` timestamp
- Team members have `member_share` for fee splitting
