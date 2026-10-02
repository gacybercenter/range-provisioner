"""
Unit tests for FastAPI Web endpoints and REST API
"""
import unittest
from fastapi.testclient import TestClient

from src.web.app import app


class TestWebAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "range-provisioner")

    def test_dashboard_html_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Range Provisioner", response.text)
        self.assertIn("Cyber Range Orchestration Platform", response.text)

    def test_presets_endpoint(self):
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data.get("presets", [])) >= 2)

    def test_validate_api(self):
        payload = {
            "globals_yaml": open("globals.yaml", "r", encoding="utf-8").read(),
            "heat_yaml": open("templates/main.yaml", "r", encoding="utf-8").read(),
            "guac_yaml": open("templates/guac.yaml", "r", encoding="utf-8").read(),
        }
        response = self.client.post("/api/config/validate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("is_valid"))

    def test_inspect_api(self):
        payload = {
            "globals_yaml": open("globals.yaml", "r", encoding="utf-8").read(),
            "heat_yaml": open("templates/main.yaml", "r", encoding="utf-8").read(),
            "guac_yaml": open("templates/guac.yaml", "r", encoding="utf-8").read(),
        }
        response = self.client.post("/api/config/inspect", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("summary", data)
        self.assertEqual(data["summary"]["organization"], "automation")
        self.assertEqual(data["summary"]["group_count"], 1)
        self.assertEqual(data["summary"]["user_count"], 4)

    def test_generate_api(self):
        payload = {
            "organization": "testlab",
            "stack_count": 3,
            "users_per_system": 2,
            "protocol": "rdp",
            "port": 3389,
            "student_user": "tester",
            "student_pass": "TestPass123!",
            "enable_swift": False
        }
        response = self.client.post("/api/config/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("globals_yaml", data)
        self.assertIn("testlab", data["globals_yaml"])
        self.assertIn("guac_yaml", data)
        self.assertIn("heat_yaml", data)

    def test_dry_run_provision_api(self):
        payload = {
            "target": "guacamole",
            "action": "create",
            "dry_run": True,
            "globals_yaml": open("globals.yaml", "r", encoding="utf-8").read(),
            "guac_yaml": open("templates/guac.yaml", "r", encoding="utf-8").read(),
        }
        response = self.client.post("/api/provision/run", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("task_id", data)
        self.assertEqual(data["status"], "RUNNING")


if __name__ == "__main__":
    unittest.main()

