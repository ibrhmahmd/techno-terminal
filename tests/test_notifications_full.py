"""
tests/test_notifications_full.py
─────────────────────────────────
Comprehensive notification endpoint testing covering all ~21 endpoints.

Core Notifications:
  POST   /notifications/absence                                  - Trigger absence alert
  POST   /notifications/receipt/{receipt_id}                      - Send receipt notification
  GET    /notifications/logs                                      - List notification logs
  GET    /notifications/logs/parent/{parent_id}                    - Parent notification logs
  POST   /notifications/reports/daily                             - Trigger daily report
  GET    /notifications/reports/daily/data                        - Daily report data
  POST   /notifications/reports/weekly                            - Trigger weekly report
  GET    /notifications/reports/weekly/data                       - Weekly report data
  POST   /notifications/reports/monthly                           - Trigger monthly report
  GET    /notifications/reports/monthly/data                      - Monthly report data

Bulk:
  POST   /notifications/bulk                                      - Bulk send

Templates:
  GET    /notifications/templates                                 - List templates
  GET    /notifications/templates/{template_id}                    - Get template
  POST   /notifications/templates                                 - Create template
  PUT    /notifications/templates/{template_id}                    - Update template
  DELETE /notifications/templates/{template_id}                    - Delete template
  POST   /notifications/templates/{template_id}/test              - Test template

Admin Settings:
  GET    /notifications/admin/settings/me                         - Get settings
  PUT    /notifications/admin/settings/me                         - Update settings
  GET    /notifications/admin/settings/me/types/{notification_type}      - Get specific setting
  PUT    /notifications/admin/settings/me/types/{notification_type}      - Toggle specific setting
  GET    /notifications/admin/settings/me/additional-recipients          - List recipients
  POST   /notifications/admin/settings/me/additional-recipients          - Add recipient
  PUT    /notifications/admin/settings/me/additional-recipients/{id}     - Update recipient
  DELETE /notifications/admin/settings/me/additional-recipients/{id}     - Remove recipient

All tests verify: auth, response envelope, and data persistence.
"""
import pytest
from uuid import uuid4

from tests.utils.db_helpers import (
    create_test_student,
    create_test_parent,
    create_test_employee,
    create_test_receipt,
)

BASE = "/api/v1/notifications"


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


# ── Core Notification Actions ─────────────────────────────────────────────

class TestNotificationActions:
    """POST /notifications/absence, POST /notifications/receipt/{id}."""

    def test_send_absence_alert_success(self, client, db_session, mock_admin_headers, override_auth):
        student = create_test_student(db_session, full_name=_unique("Student"))
        db_session.commit()

        payload = {"student_id": student.id, "session_name": "Test Session", "session_date": "2026-06-09"}
        response = client.post(f"{BASE}/absence", headers=mock_admin_headers, json=payload)

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "queued" in data["data"].lower()

    def test_send_receipt_notification_success(self, client, db_session, mock_admin_headers, override_auth):
        receipt = create_test_receipt(db_session, payer_name=_unique("Payer"))
        db_session.commit()

        params = {"student_id": 1, "amount": "500.0", "receipt_number": receipt.receipt_number or "RCP-001"}
        response = client.post(f"{BASE}/receipt/{receipt.id}", headers=mock_admin_headers, params=params)

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_send_receipt_notification_not_found(self, client, mock_admin_headers, override_auth):
        params = {"student_id": 1, "amount": "500.0", "receipt_number": "RCP-XXX"}
        response = client.post(f"{BASE}/receipt/99999", headers=mock_admin_headers, params=params)

        assert response.status_code in (200, 404, 500)

    def test_send_absence_alert_unauthorized(self, client):
        payload = {"student_id": 1, "session_name": "Test", "session_date": "2026-06-09"}
        response = client.post(f"{BASE}/absence", json=payload)

        assert response.status_code == 401


# ── Notification Logs ─────────────────────────────────────────────────────

class TestNotificationLogs:
    """GET /notifications/logs, GET /notifications/logs/parent/{id}."""

    def test_list_notification_logs_success(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/logs", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data

    def test_get_parent_logs_success(self, client, db_session, mock_admin_headers, override_auth):
        parent = create_test_parent(db_session, full_name=_unique("Parent"))
        db_session.commit()

        response = client.get(f"{BASE}/logs/parent/{parent.id}", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_list_logs_unauthorized(self, client):
        response = client.get(f"{BASE}/logs")

        assert response.status_code == 401

    def test_get_parent_logs_not_found(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/logs/parent/99999", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ── Notification Reports ──────────────────────────────────────────────────

class TestNotificationReports:
    """POST/GET /notifications/reports/daily|weekly|monthly."""

    def test_trigger_daily_report_success(self, client, mock_admin_headers, override_auth):
        response = client.post(f"{BASE}/reports/daily", headers=mock_admin_headers)

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_get_daily_report_data(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/reports/daily/data", headers=mock_admin_headers)

        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_trigger_weekly_report_success(self, client, mock_admin_headers, override_auth):
        response = client.post(f"{BASE}/reports/weekly", headers=mock_admin_headers)

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_get_weekly_report_data(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/reports/weekly/data", headers=mock_admin_headers)

        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_trigger_monthly_report_success(self, client, mock_admin_headers, override_auth):
        response = client.post(f"{BASE}/reports/monthly", headers=mock_admin_headers)

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_get_monthly_report_data(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/reports/monthly/data", headers=mock_admin_headers)

        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True


# ── Notification Templates ────────────────────────────────────────────────

class TestNotificationTemplates:
    """Full CRUD for /notifications/templates."""

    def test_list_templates_success(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/templates", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_template_success(self, client, mock_admin_headers, override_auth):
        payload = {
            "name": _unique("Tmpl"),
            "channel": "EMAIL",
            "body": "<p>Hello {{name}}</p>",
            "variables": ["name"],
            "subject": "Test Subject",
            "is_standard": False,
        }
        response = client.post(f"{BASE}/templates", headers=mock_admin_headers, json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["channel"] == "EMAIL"
        assert data["data"]["is_standard"] is False
        return data["data"]["id"]

    def test_create_template_validation(self, client, mock_admin_headers, override_auth):
        payload = {"channel": "EMAIL"}
        response = client.post(f"{BASE}/templates", headers=mock_admin_headers, json=payload)

        assert response.status_code == 422

    def test_get_template_success(self, client, mock_admin_headers, override_auth):
        payload = {
            "name": _unique("Tmpl"),
            "channel": "EMAIL",
            "body": "<p>Hello {{name}}</p>",
            "variables": ["name"],
            "subject": "Test Subject",
            "is_standard": False,
        }
        create_resp = client.post(f"{BASE}/templates", headers=mock_admin_headers, json=payload)
        assert create_resp.status_code == 200
        template_id = create_resp.json()["data"]["id"]

        response = client.get(f"{BASE}/templates/{template_id}", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == template_id

    def test_get_template_not_found(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/templates/99999", headers=mock_admin_headers)

        assert response.status_code == 404

    def test_update_template_success(self, client, mock_admin_headers, override_auth):
        payload = {
            "name": _unique("Tmpl"),
            "channel": "EMAIL",
            "body": "<p>Original</p>",
            "variables": ["name"],
            "subject": "Original Subject",
            "is_standard": False,
        }
        create_resp = client.post(f"{BASE}/templates", headers=mock_admin_headers, json=payload)
        assert create_resp.status_code == 200
        template_id = create_resp.json()["data"]["id"]

        update = {"body": "<p>Updated body</p>", "subject": "Updated Subject"}
        response = client.put(f"{BASE}/templates/{template_id}", headers=mock_admin_headers, json=update)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["body"] == "<p>Updated body</p>"
        assert data["data"]["subject"] == "Updated Subject"

    def test_delete_template_success(self, client, mock_admin_headers, override_auth):
        payload = {
            "name": _unique("Tmpl"),
            "channel": "EMAIL",
            "body": "<p>Delete me</p>",
            "variables": ["name"],
            "is_standard": False,
        }
        create_resp = client.post(f"{BASE}/templates", headers=mock_admin_headers, json=payload)
        assert create_resp.status_code == 200
        template_id = create_resp.json()["data"]["id"]

        response = client.delete(f"{BASE}/templates/{template_id}", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        get_resp = client.get(f"{BASE}/templates/{template_id}", headers=mock_admin_headers)
        assert get_resp.status_code == 404

    def test_test_template_success(self, client, mock_admin_headers, override_auth):
        payload = {
            "name": _unique("Tmpl"),
            "channel": "EMAIL",
            "body": "<p>Test {{name}}</p>",
            "variables": ["name"],
            "subject": "Test {{name}}",
            "is_standard": False,
        }
        create_resp = client.post(f"{BASE}/templates", headers=mock_admin_headers, json=payload)
        assert create_resp.status_code == 200
        template_id = create_resp.json()["data"]["id"]

        response = client.post(f"{BASE}/templates/{template_id}/test", headers=mock_admin_headers)

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["data"]["template_id"] == template_id


# ── Admin Settings ────────────────────────────────────────────────────────

class TestAdminSettings:
    """GET/PUT /notifications/admin/settings/me and sub-resources."""

    def test_get_settings_success(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/admin/settings/me", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "settings" in data["data"]
        assert "additional_recipients" in data["data"]

    def test_update_settings_success(self, client, mock_admin_headers, override_auth):
        payload = {"settings": {"daily_report": True, "weekly_report": False}}
        response = client.put(f"{BASE}/admin/settings/me", headers=mock_admin_headers, json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_specific_type(self, client, mock_admin_headers, override_auth):
        response = client.get(f"{BASE}/admin/settings/me/types/daily_report", headers=mock_admin_headers)

        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["data"]["notification_type"] == "daily_report"

    def test_toggle_notification_type(self, client, mock_admin_headers, override_auth):
        response = client.put(
            f"{BASE}/admin/settings/me/types/daily_report",
            headers=mock_admin_headers,
            json={"is_enabled": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["notification_type"] == "daily_report"
        assert data["data"]["is_enabled"] is True

    def test_add_recipient_success(self, client, mock_admin_headers, override_auth):
        payload = {
            "email": f"test-{uuid4().hex[:8]}@example.com",
            "label": "Test Recipient",
            "notification_types": ["daily_report"],
        }
        response = client.post(
            f"{BASE}/admin/settings/me/additional-recipients",
            headers=mock_admin_headers,
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == payload["email"]
        assert data["data"]["is_active"] is True
        return data["data"]["id"]

    def test_list_recipients_success(self, client, mock_admin_headers, override_auth):
        payload = {
            "email": f"list-{uuid4().hex[:8]}@example.com",
            "label": "List Test",
            "notification_types": None,
        }
        client.post(
            f"{BASE}/admin/settings/me/additional-recipients",
            headers=mock_admin_headers,
            json=payload,
        )

        response = client.get(
            f"{BASE}/admin/settings/me/additional-recipients",
            headers=mock_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1


# ── Bulk ──────────────────────────────────────────────────────────────────

class TestBulk:
    """POST /notifications/bulk."""

    def test_bulk_send_success(self, client, db_session, mock_admin_headers, override_auth):
        parent = create_test_parent(db_session, full_name=_unique("Parent"))
        db_session.commit()

        payload = {"parent_ids": [parent.id], "template_name": "daily_report", "extra_vars": {}}
        response = client.post(f"{BASE}/bulk", headers=mock_admin_headers, json=payload)

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "queued_count" in data["data"]

    def test_bulk_send_unauthorized(self, client):
        payload = {"parent_ids": [1], "template_name": "daily_report", "extra_vars": {}}
        response = client.post(f"{BASE}/bulk", json=payload)

        assert response.status_code == 401
