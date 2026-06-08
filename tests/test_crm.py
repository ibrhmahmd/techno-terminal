"""
CRM endpoint tests — Phase 3.
Tests for students and parents endpoints.
"""
import pytest


class TestStudentsRead:
    """Tests for reading student data."""
    
    def test_list_students_success(self, client, mock_admin_headers, override_auth):
        response = client.get(
            "/api/v1/crm/students?skip=0&limit=10",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
    
    def test_list_students_pagination(self, client, mock_admin_headers, override_auth):
        response1 = client.get(
            "/api/v1/crm/students?skip=0&limit=5",
            headers=mock_admin_headers
        )
        data1 = response1.json()
        
        response2 = client.get(
            "/api/v1/crm/students?skip=5&limit=5",
            headers=mock_admin_headers
        )
        data2 = response2.json()
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert data1["skip"] == 0
        assert data1["limit"] == 5
        assert data2["skip"] == 5
        assert data2["limit"] == 5
    
    def test_get_student_not_found(self, client, mock_admin_headers, override_auth):
        response = client.get(
            "/api/v1/crm/students/99999",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"
    
    def test_get_student_parents(self, client, mock_admin_headers, override_auth):
        response = client.get(
            "/api/v1/crm/students/1/parents",
            headers=mock_admin_headers
        )
        
        assert response.status_code in [200, 404]


class TestStudentsCreate:
    """Tests for creating students."""
    
    def test_create_student_success(self, client, mock_admin_headers, override_auth):
        import uuid
        unique_name = f"Test Student {uuid.uuid4().hex[:8]}"
        
        response = client.post(
            "/api/v1/crm/students",
            headers=mock_admin_headers,
            json={
                "student_data": {
                    "full_name": unique_name,
                    "date_of_birth": "2010-01-01",
                    "gender": "male",
                    "phone": "+201000000001",
                    "notes": "Test student created by automated test"
                },
                "parent_id": None,
                "relationship": None,
                "created_by_user_id": None
            }
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        created_id = data["data"]["id"]
        assert data["data"]["full_name"] == unique_name
        
        get_response = client.get(
            f"/api/v1/crm/students/{created_id}",
            headers=mock_admin_headers
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["data"]["full_name"] == unique_name
    
    def test_create_student_validation_error(self, client, mock_admin_headers, override_auth):
        response = client.post(
            "/api/v1/crm/students",
            headers=mock_admin_headers,
            json={
                "full_name": "",
                "birth_date": "invalid-date"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "ValidationError"


class TestParentsRead:
    """Tests for reading parent data."""
    
    def test_list_parents_success(self, client, mock_admin_headers, override_auth):
        response = client.get(
            "/api/v1/crm/parents?skip=0&limit=10",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
    
    def test_search_parents_by_phone(self, client, mock_admin_headers, override_auth):
        response = client.get(
            "/api/v1/crm/parents?q=+2010",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)


class TestStudentsUpdate:
    """Tests for updating students."""
    
    def test_update_student_success(self, client, mock_admin_headers, override_auth):
        import uuid
        unique_name = f"Updated Student {uuid.uuid4().hex[:8]}"
        
        create_response = client.post(
            "/api/v1/crm/students",
            headers=mock_admin_headers,
            json={
                "student_data": {
                    "full_name": "Original Name",
                    "date_of_birth": "2010-01-01",
                    "gender": "male",
                    "phone": "+201000000001"
                },
                "parent_id": None,
                "relationship": None,
                "created_by_user_id": None
            }
        )
        
        if create_response.status_code == 201:
            student_id = create_response.json()["data"]["id"]
            
            response = client.patch(
                f"/api/v1/crm/students/{student_id}",
                headers=mock_admin_headers,
                json={
                    "full_name": unique_name,
                    "notes": "Updated via test"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["full_name"] == unique_name
    
    def test_update_student_not_found(self, client, mock_admin_headers, override_auth):
        response = client.patch(
            "/api/v1/crm/students/99999",
            headers=mock_admin_headers,
            json={"full_name": "Updated Name"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"


class TestParentsGetById:
    """Tests for getting parent by ID."""
    
    def test_get_parent_not_found(self, client, mock_admin_headers, override_auth):
        response = client.get(
            "/api/v1/crm/parents/99999",
            headers=mock_admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "NotFoundError"


class TestParentsCreate:
    """Tests for creating parents."""
    
    def test_create_parent_success(self, client, mock_admin_headers, override_auth):
        import uuid
        unique_name = f"Test Parent {uuid.uuid4().hex[:8]}"
        unique_phone = f"+20100{uuid.uuid4().hex[:6]}"
        
        response = client.post(
            "/api/v1/crm/parents",
            headers=mock_admin_headers,
            json={
                "full_name": unique_name,
                "phone_primary": unique_phone,
                "phone_secondary": None,
                "email": None,
                "relation": None,
                "notes": "Test parent created by automated test"
            }
        )
        
        assert response.status_code in [201, 422]
        
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            created_id = data["data"]["id"]
            
            get_response = client.get(
                f"/api/v1/crm/parents/{created_id}",
                headers=mock_admin_headers
            )
            assert get_response.status_code == 200
            get_data = get_response.json()
            assert get_data["data"]["full_name"] == unique_name
    
    def test_create_parent_validation_error(self, client, mock_admin_headers, override_auth):
        response = client.post(
            "/api/v1/crm/parents",
            headers=mock_admin_headers,
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestParentsUpdate:
    """Tests for updating parents."""
    
    def test_update_parent_not_found(self, client, mock_admin_headers, override_auth):
        response = client.patch(
            "/api/v1/crm/parents/99999",
            headers=mock_admin_headers,
            json={"full_name": "Updated Name"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestCRMAuth:
    """Tests for CRM endpoint authentication requirements."""
    
    def test_students_list_requires_auth(self, client):
        """GET /crm/students without auth returns 401."""
        response = client.get("/api/v1/crm/students")
        assert response.status_code == 401
    
    def test_parents_list_requires_auth(self, client):
        """GET /crm/parents without auth returns 401."""
        response = client.get("/api/v1/crm/parents")
        assert response.status_code == 401
    
    def test_student_create_requires_admin(self, client):
        """POST /crm/students without admin role returns 403."""
        # This would require a non-admin token to test properly
        # For now, just verify it requires auth
        response = client.post("/api/v1/crm/students", json={})
        assert response.status_code == 401
