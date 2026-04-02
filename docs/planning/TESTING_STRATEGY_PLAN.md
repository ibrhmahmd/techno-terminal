# API Testing Strategy & Implementation Plan

**Date:** 2026-04-02  
**Project:** Techno Terminal — FastAPI Test Suite  
**Backlog Item:** C5 — Automated Test Suite (21 SP)  
**Status:** Ready for Implementation

---

## Executive Summary

This document outlines a **phased testing strategy** for the Techno Terminal FastAPI layer. The goal is to build a comprehensive pytest-based test suite that validates API contracts, prevents regressions, and provides confidence for frontend team integration.

**Total Estimated Effort:** 21 Story Points (~18-22 hours of development work)

**Key Principles:**
- **API Safety First:** No breaking changes to existing endpoints
- **Mock External Dependencies:** Supabase JWT mocked, no real auth calls in tests
- **Transaction Isolation:** Each test rolls back DB changes
- **Prioritized by Risk:** Auth first, then error handlers, then business logic

---

## Phase Overview

| Phase | Focus Area | Endpoints | Status | Priority |
|:---:|:---|:---:|:---:|:---:|
| **1** | Infrastructure & Auth | 6 | 🔴 Not Started | 🔴 Critical |
| **2** | Error Handling | Global | 🟡 Partial | 🟡 High |
| **3** | CRM | 9 | ✅ Complete | 🟢 Done |
| **4** | Enrollments | 4 | ✅ Complete | 🟢 Done |
| **5** | Finance | 8 | ✅ Complete | 🟢 Done |
| **6** | Attendance | 2 | 🔴 Not Started | 🔴 Critical |
| **7** | Academics | 14 | 🔴 Not Started | � Critical |
| **8** | Competitions | 8 | 🔴 Not Started | 🟡 Medium |
| **9** | HR | 7 | 🔴 Not Started | 🟡 Medium |
| **10** | Analytics | 19 | 🔴 Not Started | � Low |
| **Total** | | **83** | **27 Tested (33%)** | |

**Phase Success Criteria:** Each phase must achieve >80% coverage of its target endpoints before proceeding to next phase.

**Current Coverage:** 27/83 endpoints tested (33%)
- ✅ CRM: 9/9 (100%)
- ✅ Enrollments: 4/4 (100%)
- ✅ Finance: 8/8 (100%)
- ❌ Auth: 0/6 (0%)
- ❌ Attendance: 0/2 (0%)
- ❌ Academics: 0/14 (0%)
- ❌ Competitions: 0/8 (0%)
- ❌ HR: 0/7 (0%)
- ❌ Analytics: 0/19 (0%)

---

## Phase 1: Infrastructure & Auth Testing (5 SP)

**Goal:** Establish testing foundation and validate authentication layer.

**Why First:** All subsequent tests depend on working auth infrastructure.

### 1.1 Files to Create

```
tests/
├── __init__.py              # Makes tests a package
├── conftest.py              # Shared fixtures
├── utils/
│   ├── __init__.py
│   ├── jwt_mocks.py         # Supabase JWT mock generation
│   └── db_helpers.py        # Test data utilities
└── test_auth.py             # Authentication tests
```

### 1.2 Code Implementation

**tests/conftest.py:**
```python
"""
Test configuration and shared fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from app.api.main import create_app
from tests.utils.jwt_mocks import generate_mock_supabase_token


@pytest.fixture(scope="session")
def app():
    """FastAPI application instance."""
    return create_app()


@pytest.fixture(scope="function")
def client(app):
    """FastAPI TestClient instance — fresh for each test."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    """Generate valid admin JWT for testing."""
    return generate_mock_supabase_token(
        user_id="test-admin-001",
        role="admin",
        email="admin@test.com"
    )


@pytest.fixture
def system_admin_token():
    """Generate valid system_admin JWT for testing."""
    return generate_mock_supabase_token(
        user_id="test-sysadmin-001",
        role="system_admin",
        email="sysadmin@test.com"
    )


@pytest.fixture
def admin_headers(admin_token):
    """Auth headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def system_admin_headers(system_admin_token):
    """Auth headers with system_admin token."""
    return {"Authorization": f"Bearer {system_admin_token}"}


@pytest.fixture
def db_session():
    """
    Database session for test data setup.
    Uses transaction rollback for test isolation.
    """
    from app.db.connection import get_session
    session = get_session()
    try:
        yield session
        session.rollback()  # Clean up test data
    finally:
        session.close()
```

**tests/utils/jwt_mocks.py:**
```python
"""
Mock Supabase JWT generation for tests.
Uses HS256 with a test secret (never use in production).
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional

TEST_SECRET = "test-secret-for-local-testing-only-never-use-in-prod"


def generate_mock_supabase_token(
    user_id: str,
    role: str,
    email: str,
    expires_in_minutes: int = 30
) -> str:
    """
    Generate a mock Supabase-style JWT for testing.
    
    Mimics the structure of Supabase auth tokens:
    {
        "sub": "user-uuid",
        "role": "authenticated",
        "app_metadata": {"role": "admin"},
        "email": "user@example.com",
        "iat": 1234567890,
        "exp": 1234567890
    }
    
    Args:
        user_id: Unique user identifier (maps to users.supabase_uid)
        role: User role (admin, system_admin)
        email: User email address
        expires_in_minutes: Token expiration time
        
    Returns:
        Valid JWT token string
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": "authenticated",
        "app_metadata": {"role": role},
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=expires_in_minutes)
    }
    
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def decode_mock_token(token: str) -> dict:
    """
    Decode a mock token for verification in tests.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
    """
    return jwt.decode(token, TEST_SECRET, algorithms=["HS256"])


def generate_expired_token(user_id: str, role: str, email: str) -> str:
    """Generate an expired token for testing 401 responses."""
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": "authenticated",
        "app_metadata": {"role": role},
        "email": email,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1)  # Expired 1 hour ago
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")
```

**tests/utils/db_helpers.py:**
```python
"""
Test database utilities for creating test data.
"""
from sqlmodel import Session
from app.modules.crm.models import Student, Parent
from app.modules.academics.models import Course, Group
from typing import Optional


def create_test_parent(
    session: Session,
    full_name: str = "Test Parent",
    phone_primary: str = "+201000000001",
    email: Optional[str] = None
) -> Parent:
    """Create a test parent record."""
    parent = Parent(
        full_name=full_name,
        phone_primary=phone_primary,
        email=email
    )
    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent


def create_test_student(
    session: Session,
    full_name: str = "Test Student",
    birth_date: Optional[str] = None,
    parent_id: Optional[int] = None
) -> Student:
    """Create a test student record."""
    student = Student(
        full_name=full_name,
        birth_date=birth_date,
        is_active=True
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def create_test_course(
    session: Session,
    name: str = "Test Course",
    category: str = "software",
    price_per_level: float = 1000.0
) -> Course:
    """Create a test course record."""
    course = Course(
        name=name,
        category=category,
        price_per_level=price_per_level
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


# ... additional helpers for groups, enrollments, receipts
```

**tests/test_auth.py:**
```python
"""
Authentication endpoint tests — Phase 1 Priority.
Validates JWT handling, role verification, and error responses.
"""
import pytest
from tests.utils.jwt_mocks import generate_expired_token


class TestAuthMe:
    """Tests for GET /api/v1/auth/me endpoint."""
    
    def test_auth_me_success_with_admin(self, client, admin_headers):
        """
        GET /auth/me with valid admin token returns 200 + user info.
        
        Expected:
        - Status: 200 OK
        - Response: {success: true, data: {email, role, id}}
        - Role: "admin"
        """
        response = client.get("/api/v1/auth/me", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["email"] == "admin@test.com"
        assert data["data"]["role"] == "admin"
    
    def test_auth_me_success_with_system_admin(self, client, system_admin_headers):
        """
        GET /auth/me with valid system_admin token returns 200 + user info.
        
        Expected:
        - Status: 200 OK
        - Role: "system_admin"
        """
        response = client.get("/api/v1/auth/me", headers=system_admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "system_admin"
    
    def test_auth_me_no_token(self, client):
        """
        GET /auth/me without token returns 401 Unauthorized.
        
        Expected:
        - Status: 401
        - Response: {success: false, error: "Unauthorized"}
        """
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Unauthorized"
    
    def test_auth_me_invalid_token_format(self, client):
        """
        GET /auth/me with malformed token returns 401.
        
        Expected:
        - Status: 401
        - No server error (graceful handling)
        """
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-format"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_auth_me_expired_token(self, client):
        """
        GET /auth/me with expired token returns 401.
        
        Expected:
        - Status: 401
        - Token expiration detected
        """
        expired_token = generate_expired_token(
            user_id="expired-user",
            role="admin",
            email="expired@test.com"
        )
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401


class TestAuthProtectedEndpoints:
    """Tests that protected endpoints reject unauthenticated requests."""
    
    def test_crm_students_requires_auth(self, client):
        """GET /crm/students without auth returns 401."""
        response = client.get("/api/v1/crm/students")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_finance_receipts_requires_auth(self, client):
        """POST /finance/receipts without auth returns 401."""
        response = client.post("/api/v1/finance/receipts", json={})
        
        assert response.status_code == 401
```

### 1.3 Phase 1 Success Criteria

- [ ] `pytest tests/test_auth.py` passes all tests
- [ ] Mock JWT generation works without real Supabase connection
- [ ] Database fixtures clean up after each test (no test data leakage)
- [ ] Coverage: 100% of auth endpoints covered

### 1.4 Time Estimate

| Task | Hours |
|:---|:---:|
| conftest.py setup | 1.5 |
| jwt_mocks.py implementation | 1.5 |
| db_helpers.py basic utilities | 1.5 |
| test_auth.py comprehensive tests | 2 |
| **Total** | **6.5 hours** |

---

## Phase 2: Error Handling & Validation (3 SP)

**Goal:** Verify standardized error responses across all error types.

**Why Second:** Error format is part of API contract — frontend depends on consistent structure.

### 2.1 Files to Create

```
tests/
└── test_error_handlers.py     # Error response format tests
```

### 2.2 Code Implementation

**tests/test_error_handlers.py:**
```python
"""
Error handler tests — Phase 2.
Verify standardized error response format across all error types.
"""
import pytest


class TestErrorResponseStructure:
    """
    All errors must return: {success: false, error: string, message: string}
    """
    
    def test_404_error_structure(self, client, admin_headers):
        """
        Non-existent endpoint returns standardized 404.
        
        Expected format:
        {
            "success": false,
            "error": "NotFound",
            "message": "..."
        }
        """
        response = client.get(
            "/api/v1/crm/students/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "success" in data
        assert "error" in data
        assert "message" in data
        assert data["success"] is False
    
    def test_401_error_structure(self, client):
        """
        Missing authentication returns standardized 401.
        """
        response = client.get("/api/v1/crm/students")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    def test_403_error_structure(self, client):
        """
        Forbidden access returns standardized 403.
        
        Note: With simplified 2-role system, this is rare but should still
        return standard format if triggered.
        """
        # Create a token with invalid role (would need implementation)
        # For now, verify structure if endpoint returns 403
        pass
    
    def test_422_validation_error_structure(self, client, admin_headers):
        """
        Pydantic validation errors return standardized 422.
        
        Expected: {success: false, error: "ValidationError", details: [...]}
        """
        response = client.post(
            "/api/v1/crm/students",
            headers=admin_headers,
            json={"full_name": "", "phone": "invalid"}  # Missing required fields
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestValidationErrors:
    """Tests for Pydantic validation error details."""
    
    def test_missing_required_field(self, client, admin_headers):
        """Creating student without required fields returns validation error."""
        response = client.post(
            "/api/v1/crm/students",
            headers=admin_headers,
            json={}  # Empty body
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "details" in data or "message" in data
    
    def test_invalid_email_format(self, client, admin_headers):
        """Invalid email format returns validation error."""
        response = client.post(
            "/api/v1/crm/parents",
            headers=admin_headers,
            json={
                "full_name": "Test Parent",
                "phone_primary": "+201000000001",
                "email": "not-an-email"
            }
        )
        
        assert response.status_code == 422
```

### 2.3 Phase 2 Success Criteria

- [ ] All error responses follow standard format
- [ ] 401, 403, 404, 422 errors properly tested
- [ ] Validation error details are helpful for debugging

### 2.4 Time Estimate

| Task | Hours |
|:---|:---:|
| test_error_handlers.py implementation | 3 |
| **Total** | **3 hours** |

---

## Phase 3: CRM Endpoints (5 SP)

**Goal:** Comprehensive tests for CRM domain (students, parents).

**Why Third:** Core business functionality, high API traffic.

### 3.1 Files to Create

```
tests/
├── test_crm.py                # CRM endpoint tests
└── factories.py               # Test data factories (optional)
```

### 3.2 Test Coverage Matrix

| Endpoint | Tests | Priority |
|:---|:---|:---:|
| `GET /crm/students` | Pagination, filtering, empty list | High |
| `GET /crm/students/{id}` | Success, 404 | High |
| `POST /crm/students` | Success, validation errors | High |
| `PUT /crm/students/{id}` | Success, 404, validation | Medium |
| `GET /crm/parents` | Pagination, search | High |
| `POST /crm/parents` | Success, duplicate phone handling | High |
| `GET /crm/parents/{id}` | Success, 404 | High |

### 3.3 Phase 3 Success Criteria

- [ ] All CRM GET endpoints tested (happy paths + 404s)
- [ ] All CRM POST endpoints tested (success + validation)
- [ ] Pagination verified (skip/limit works correctly)
- [ ] Coverage: >80% of CRM endpoints

### 3.4 Time Estimate

| Task | Hours |
|:---|:---:|
| test_crm.py setup | 1 |
| Students endpoints tests | 2 |
| Parents endpoints tests | 2 |
| Edge cases & cleanup | 1 |
| **Total** | **6 hours** |

---

## Phase 4: Enrollment Endpoints (4 SP)

**Goal:** Test enrollment workflows including transfers and drops.

**Why Fourth:** Complex business logic with side effects.

### 4.1 Files to Create

```
tests/
└── test_enrollments.py        # Enrollment endpoint tests
```

### 4.2 Test Coverage Matrix

| Endpoint | Tests | Priority |
|:---|:---|:---:|
| `POST /enrollments` | Successful enrollment, duplicate check | High |
| `GET /enrollments/student/{id}` | List student enrollments | High |
| `POST /enrollments/{id}/drop` | Drop enrollment, 404 | Medium |
| `POST /enrollments/transfer` | Transfer student, validation | Medium |

### 4.3 Phase 4 Success Criteria

- [ ] Enrollment creation flow tested
- [ ] Transfer flow tested
- [ ] Drop/withdrawal tested
- [ ] Coverage: >80% of enrollment endpoints

### 4.4 Time Estimate

| Task | Hours |
|:---|:---:|
| test_enrollments.py setup | 1 |
| Enrollment CRUD tests | 2 |
| Transfer workflow tests | 2 |
| **Total** | **5 hours** |

---

## Phase 5: Finance Endpoints (4 SP)

**Goal:** Test financial operations including receipts and refunds.

**Why Fifth:** Money handling — highest risk, but depends on CRM/Enrollment.

### 5.1 Files to Create

```
tests/
└── test_finance.py            # Finance endpoint tests
```

### 5.2 Test Coverage Matrix

| Endpoint | Tests | Priority |
|:---|:---|:---:|
| `POST /finance/receipts` | Create receipt, overpayment warning | High |
| `GET /finance/receipts` | Search, pagination | High |
| `GET /finance/receipts/{id}` | Detail view, 404 | High |
| `POST /finance/refunds` | Issue refund, validation | Medium |
| `GET /finance/summary` | Financial summary data | Low |

### 5.3 Phase 5 Success Criteria

- [x] Receipt creation tested (single + multiple line items)
- [x] Receipt search/filter tested
- [x] Refund flow tested
- [x] Coverage: 100% of finance endpoints (8/8)

### 5.4 Time Estimate

| Task | Hours |
|:---|:---:|
| test_finance.py setup | 1 |
| Receipt tests | 2 |
| Refund tests | 2 |
| **Total** | **5 hours** |

---

## Phase 6: Attendance Endpoints (2 SP)

**Goal:** Test attendance marking and session roster retrieval.

**Why Sixth:** Core daily operations, simple endpoints.

### 6.1 Files to Create

```
tests/
└── test_attendance.py         # Attendance endpoint tests
```

### 6.2 Test Coverage Matrix

| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/attendance/session/{id}` | Get roster, 404 | High |
| POST | `/attendance/session/{id}/mark` | Mark attendance, validation, bulk | High |

### 6.3 Phase 6 Success Criteria

- [ ] Attendance roster retrieval tested
- [ ] Bulk attendance marking tested
- [ ] Coverage: 100% of attendance endpoints (2/2)

---

## Phase 7: Academics Endpoints (6 SP)

**Goal:** Test course, group, and session management.

**Why Seventh:** Complex academic operations, many endpoints.

### 7.1 Files to Create

```
tests/
└── test_academics.py          # Academics endpoint tests
```

### 7.2 Test Coverage Matrix

**Courses (3 endpoints):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/academics/courses` | List, pagination | High |
| POST | `/academics/courses` | Create (admin only) | High |
| PATCH | `/academics/courses/{id}` | Update (admin only), 404 | Medium |

**Groups (6 endpoints):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/academics/groups` | List, pagination | High |
| GET | `/academics/groups/{id}` | Get by ID, 404 | High |
| POST | `/academics/groups` | Create/schedule (admin only) | High |
| PATCH | `/academics/groups/{id}` | Update (admin only), 404 | Medium |
| GET | `/academics/groups/{id}/sessions` | List sessions, filter by level | High |
| POST | `/academics/groups/{id}/progress-level` | Progress to next level | Medium |

**Sessions (5 endpoints):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/academics/sessions/daily-schedule` | Get by date | High |
| POST | `/academics/groups/{id}/sessions` | Add extra session | Medium |
| GET | `/academics/sessions/{id}` | Get by ID, 404 | High |
| PATCH | `/academics/sessions/{id}` | Update, 404 | Medium |
| DELETE | `/academics/sessions/{id}` | Delete, 404 | Medium |
| POST | `/academics/sessions/{id}/cancel` | Cancel and reschedule | Medium |
| POST | `/academics/sessions/{id}/substitute` | Mark substitute instructor | Low |

### 7.3 Phase 7 Success Criteria

- [ ] All course endpoints tested
- [ ] All group endpoints tested
- [ ] All session endpoints tested
- [ ] Coverage: >80% of academics endpoints (11+/14)

---

## Phase 8: Competitions Endpoints (4 SP)

**Goal:** Test competition and team registration management.

**Why Eighth:** Specialized module, lower traffic.

### 8.1 Files to Create

```
tests/
└── test_competitions.py       # Competitions endpoint tests
```

### 8.2 Test Coverage Matrix

| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/competitions` | List all | Medium |
| POST | `/competitions` | Create (admin only) | Medium |
| GET | `/competitions/{id}` | Get by ID, 404 | Medium |
| GET | `/competitions/{id}/categories` | List categories | Medium |
| POST | `/competitions/{id}/categories` | Add category (admin only) | Medium |
| POST | `/competitions/register` | Register team | Medium |
| GET | `/competitions/{id}/categories/{id}/teams` | List teams with members | Low |
| POST | `/competitions/team-members/{id}/pay` | Mark fee paid (admin only) | Low |

### 8.3 Phase 8 Success Criteria

- [ ] Competition CRUD tested
- [ ] Team registration tested
- [ ] Coverage: >60% of competitions endpoints (5+/8)

---

## Phase 9: HR Endpoints (4 SP)

**Goal:** Test employee and staff account management.

**Why Ninth:** Admin-only functionality, lower priority.

### 9.1 Files to Create

```
tests/
└── test_hr.py                 # HR endpoint tests
```

### 9.2 Test Coverage Matrix

| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/hr/employees` | List all (admin only) | Medium |
| GET | `/hr/employees/{id}` | Get by ID, 404 (admin only) | Medium |
| POST | `/hr/employees` | Create, validation, 409 conflict (admin only) | Medium |
| PUT | `/hr/employees/{id}` | Update, 404 (admin only) | Medium |
| GET | `/hr/staff-accounts` | List with linked employee info (admin only) | Low |
| POST | `/hr/attendance/log` | Log attendance (stub) | Low |

### 9.3 Phase 9 Success Criteria

- [ ] Employee CRUD tested
- [ ] Staff accounts tested
- [ ] Coverage: >70% of HR endpoints (5+/7)

---

## Phase 10: Analytics Endpoints (5 SP)

**Goal:** Test dashboard and reporting endpoints.

**Why Tenth:** Read-only endpoints, lowest priority.

### 10.1 Files to Create

```
tests/
├── test_analytics_dashboard.py
├── test_analytics_academic.py
├── test_analytics_bi.py
└── test_analytics_financial.py
```

### 10.2 Test Coverage Matrix

**Dashboard (1 endpoint):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/analytics/dashboard/summary` | Active enrollments, today's sessions | High |

**Academic Analytics (3 endpoints):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/analytics/academics/unpaid-attendees` | Today's unpaid students | Medium |
| GET | `/analytics/academics/groups/{id}/roster` | Group roster by level | Medium |
| GET | `/analytics/academics/groups/{id}/heatmap` | Attendance matrix | Low |

**BI Analytics (7 endpoints):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/analytics/bi/enrollment-trend` | Daily new enrollments | Low |
| GET | `/analytics/bi/retention` | Retention rates by course | Low |
| GET | `/analytics/bi/instructor-performance` | Groups/students per instructor | Low |
| GET | `/analytics/bi/retention-funnel` | Level progression counts | Low |
| GET | `/analytics/bi/instructor-value` | Revenue vs attendance correlation | Low |
| GET | `/analytics/bi/schedule-utilization` | Slot utilization % | Low |
| GET | `/analytics/bi/flight-risk` | At-risk students | Low |

**Competition Analytics (1 endpoint):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/analytics/competitions/fee-summary` | Participation and fees | Low |

**Financial Analytics (4 endpoints):**
| Method | Endpoint | Tests | Priority |
|:---:|:---|:---|:---:|
| GET | `/analytics/finance/revenue-by-date` | Daily revenue totals | Medium |
| GET | `/analytics/finance/revenue-by-method` | Revenue by payment method | Medium |
| GET | `/analytics/finance/outstanding-by-group` | Balances grouped by group | Medium |
| GET | `/analytics/finance/top-debtors` | Highest outstanding balances | Medium |

### 10.3 Phase 10 Success Criteria

- [ ] Dashboard summary tested
- [ ] Key financial analytics tested
- [ ] Coverage: >40% of analytics endpoints (8+/19)

---

## Running the Tests

### Individual Phase
```bash
# Phase 1 only
pytest tests/test_auth.py -v

# Phase 2 only
pytest tests/test_error_handlers.py -v

# Phase 3 only
pytest tests/test_crm.py -v
```

### Full Suite
```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app.api --cov-report=html --cov-report=term

# Fail fast (stop on first failure)
pytest tests/ -x
```

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
- name: Run API Tests
  run: |
    pip install pytest pytest-cov
    pytest tests/ --cov=app.api --cov-fail-under=80
```

---

## Risk Assessment

| Risk | Mitigation |
|:---|:---|
| Tests depend on real Supabase | Mock JWT with test secret (HS256) |
| Database state leaks between tests | Transaction rollback in fixtures |
| Tests are slow | Session-scoped app, function-scoped client |
| Missing edge cases | Start with happy paths, add edge cases iteratively |
| CI environment differences | Use SQLite for CI or dedicated test DB |

---

## Success Metrics

| Metric | Current | Target |
|:---|:---:|:---:|
| **Overall test coverage** | 33% (27/83) | >80% |
| Auth endpoint coverage | 0% (0/6) | 100% |
| Error handler coverage | 0% | 100% |
| **CRM endpoint coverage** | 100% (9/9) ✅ | 100% |
| **Enrollment endpoint coverage** | 100% (4/4) ✅ | 100% |
| **Finance endpoint coverage** | 100% (8/8) ✅ | 100% |
| Attendance endpoint coverage | 0% (0/2) | 100% |
| Academics endpoint coverage | 0% (0/14) | >80% |
| Competitions endpoint coverage | 0% (0/8) | >60% |
| HR endpoint coverage | 0% (0/7) | >70% |
| Analytics endpoint coverage | 0% (0/19) | >40% |
| Test execution time | <2 minutes | <2 minutes |
| CI pipeline integration | ✅ | ✅ |

---

## Post-Implementation Checklist

- [ ] All tests pass in local environment
- [ ] All tests pass in CI pipeline
- [ ] Coverage report generated and reviewed
- [ ] Documentation updated with test examples
- [ ] Team trained on running/debugging tests
- [ ] Test data factories extended as needed

---

**Next Step:** Proceed with Phase 1 implementation (Infrastructure & Auth Testing)?
