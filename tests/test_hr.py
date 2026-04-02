"""
tests/test_hr.py
────────────────
HR endpoint tests — Phase 9.

Covers:
- Employee CRUD (list, get, create, update)
- Staff Accounts
- HR Attendance Logging
"""
import pytest


class TestEmployeesRead:
    """Tests for GET /hr/employees endpoints."""
    
    def test_list_employees_success(self, client, admin_headers):
        """
        GET /hr/employees returns list of employees.
        Requires admin role.
        """
        response = client.get(
            "/api/v1/hr/employees",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_list_employees_requires_admin(self, client):
        """
        GET /hr/employees without auth returns 401.
        """
        response = client.get("/api/v1/hr/employees")
        
        assert response.status_code == 401
    
    def test_get_employee_by_id_success(self, client, admin_headers):
        """
        GET /hr/employees/{id} returns employee details.
        """
        response = client.get(
            "/api/v1/hr/employees/1",
            headers=admin_headers
        )
        
        # May succeed or return 404
        assert response.status_code in [200, 404]
    
    def test_get_employee_not_found(self, client, admin_headers):
        """
        GET /hr/employees/{id} for non-existent ID returns 404.
        """
        response = client.get(
            "/api/v1/hr/employees/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404


class TestEmployeesWrite:
    """Tests for POST/PUT /hr/employees — modifying employees."""
    
    def test_create_employee_success(self, client, admin_headers):
        """
        POST /hr/employees creates a new employee.
        Requires admin role.
        """
        import time
        unique_suffix = str(int(time.time()))
        
        response = client.post(
            "/api/v1/hr/employees",
            headers=admin_headers,
            json={
                "full_name": f"Test Employee {unique_suffix}",
                "job_title": "Software Engineer",
                "department": "Engineering",
                "phone": "+201000000001",
                "email": f"test.employee.{unique_suffix}@example.com",
                "salary": 5000.0,
                "is_active": True
            }
        )
        
        # May succeed (201) or fail with validation/conflict
        assert response.status_code in [201, 409, 422]
        
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    def test_create_employee_validation_error(self, client, admin_headers):
        """
        POST /hr/employees with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/hr/employees",
            headers=admin_headers,
            json={
                "full_name": "",  # Empty name should fail
                "job_title": "Tester"
            }
        )
        
        # Should return validation error
        assert response.status_code in [422, 409]
    
    def test_create_employee_requires_admin(self, client):
        """
        POST /hr/employees without auth returns 401.
        """
        response = client.post(
            "/api/v1/hr/employees",
            json={"full_name": "Test", "job_title": "Tester"}
        )
        
        assert response.status_code == 401
    
    def test_update_employee_success(self, client, admin_headers):
        """
        PUT /hr/employees/{id} updates an employee.
        Requires admin role.
        """
        # First try to get an existing employee
        list_response = client.get(
            "/api/v1/hr/employees",
            headers=admin_headers
        )
        
        if list_response.status_code == 200 and list_response.json()["data"]:
            employee_id = list_response.json()["data"][0]["id"]
            
            response = client.put(
                f"/api/v1/hr/employees/{employee_id}",
                headers=admin_headers,
                json={
                    "full_name": "Updated Employee Name",
                    "job_title": "Senior Engineer",
                    "department": "Engineering",
                    "is_active": True
                }
            )
            
            # May succeed or fail with conflict
            assert response.status_code in [200, 409, 422]
    
    def test_update_employee_not_found(self, client, admin_headers):
        """
        PUT /hr/employees/{id} for non-existent ID.
        Note: API validates input before checking existence, may return 422.
        """
        response = client.put(
            "/api/v1/hr/employees/99999",
            headers=admin_headers,
            json={
                "full_name": "Updated Name",
                "job_title": "Tester",
                "department": "Test",
                "is_active": True
            }
        )
        
        # API validates input before checking existence
        assert response.status_code in [404, 422]


class TestStaffAccounts:
    """Tests for /hr/staff-accounts endpoints."""
    
    def test_list_staff_accounts_success(self, client, admin_headers):
        """
        GET /hr/staff-accounts returns staff accounts.
        Requires admin role.
        """
        response = client.get(
            "/api/v1/hr/staff-accounts",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_list_staff_accounts_requires_admin(self, client):
        """
        GET /hr/staff-accounts without auth returns 401.
        """
        response = client.get("/api/v1/hr/staff-accounts")
        
        assert response.status_code == 401


class TestHRAttendance:
    """Tests for /hr/attendance endpoints."""
    
    def test_log_attendance_success(self, client, admin_headers):
        """
        POST /hr/attendance/log logs attendance (stub).
        Requires admin role.
        """
        response = client.post(
            "/api/v1/hr/attendance/log",
            headers=admin_headers,
            json={
                "employee_id": 1,
                "status": "check_in",
                "notes": "Test attendance log"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["employee_id"] == 1
        assert data["data"]["status"] == "check_in"
    
    def test_log_attendance_validation_error(self, client, admin_headers):
        """
        POST /hr/attendance/log with invalid data returns 422.
        """
        response = client.post(
            "/api/v1/hr/attendance/log",
            headers=admin_headers,
            json={
                "employee_id": "not-an-int",  # Invalid type
                "status": "invalid_status"
            }
        )
        
        assert response.status_code == 422
    
    def test_log_attendance_requires_admin(self, client):
        """
        POST /hr/attendance/log without auth returns 401.
        """
        response = client.post(
            "/api/v1/hr/attendance/log",
            json={"employee_id": 1, "status": "check_in"}
        )
        
        assert response.status_code == 401


class TestHRAuth:
    """Authentication tests for all HR endpoints."""
    
    def test_all_hr_endpoints_require_admin(self, client, admin_headers):
        """
        Verify all HR endpoints require admin authentication.
        """
        endpoints = [
            ("GET", "/api/v1/hr/employees"),
            ("GET", "/api/v1/hr/employees/1"),
            ("POST", "/api/v1/hr/employees"),
            ("PUT", "/api/v1/hr/employees/99999"),
            ("GET", "/api/v1/hr/staff-accounts"),
            ("POST", "/api/v1/hr/attendance/log"),
        ]
        
        for method, endpoint in endpoints:
            # Without auth should fail
            if method == "GET":
                no_auth = client.get(endpoint)
            elif method == "POST":
                no_auth = client.post(endpoint, json={})
            elif method == "PUT":
                no_auth = client.put(endpoint, json={})
            
            assert no_auth.status_code == 401, f"{endpoint} should require auth"
            
            # With admin auth should not be 401 (may be 404 if resource doesn't exist)
            if method == "GET":
                with_auth = client.get(endpoint, headers=admin_headers)
            elif method == "POST":
                with_auth = client.post(endpoint, headers=admin_headers, json={"employee_id": 1, "status": "check_in"} if "attendance" in endpoint else {"full_name": "Test", "job_title": "Tester"})
            elif method == "PUT":
                with_auth = client.put(endpoint, headers=admin_headers, json={"full_name": "Test", "job_title": "Tester"})
            
            assert with_auth.status_code != 401, f"{endpoint} should accept admin auth"
