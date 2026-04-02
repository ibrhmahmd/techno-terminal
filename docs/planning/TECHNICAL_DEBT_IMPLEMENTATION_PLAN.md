# Technical Debt Implementation Plan

**Date:** 2026-04-02  
**Purpose:** Detailed implementation guide for Stream B & C backlog items  
**Priority Order:** API-safe sequence for frontend team coordination

---

## Executive Summary

This plan addresses the remaining technical debt items from `BACKLOG.md` in an order that **protects API stability** for the frontend team currently wiring to the API.

| Order | Item | SP | Risk Level | API Impact |
|:---:|:---|:---:|:---:|:---|
| 1 | **C4** — Role Guard Helpers | 3 | 🟢 None | Zero breaking changes |
| 2 | **C5** — Automated Test Suite | 21 | 🟢 None | Protects API contract |
| 3 | **B4** — PDF Export Enhancement | 2 | 🟢 None | Feature addition only |
| 4 | **C2** — HR/Finance SOLID Refactor | 21 | 🟡 Low | Backend internal only |
| 5 | **C3** — Facade Retirement | 8 | 🟠 Medium | UI imports affected |
| 6 | **C1** — Session Injection Refactor | 35 | 🔴 High | Transaction behavior changes |

**Total safe immediate work (C4 + C5 + B4):** 26 SP (~1 week)  
**Total deferred work (C2 + C3 + C1):** 64 SP (~3-4 weeks)

---

## Priority 1: C4 — Role Guard Helpers (3 SP)

### What It Will Work On
Create convenience dependency wrappers for common role-based access control patterns in FastAPI routers.

### The Problem
Currently, routers use verbose inline role checks:
```python
@router.get("/admin-only")
def admin_endpoint(user: User = Depends(require_role("admin"))):
    pass
```

This is repetitive and error-prone. Standard patterns like `require_admin`, `require_instructor` should be first-class dependencies.

### Recommended Solution
Add pre-configured guard functions to `dependencies.py` that wrap the existing `require_role` logic.

### Files & Directories
- `app/api/dependencies.py` — Add guard helper functions
- `app/api/routers/*.py` — Example refactors to demonstrate usage

### Code Changes

**app/api/dependencies.py:**
```python
# Add after existing require_role function

def require_admin():
    """
    Dependency factory for admin-only endpoints.
    Usage: user: User = Depends(require_admin())
    """
    return require_role("admin")


def require_instructor():
    """
    Dependency factory for instructor+ endpoints.
    Usage: user: User = Depends(require_instructor())
    """
    return require_any("admin", "instructor")


def require_finance():
    """
    Dependency factory for finance team endpoints.
    Usage: user: User = Depends(require_finance())
    """
    return require_any("admin", "finance")


def require_any(*roles: str):
    """
    Dependency factory allowing any of the specified roles.
    Usage: user: User = Depends(require_any("admin", "instructor"))
    """
    def role_checker():
        return require_role(roles)
    return role_checker
```

**Example refactor in app/api/routers/hr_router.py:**
```python
# BEFORE
from app.api.dependencies import require_role, get_hr_service

@router.get("/hr/employees/{id}")
def get_employee(
    id: int,
    user: User = Depends(require_role("admin")),  # Verbose
    hr = Depends(get_hr_service)
):
    pass

# AFTER
from app.api.dependencies import require_admin, get_hr_service

@router.get("/hr/employees/{id}")
def get_employee(
    id: int,
    user: User = Depends(require_admin()),  # Clean
    hr = Depends(get_hr_service)
):
    pass
```

### Verification
- [ ] All existing `require_role("admin")` calls can be replaced with `require_admin()`
- [ ] No changes to API responses or authentication behavior
- [ ] Swagger UI shows same authentication requirements

### Risk Assessment
| Factor | Assessment |
|:---|:---|
| Breaking Changes | None — Pure wrapper functions |
| Frontend Impact | None — Same authentication flow |
| Rollback | Immediate — Just revert imports |
| Bug Risk | Very low — Simple delegation |

---

## Priority 2: C5 — Automated Test Suite (21 SP)

### What It Will Work On
Build comprehensive pytest-based test suite for all API endpoints using FastAPI TestClient.

### The Problem
- No automated regression testing for API endpoints
- Frontend team has no contract validation
- Breaking changes discovered only after deployment
- Manual testing via Swagger is time-consuming

### Recommended Solution
Create `tests/` directory with:
1. Unit tests for auth endpoints
2. Integration tests for CRM, enrollments, finance happy paths
3. Error flow tests (401, 403, 404, 422)
4. Mock Supabase JWT for authentication
5. Database fixture management (create/drop test data)

### Files & Directories
```
tests/
├── conftest.py                 # Shared fixtures, TestClient, auth mocks
├── test_auth.py               # Authentication endpoints
├── test_crm.py                # CRM endpoints
├── test_enrollments.py        # Enrollment endpoints
├── test_finance.py            # Finance endpoints
├── test_error_handlers.py     # Error response format tests
└── utils/
    ├── jwt_mocks.py          # Supabase JWT mock generation
    └── db_helpers.py         # Test database setup/cleanup
```

### Code Changes

**tests/conftest.py:**
```python
"""
Test configuration and shared fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from tests.utils.jwt_mocks import generate_mock_supabase_token


@pytest.fixture(scope="module")
def client():
    """
    FastAPI TestClient instance.
    """
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """
    Generate auth headers with mock Supabase JWT.
    """
    token = generate_mock_supabase_token(
        user_id="test-user-123",
        role="admin",
        email="test@example.com"
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db_session():
    """
    Database session for test data setup.
    Uses transaction rollback for test isolation.
    """
    from app.db.connection import get_session
    session = get_session()
    yield session
    session.rollback()  # Clean up test data
```

**tests/utils/jwt_mocks.py:**
```python
"""
Mock Supabase JWT generation for tests.
Uses HS256 with a test secret (never use in production).
"""
import jwt
from datetime import datetime, timedelta

TEST_SECRET = "test-secret-for-local-testing-only"


def generate_mock_supabase_token(
    user_id: str,
    role: str,
    email: str,
    expires_in_hours: int = 1
) -> str:
    """
    Generate a mock Supabase-style JWT for testing.
    
    Mimics the structure of Supabase auth tokens:
    {
        "sub": "user-uuid",
        "role": "authenticated",
        "app_metadata": {"role": "admin"},
        "email": "user@example.com",
        "exp": 1234567890
    }
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": "authenticated",
        "app_metadata": {"role": role},
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=expires_in_hours)
    }
    
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def decode_mock_token(token: str) -> dict:
    """
    Decode a mock token for verification in tests.
    """
    return jwt.decode(token, TEST_SECRET, algorithms=["HS256"])
```

**tests/test_auth.py:**
```python
"""
Authentication endpoint tests.
"""
import pytest


def test_auth_me_success(client, auth_headers):
    """
    GET /api/v1/auth/me returns current user info.
    """
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "test@example.com"
    assert data["data"]["role"] == "admin"


def test_auth_me_no_token(client):
    """
    GET /api/v1/auth/me without token returns 401.
    """
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "Unauthorized"


def test_auth_me_invalid_token(client):
    """
    GET /api/v1/auth/me with malformed token returns 401.
    """
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401
```

**tests/test_crm.py:**
```python
"""
CRM endpoint tests.
"""
import pytest


def test_list_students_success(client, auth_headers, db_session):
    """
    GET /api/v1/crm/students returns paginated student list.
    """
    # Setup: Create test student
    # ... (using db_session to insert test data)
    
    response = client.get(
        "/api/v1/crm/students?skip=0&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]


def test_get_student_not_found(client, auth_headers):
    """
    GET /api/v1/crm/students/{id} for non-existent ID returns 404.
    """
    response = client.get(
        "/api/v1/crm/students/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "NotFound"


def test_create_student_validation_error(client, auth_headers):
    """
    POST /api/v1/crm/students with invalid data returns 422.
    """
    response = client.post(
        "/api/v1/crm/students",
        headers=auth_headers,
        json={"name": "", "phone": "invalid"}  # Missing required fields
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "ValidationError"
```

**tests/test_error_handlers.py:**
```python
"""
Verify standardized error response format across all error types.
"""
import pytest


def test_error_response_structure_standardized(client):
    """
    All errors return {success: false, error: string, message: string}.
    """
    # 404 error
    response = client.get("/api/v1/nonexistent")
    data = response.json()
    assert "success" in data
    assert "error" in data
    assert "message" in data
    assert data["success"] is False


def test_http_exception_handler(client, auth_headers):
    """
    HTTPException is converted to standard ErrorResponse envelope.
    """
    # This would test an endpoint that raises HTTPException
    # For example, hitting a protected endpoint without auth
    response = client.get("/api/v1/crm/students")
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "message" in data
```

### Verification
- [ ] `pytest tests/` runs all tests successfully
- [ ] Coverage report shows >80% for API layer
- [ ] Tests run in CI/CD pipeline
- [ ] Mock JWTs don't require real Supabase connection

### Risk Assessment
| Factor | Assessment |
|:---|:---|
| Breaking Changes | None — Test code only |
| Frontend Impact | Positive — Contract validation |
| Rollback | N/A — New files only |
| Bug Risk | None — Only finds existing bugs |

---

## Priority 3: B4 — PDF Export Enhancement (2 SP)

### What It Will Work On
Enhance PDF receipt generation with logo support, multi-signature blocks, and improved layout.

### The Problem
Current PDF receipts are basic. Business needs:
- Organization logo/branding
- Multiple signature blocks (issuer, receiver, approver)
- Better layout and formatting

### Recommended Solution
Extend existing PDF generation in finance module with configurable template options.

### Files & Directories
- `app/modules/finance/pdf_generator.py` — Enhance existing generator
- `app/api/routers/finance_router.py` — Add logo upload/config endpoints
- `app/core/config.py` — Add PDF template settings

### Code Changes

**app/core/config.py:**
```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ... existing settings ...
    
    # PDF Export Configuration
    PDF_LOGO_PATH: Optional[str] = None  # Path to logo image
    PDF_COMPANY_NAME: str = "Techno Terminal"
    PDF_COMPANY_ADDRESS: str = ""
    PDF_PRIMARY_SIGNATURE: str = "Financial Manager"
    PDF_SECONDARY_SIGNATURE: Optional[str] = None  # e.g., "Director"
    
    class Config:
        env_file = ".env"
```

**app/modules/finance/pdf_generator.py:**
```python
"""
Enhanced PDF receipt generator with branding and signatures.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from app.core.config import settings
from typing import Optional
import os


class PDFReceiptGenerator:
    """
    Generates branded PDF receipts with signature blocks.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
        )
    
    def generate_receipt(
        self,
        receipt_data: dict,
        output_path: str,
        include_logo: bool = True,
        include_signatures: bool = True
    ) -> str:
        """
        Generate a PDF receipt with optional branding and signatures.
        
        Args:
            receipt_data: Dictionary containing receipt details
            output_path: Where to save the PDF
            include_logo: Whether to include organization logo
            include_signatures: Whether to include signature blocks
            
        Returns:
            Path to generated PDF file
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Logo and header
        if include_logo and settings.PDF_LOGO_PATH:
            story.extend(self._build_header())
        
        # Receipt title
        story.append(Paragraph("Payment Receipt", self.title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt details table
        story.extend(self._build_receipt_table(receipt_data))
        story.append(Spacer(1, 0.3*inch))
        
        # Payment breakdown
        story.extend(self._build_payment_breakdown(receipt_data))
        story.append(Spacer(1, 0.5*inch))
        
        # Signature blocks
        if include_signatures:
            story.extend(self._build_signature_blocks())
        
        # Footer
        story.extend(self._build_footer())
        
        doc.build(story)
        return output_path
    
    def _build_header(self) -> list:
        """Build header with logo and company info."""
        elements = []
        
        # Logo
        if os.path.exists(settings.PDF_LOGO_PATH):
            img = Image(settings.PDF_LOGO_PATH, width=1.5*inch, height=0.75*inch)
            elements.append(img)
        
        # Company name and address
        elements.append(Paragraph(
            f"<b>{settings.PDF_COMPANY_NAME}</b>",
            self.styles['Heading2']
        ))
        if settings.PDF_COMPANY_ADDRESS:
            elements.append(Paragraph(
                settings.PDF_COMPANY_ADDRESS,
                self.styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _build_receipt_table(self, data: dict) -> list:
        """Build main receipt information table."""
        table_data = [
            ['Receipt #:', data.get('receipt_number', 'N/A')],
            ['Date:', data.get('paid_at', 'N/A')],
            ['Student:', data.get('student_name', 'N/A')],
            ['Parent:', data.get('parent_name', 'N/A')],
            ['Group:', data.get('group_name', 'N/A')],
            ['Received By:', data.get('received_by', 'N/A')],
        ]
        
        table = Table(table_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return [table]
    
    def _build_payment_breakdown(self, data: dict) -> list:
        """Build payment line items table."""
        elements = []
        elements.append(Paragraph("<b>Payment Details</b>", self.styles['Heading3']))
        
        table_data = [['Description', 'Amount']]
        
        for line in data.get('lines', []):
            table_data.append([
                line.get('description', ''),
                f"${line.get('amount', 0):,.2f}"
            ])
        
        # Totals
        table_data.append(['', ''])
        table_data.append(['Subtotal:', f"${data.get('subtotal', 0):,.2f}"])
        if data.get('discount', 0) > 0:
            table_data.append(['Discount:', f"-${data.get('discount', 0):,.2f}"])
        table_data.append(['Total:', f"${data.get('total', 0):,.2f}"])
        
        table = Table(table_data, colWidths=[4.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -2), 1, colors.grey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        
        return elements + [table]
    
    def _build_signature_blocks(self) -> list:
        """Build signature line blocks."""
        elements = []
        elements.append(Spacer(1, 0.5*inch))
        
        signatures = [
            settings.PDF_PRIMARY_SIGNATURE,
            settings.PDF_SECONDARY_SIGNATURE
        ]
        signatures = [s for s in signatures if s]  # Remove None
        
        if len(signatures) == 1:
            # Single centered signature
            elements.append(self._single_signature(signatures[0]))
        elif len(signatures) == 2:
            # Two side-by-side signatures
            elements.append(self._dual_signatures(signatures[0], signatures[1]))
        
        return elements
    
    def _single_signature(self, title: str) -> Table:
        """Create a single centered signature block."""
        sig_data = [
            ['_' * 40],
            [title],
        ]
        table = Table(sig_data, colWidths=[3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ]))
        return table
    
    def _dual_signatures(self, left_title: str, right_title: str) -> Table:
        """Create side-by-side signature blocks."""
        sig_data = [
            ['_' * 30, '_' * 30],
            [left_title, right_title],
        ]
        table = Table(sig_data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ]))
        return table
    
    def _build_footer(self) -> list:
        """Build receipt footer."""
        return [
            Spacer(1, 0.5*inch),
            Paragraph(
                "Thank you for your payment!",
                ParagraphStyle(
                    'Footer',
                    parent=self.styles['Normal'],
                    alignment=1,  # Center
                    textColor=colors.grey,
                )
            )
        ]
```

**app/api/routers/finance_router.py (add endpoint):**
```python
@router.post(
    "/finance/receipts/{receipt_id}/pdf",
    summary="Generate PDF receipt",
)
def generate_receipt_pdf(
    receipt_id: int,
    include_logo: bool = True,
    include_signatures: bool = True,
    user: User = Depends(require_admin()),
    finance = Depends(get_finance_service)
):
    """
    Generate a branded PDF receipt with optional logo and signatures.
    """
    from app.modules.finance.pdf_generator import PDFReceiptGenerator
    import tempfile
    import os
    
    # Get receipt data
    receipt = finance.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Generate PDF
    generator = PDFReceiptGenerator()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_path = generator.generate_receipt(
            receipt_data=receipt,
            output_path=tmp.name,
            include_logo=include_logo,
            include_signatures=include_signatures
        )
    
    # Return file (in production, might upload to S3 and return URL)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"receipt_{receipt['receipt_number']}.pdf"
    )
```

### Verification
- [ ] PDF generates with logo when `PDF_LOGO_PATH` is set
- [ ] Signature blocks appear as configured
- [ ] Layout is professional and printable
- [ ] Generated PDFs are under 500KB

### Risk Assessment
| Factor | Assessment |
|:---|:---|
| Breaking Changes | None — New endpoint only |
| Frontend Impact | None — File download endpoint |
| Rollback | Easy — Feature flag via env vars |
| Bug Risk | Low — Isolated to PDF generation |

---

## Priority 4: C2 — HR + Finance SOLID Refactor (21 SP)

### What It Will Work On
Split monolithic `hr/hr_service.py` and `finance/finance_service.py` into proper layered architecture with `models/`, `repositories/`, `services/` subdirectories.

### The Problem
Both modules are flat single files violating SOLID principles:
- `app/modules/hr/hr_service.py` (~215 lines) — Mixes concerns
- `app/modules/finance/finance_service.py` (~300+ lines) — Too many responsibilities

This makes testing, maintenance, and team collaboration difficult.

### Recommended Solution
Apply `module_refactoring_guide.md` SOP:
1. Extract models to `models.py` (or keep in `hr/models.py`)
2. Create `repositories/` with data access layer
3. Create `services/` with business logic layer
4. Update imports in `__init__.py` for backward compatibility

### Files & Directories

**HR Module:**
```
app/modules/hr/
├── __init__.py           # Re-export for backward compatibility
├── models.py             # SQLModel definitions (existing)
├── repositories/
│   ├── __init__.py
│   ├── employee_repository.py
│   └── staff_account_repository.py
├── services/
│   ├── __init__.py
│   ├── employee_service.py
│   └── staff_account_service.py
└── hr_service.py         # DEPRECATED — keep for migration period
```

**Finance Module:**
```
app/modules/finance/
├── __init__.py           # Re-export for backward compatibility
├── models.py             # SQLModel definitions (existing)
├── repositories/
│   ├── __init__.py
│   ├── receipt_repository.py
│   ├── payment_repository.py
│   └── balance_repository.py
├── services/
│   ├── __init__.py
│   ├── receipt_service.py
│   ├── payment_service.py
│   └── balance_service.py
├── schemas/
│   ├── __init__.py
│   └── finance_schemas.py  # Move from api/schemas/finance/
├── pdf_generator.py      # (from B4)
└── finance_service.py    # DEPRECATED — keep for migration period
```

### Code Changes

**app/modules/hr/repositories/employee_repository.py:**
```python
"""
Employee data access layer.
"""
from typing import Optional, List
from sqlmodel import Session, select
from app.modules.hr.models import Employee


class EmployeeRepository:
    """
    Repository for Employee CRUD operations.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        """Get employee by ID."""
        return self.session.get(Employee, employee_id)
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[Employee]:
        """List all employees with pagination."""
        statement = select(Employee).offset(skip).limit(limit)
        return self.session.exec(statement).all()
    
    def create(self, employee: Employee) -> Employee:
        """Create new employee."""
        self.session.add(employee)
        self.session.commit()
        self.session.refresh(employee)
        return employee
    
    def update(self, employee: Employee) -> Employee:
        """Update existing employee."""
        self.session.add(employee)
        self.session.commit()
        self.session.refresh(employee)
        return employee
    
    def delete(self, employee_id: int) -> bool:
        """Delete employee by ID."""
        employee = self.get_by_id(employee_id)
        if employee:
            self.session.delete(employee)
            self.session.commit()
            return True
        return False
```

**app/modules/hr/services/employee_service.py:**
```python
"""
Employee business logic layer.
"""
from typing import Optional, List
from app.modules.hr.models import Employee
from app.modules.hr.repositories.employee_repository import EmployeeRepository
from app.shared.exceptions import NotFoundError, ConflictError


class EmployeeService:
    """
    Service for employee management operations.
    """
    
    def __init__(self, repository: EmployeeRepository):
        self.repository = repository
    
    def get_employee(self, employee_id: int) -> Optional[Employee]:
        """
        Get employee by ID.
        
        Raises:
            NotFoundError: If employee doesn't exist
        """
        employee = self.repository.get_by_id(employee_id)
        if not employee:
            raise NotFoundError(f"Employee {employee_id} not found")
        return employee
    
    def list_employees(self, skip: int = 0, limit: int = 100) -> List[Employee]:
        """List all employees."""
        return self.repository.list_all(skip=skip, limit=limit)
    
    def create_employee(self, employee_data: dict) -> Employee:
        """
        Create new employee.
        
        Raises:
            ConflictError: If national_id already exists
        """
        # Business logic: Check for duplicate national_id
        existing = self._find_by_national_id(employee_data.get("national_id"))
        if existing:
            raise ConflictError("Employee with this national ID already exists")
        
        employee = Employee(**employee_data)
        return self.repository.create(employee)
    
    def update_employee(self, employee_id: int, updates: dict) -> Employee:
        """Update employee fields."""
        employee = self.get_employee(employee_id)
        
        for field, value in updates.items():
            if hasattr(employee, field):
                setattr(employee, field, value)
        
        return self.repository.update(employee)
    
    def _find_by_national_id(self, national_id: str) -> Optional[Employee]:
        """Internal helper to find by national ID."""
        # Implementation would query repository with filter
        pass
```

**app/modules/hr/__init__.py (backward compatibility):**
```python
"""
HR Module — SOLID Refactored

Deprecated: Importing from hr.hr_service is deprecated.
Use: from hr.services.employee_service import EmployeeService
"""
import warnings

# New clean imports
from app.modules.hr.models import Employee
from app.modules.hr.services.employee_service import EmployeeService
from app.modules.hr.services.staff_account_service import StaffAccountService
from app.modules.hr.repositories.employee_repository import EmployeeRepository
from app.modules.hr.repositories.staff_account_repository import StaffAccountRepository

# Backward compatibility — warn on old imports
warnings.warn(
    "Importing from hr.hr_service is deprecated. "
    "Use hr.services.employee_service instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export old names for compatibility during migration
from app.modules.hr.hr_service import (
    list_all_employees,
    get_employee_by_id,
    create_employee_only,
    # ... other old functions
)
```

### Verification
- [ ] All existing imports continue to work (with deprecation warnings)
- [ ] New layered imports work correctly
- [ ] Tests pass with new structure
- [ ] No functionality changes

### Risk Assessment
| Factor | Assessment |
|:---|:---|
| Breaking Changes | Low — Backward compatibility layer |
| Frontend Impact | None — Internal restructure only |
| Rollback | Medium — Can revert to old imports if issues |
| Bug Risk | Low — File moves, logic unchanged |

---

## Priority 5: C3 — Facade `__init__.py` Retirement (8 SP)

### What It Will Work On
Remove singleton re-exports from `crm/__init__.py` and `academics/__init__.py`. Update all UI and router code to import directly from service classes.

### The Problem
Current pattern:
```python
# app/modules/crm/__init__.py
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.services.parent_service import ParentService

student_service = StudentService()
parent_service = ParentService()
```

This creates:
- Singleton instances at import time
- Tight coupling to specific service lifecycle
- Difficulty testing with mocks
- Hidden dependencies

### Recommended Solution
1. Remove singleton exports from `__init__.py`
2. Update all imports in UI and routers
3. Use dependency injection everywhere

### Files & Directories
- `app/modules/crm/__init__.py` — Remove singleton re-exports
- `app/modules/academics/__init__.py` — Remove singleton re-exports
- `app/ui/pages/*.py` — Update all UI imports
- `app/ui/components/*.py` — Update component imports
- `app/api/routers/*.py` — Already using DI (mostly safe)

### Code Changes

**app/modules/crm/__init__.py (AFTER):**
```python
"""
CRM Module

Usage:
    from app.modules.crm.models import Student, Parent
    from app.modules.crm.services.student_service import StudentService
    from app.modules.crm.services.parent_service import ParentService
"""

# Only export models and classes — no singleton instances
from app.modules.crm.models import Student, Parent

# Services must be instantiated by caller or DI
# Do NOT create singletons here
```

**app/ui/pages/01_Students.py (example migration):**
```python
# BEFORE
from app.modules.crm import student_service

students = student_service.list_students()

# AFTER
from app.modules.crm.services.student_service import StudentService
from app.db.connection import get_session

with get_session() as session:
    service = StudentService(session)
    students = service.list_students()
```

**app/ui/state.py (helper for UI):**
```python
"""
UI state helpers with proper service lifecycle.
"""
from contextlib import contextmanager
from app.db.connection import get_session


@contextmanager
def get_crm_service(service_class):
    """
    Context manager for CRM services with automatic session handling.
    
    Usage:
        with get_crm_service(StudentService) as service:
            students = service.list_students()
    """
    with get_session() as session:
        yield service_class(session)


# Convenience helpers for common services
def get_student_service():
    """Get StudentService with session."""
    from app.modules.crm.services.student_service import StudentService
    return get_crm_service(StudentService)


def get_parent_service():
    """Get ParentService with session."""
    from app.modules.crm.services.parent_service import ParentService
    return get_crm_service(ParentService)
```

### Migration Script

**scripts/migrate_facade_imports.py:**
```python
"""
Script to help migrate from facade imports to direct imports.
Run this to find all files that need updating.
"""
import os
import re
from pathlib import Path


def find_facade_imports(directory: str):
    """
    Find all Python files importing from crm or academics facades.
    """
    facade_pattern = re.compile(
        r'from\s+app\.modules\.(crm|academics)\s+import\s+(.+)',
        re.MULTILINE
    )
    
    results = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                matches = facade_pattern.findall(content)
                if matches:
                    results.append({
                        'file': filepath,
                        'imports': matches
                    })
    
    return results


def main():
    # Find all UI files with facade imports
    ui_results = find_facade_imports('app/ui')
    
    print(f"Found {len(ui_results)} files with facade imports:")
    for result in ui_results:
        print(f"\n  {result['file']}")
        for module, imports in result['imports']:
            print(f"    from app.modules.{module} import {imports}")


if __name__ == "__main__":
    main()
```

### Verification
- [ ] No imports from `crm` or `academics` facades remain
- [ ] All UI pages work correctly
- [ ] No singleton instances created at module load
- [ ] Tests updated and passing

### Risk Assessment
| Factor | Assessment |
|:---|:---|
| Breaking Changes | **HIGH** — All UI imports change |
| Frontend Impact | **YES** — UI team must update all imports |
| Rollback | Difficult — Requires reverting many files |
| Bug Risk | Medium — Import errors, missing service instances |

### Coordination Required
- [ ] Notify UI team of import changes
- [ ] Schedule joint refactoring session
- [ ] Update UI coding standards documentation
- [ ] Provide migration script and examples

---

## Priority 6: C1 — Session Injection Refactor (35 SP)

### What It Will Work On
Add `db: Session` parameter to all service methods across 7 modules for atomic multi-service transactions.

### The Problem
Current pattern:
```python
# Router
def enroll_student(data):
    with get_session() as session:
        enrollment_service.enroll(data)  # Creates own session
        finance_service.create_receipt(data)  # Creates own session
        # Not atomic! First could succeed, second fail
```

Need ability to share session across services for atomic operations.

### Recommended Solution
1. Add `session: Session` as first parameter to all service methods
2. Create `UnitOfWork` pattern for complex transactions
3. Update all routers to pass session from `Depends(get_db)`

### Files & Directories
**All 7 modules affected:**
- `app/modules/academics/services/*.py` — 3 services
- `app/modules/crm/services/*.py` — 2 services
- `app/modules/enrollments/*.py` — 1 service
- `app/modules/finance/services/*.py` — 1 service
- `app/modules/hr/services/*.py` — 1 service
- `app/modules/competitions/services/*.py` — 2 services
- `app/modules/attendance/*.py` — 1 service

Plus all routers:
- `app/api/routers/*.py` — All endpoints

### Code Changes

**app/modules/crm/services/student_service.py (AFTER):**
```python
"""
Student service with session injection.
"""
from sqlmodel import Session
from typing import Optional, List
from app.modules.crm.models import Student
from app.modules.crm.repositories.student_repository import StudentRepository


class StudentService:
    """
    Student management service.
    
    All methods accept session for transaction control.
    """
    
    def __init__(self, repository: StudentRepository):
        self.repository = repository
    
    def list_students(
        self,
        session: Session,  # NEW: Injected session
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Student]:
        """List students with pagination."""
        return self.repository.list_all(
            session=session,  # Pass to repository
            skip=skip,
            limit=limit,
            search=search
        )
    
    def get_student(
        self,
        session: Session,  # NEW: Injected session
        student_id: int
    ) -> Optional[Student]:
        """Get student by ID."""
        return self.repository.get_by_id(session, student_id)
    
    def create_student(
        self,
        session: Session,  # NEW: Injected session
        student_data: dict
    ) -> Student:
        """Create new student."""
        student = Student(**student_data)
        return self.repository.create(session, student)
```

**app/modules/crm/repositories/student_repository.py (AFTER):**
```python
"""
Student repository with session injection.
"""
from sqlmodel import Session, select
from typing import Optional, List
from app.modules.crm.models import Student


class StudentRepository:
    """
    Student data access with session parameter.
    """
    
    def get_by_id(
        self,
        session: Session,  # NEW: Injected session
        student_id: int
    ) -> Optional[Student]:
        """Get student by ID."""
        return session.get(Student, student_id)
    
    def list_all(
        self,
        session: Session,  # NEW: Injected session
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Student]:
        """List all students."""
        query = select(Student)
        
        if search:
            query = query.where(
                (Student.name.contains(search)) |
                (Student.phone.contains(search))
            )
        
        query = query.offset(skip).limit(limit)
        return session.exec(query).all()
    
    def create(
        self,
        session: Session,  # NEW: Injected session
        student: Student
    ) -> Student:
        """Create student."""
        session.add(student)
        session.flush()  # Get ID without committing
        return student
```

**app/api/routers/crm/students.py (AFTER):**
```python
"""
CRM students router with session injection.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.api.dependencies import require_admin, get_db
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.repositories.student_repository import StudentRepository

router = APIRouter()


def get_student_service_dep(session: Session = Depends(get_db)):
    """
    Factory to create StudentService with session.
    """
    repository = StudentRepository()
    return StudentService(repository)


@router.get("/crm/students")
def list_students(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    user = Depends(require_admin()),
    service: StudentService = Depends(get_student_service_dep),
    session: Session = Depends(get_db)  # Injected session
):
    """List students."""
    students = service.list_students(
        session=session,  # Pass session to service
        skip=skip,
        limit=limit,
        search=search
    )
    return {"items": students}
```

**Unit of Work Pattern (for complex transactions):**

**app/shared/unit_of_work.py:**
```python
"""
Unit of Work pattern for atomic multi-service operations.
"""
from contextlib import contextmanager
from sqlmodel import Session
from app.db.connection import get_session
from app.modules.crm.repositories.student_repository import StudentRepository
from app.modules.finance.repositories.receipt_repository import ReceiptRepository


class EnrollmentUnitOfWork:
    """
    Coordinates enrollment + receipt creation atomically.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.student_repo = StudentRepository()
        self.receipt_repo = ReceiptRepository()
        self.committed = False
    
    def enroll_and_pay(
        self,
        student_data: dict,
        payment_data: dict
    ) -> tuple:
        """
        Enroll student and create receipt in one transaction.
        
        Both succeed or both fail (atomic).
        """
        try:
            # Create enrollment
            enrollment = self._create_enrollment(student_data)
            
            # Create receipt
            receipt = self._create_receipt(payment_data)
            
            # Only commit if both succeed
            self.session.commit()
            self.committed = True
            
            return enrollment, receipt
            
        except Exception:
            self.session.rollback()
            raise
    
    def _create_enrollment(self, data: dict):
        """Internal: Create enrollment."""
        # Implementation
        pass
    
    def _create_receipt(self, data: dict):
        """Internal: Create receipt."""
        # Implementation
        pass


@contextmanager
def enrollment_uow():
    """
    Context manager for enrollment unit of work.
    
    Usage:
        with enrollment_uow() as uow:
            enrollment, receipt = uow.enroll_and_pay(student, payment)
    """
    with get_session() as session:
        uow = EnrollmentUnitOfWork(session)
        try:
            yield uow
            if not uow.committed:
                uow.session.rollback()
        except Exception:
            uow.session.rollback()
            raise
```

### Migration Strategy

**Phase 1 — Add Optional Session (Backward Compatible):**
```python
def list_students(
    self,
    session: Optional[Session] = None  # Optional for migration
):
    if session is None:
        with get_session() as session:
            return self._list_students(session)
    return self._list_students(session)
```

**Phase 2 — Update Routers:**
Change routers to pass session from `Depends(get_db)`

**Phase 3 — Make Required:**
Remove default `None` and old session creation logic

### Verification
- [ ] All service methods accept `session` parameter
- [ ] All repositories accept `session` parameter
- [ ] Routers pass session from `Depends(get_db)`
- [ ] Multi-service operations are atomic
- [ ] No session leaks or connection pool exhaustion

### Risk Assessment
| Factor | Assessment |
|:---|:---|
| Breaking Changes | **HIGH** — Every service method signature changes |
| Frontend Impact | **POTENTIAL** — Session bugs could cause data issues |
| Rollback | **DIFFICULT** — Core architecture change |
| Bug Risk | **HIGH** — Transaction boundaries, session lifecycle |

### Prerequisites Before Starting C1
1. ✅ C5 Test Suite complete (catch regressions)
2. ✅ C2 SOLID Refactor complete (clean service boundaries)
3. ✅ Comprehensive integration tests for multi-service operations
4. ✅ Staging environment for testing
5. ✅ Rollback plan if issues in production

---

## Summary Timeline

| Phase | Items | SP | Duration | Dependencies |
|:---:|:---|:---:|:---:|:---|
| **1** | C4 Role Guards + B4 PDF | 5 | 2-3 days | None |
| **2** | C5 Test Suite | 21 | 1 week | Phase 1 |
| **3** | C2 SOLID Refactor | 21 | 1 week | Phase 2 |
| **4** | C3 Facade Retirement | 8 | 2-3 days | Phase 3 + UI team ready |
| **5** | C1 Session Injection | 35 | 2 weeks | Phase 2 + Phase 3 + full test coverage |

**Minimum safe work for frontend team (Phases 1-2):** 26 SP (~1.5 weeks)  
**Full technical debt resolution:** 90 SP (~5-6 weeks)

**Recommendation:** Complete Phases 1-2 immediately, then reassess with frontend team progress.
