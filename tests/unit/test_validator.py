"""
Unit tests for configuration validators
"""
import unittest
from src.config.validator import (
    validate_globals,
    validate_heat_template,
    validate_guacamole_template,
    validate_range_package,
)


class TestConfigValidator(unittest.TestCase):
    def test_validate_globals_valid(self):
        raw = """
globals:
  organization: testorg
  amount: 2
  debug: false
heat:
  cloud: openstack
  amount: 2
guacamole:
  cloud: guac
"""
        res = validate_globals(raw)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.info.get("organization"), "testorg")

    def test_validate_globals_invalid_syntax(self):
        raw = "globals: [invalid yaml"
        res = validate_globals(raw)
        self.assertFalse(res.is_valid)
        self.assertTrue(len(res.errors) > 0)

    def test_validate_heat_valid(self):
        raw = """
heat_template_version: 2018-03-02
resources:
  my_vm:
    type: OS::Nova::Server
    properties:
      name: vm1
"""
        res = validate_heat_template(raw)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.info.get("server_count"), 1)

    def test_validate_heat_no_resources(self):
        raw = """
heat_template_version: 2018-03-02
parameters:
  param1:
    type: string
"""
        res = validate_heat_template(raw)
        self.assertFalse(res.is_valid)
        self.assertIn("resources", res.errors[0])

    def test_validate_guac_valid(self):
        raw = """
groups:
  range:
    parent: ROOT
connectionTemplates:
  server1:
    parent: range
    protocol: rdp
users:
  user1:
    username: u1
"""
        res = validate_guacamole_template(raw)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.info.get("group_count"), 1)
        self.assertEqual(res.info.get("connection_count"), 1)
        self.assertEqual(res.info.get("user_count"), 1)

    def test_validate_guac_missing_parent_warning(self):
        raw = """
groups:
  subgroup:
    parent: nonexistent_parent
"""
        res = validate_guacamole_template(raw)
        self.assertTrue(len(res.warnings) > 0)


if __name__ == "__main__":
    unittest.main()

