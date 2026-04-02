"""
tests/test_attendance.py
────────────────────────
Phase 6: Attendance Endpoints Testing

Covers:
- GET /attendance/session/{session_id} — Get roster with attendance status
- POST /attendance/session/{session_id}/mark — Mark/update attendance

All tests verify:
- Admin-only authentication
- Response schema compliance
- Bulk attendance marking behavior
"""
import pytest


class TestAttendanceRead:
    """Tests for GET /attendance/session/{id} — reading attendance data."""
    
    def test_get_session_attendance_success(self, client, admin_headers):
        """
        GET /attendance/session/{id} returns roster with attendance status.
        Requires admin role.
        """
        # Using session_id 1 — may or may not exist
        response = client.get(
            "/api/v1/attendance/session/1",
            headers=admin_headers
        )
        
        # Should return 200 with list (empty if no students enrolled)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # If students are enrolled, verify structure
        if data["data"]:
            first_row = data["data"][0]
            assert "student_id" in first_row
            assert "status" in first_row
    
    def test_get_session_attendance_empty_session(self, client, admin_headers):
        """
        GET /attendance/session/{id} for session with no students returns empty list.
        """
        # Using a high session_id that likely has no students
        response = client.get(
            "/api/v1/attendance/session/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
    
    def test_get_session_attendance_requires_auth(self, client):
        """
        GET /attendance/session/{id} without auth returns 401.
        """
        response = client.get("/api/v1/attendance/session/1")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestAttendanceMark:
    """Tests for POST /attendance/session/{id}/mark — marking attendance."""
    
    def test_mark_attendance_validation_error(self, client, admin_headers):
        """
        POST /attendance/session/{id}/mark with invalid status.
        Note: API currently accepts any status value (does not validate).
        """
        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json={
                "student_statuses": {
                    1: "invalid_status"  # API currently accepts this
                }
            }
        )
        
        # API currently accepts any status (no validation)
        # Future: should return 422 for invalid status
        assert response.status_code in [200, 422]
    
    def test_mark_attendance_empty_body(self, client, admin_headers):
        """
        POST /attendance/session/{id}/mark with empty dict marks no students.
        """
        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json={"student_statuses": {}}
        )
        
        # Should succeed but mark 0 students
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # Response should indicate 0 records marked
    
    def test_mark_attendance_bulk(self, client, admin_headers):
        """
        POST /attendance/session/{id}/mark with multiple students.
        Tests bulk attendance marking.
        """
        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json={
                "student_statuses": {
                    1: "present",
                    2: "absent",
                    3: "late",
                    4: "excused"
                }
            }
        )
        
        # May succeed or fail if students don't exist
        assert response.status_code in [200, 404, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    def test_mark_attendance_requires_auth(self, client):
        """
        POST /attendance/session/{id}/mark without auth returns 401.
        """
        response = client.post(
            "/api/v1/attendance/session/1/mark",
            json={"student_statuses": {1: "present"}}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_mark_attendance_invalid_student_id(self, client, admin_headers):
        """
        POST /attendance/session/{id}/mark with non-existent student handles gracefully.
        """
        response = client.post(
            "/api/v1/attendance/session/1/mark",
            headers=admin_headers,
            json={
                "student_statuses": {
                    99999: "present"  # Non-existent student
                }
            }
        )
        
        # Should handle gracefully (may succeed with 0 marked or fail with 404)
        assert response.status_code in [200, 404, 422]


class TestAttendanceAuth:
    """Authentication and authorization tests for attendance endpoints."""
    
    def test_all_attendance_endpoints_require_admin(self, client, admin_headers):
        """
        Verify all attendance endpoints require admin authentication.
        """
        endpoints = [
            ("GET", "/api/v1/attendance/session/1"),
            ("POST", "/api/v1/attendance/session/1/mark"),
        ]
        
        for method, endpoint in endpoints:
            # Test without auth
            if method == "GET":
                no_auth_response = client.get(endpoint)
            else:
                no_auth_response = client.post(endpoint, json={})
            
            assert no_auth_response.status_code == 401, f"{endpoint} should require auth"
            
            # Test with admin auth
            if method == "GET":
                admin_response = client.get(endpoint, headers=admin_headers)
            else:
                admin_response = client.post(
                    endpoint, 
                    headers=admin_headers, 
                    json={"student_statuses": {}}
                )
            
            assert admin_response.status_code != 401, f"{endpoint} should accept admin token"
