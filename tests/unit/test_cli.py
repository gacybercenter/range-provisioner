"""
Unit tests for Click CLI commands
"""
import unittest
from click.testing import CliRunner
from src.cli import cli


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_cli_version(self):
        result = self.runner.invoke(cli, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("range-provisioner", result.output)

    def test_cli_help(self):
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("provision", result.output)
        self.assertIn("validate", result.output)
        self.assertIn("inspect", result.output)
        self.assertIn("serve", result.output)

    def test_cli_validate(self):
        result = self.runner.invoke(cli, ["validate", "--config", "globals.yaml"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Validation Report", result.output)
        self.assertIn("Valid", result.output)

    def test_cli_inspect(self):
        result = self.runner.invoke(cli, ["inspect", "--config", "globals.yaml"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Cyber Range", result.output)

    def test_cli_provision_dry_run(self):
        result = self.runner.invoke(cli, ["provision", "--dry-run", "--config", "globals.yaml"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("DRY-RUN SIMULATION", result.output)
        self.assertIn("Provisioning finished successfully", result.output)

    def test_cli_schedule_commands(self):
        # 1. schedule list
        res_list = self.runner.invoke(cli, ["schedule", "list"])
        self.assertEqual(res_list.exit_code, 0)

        # 2. schedule create
        res_create = self.runner.invoke(cli, [
            "schedule", "create",
            "--name", "CLI Scheduled Exercise",
            "--target", "full",
            "--dry-run",
            "--build-at", "2030-01-01T10:00:00",
            "--delete-at", "2030-01-01T18:00:00"
        ])
        self.assertEqual(res_create.exit_code, 0)
        self.assertIn("Successfully created scheduled job #", res_create.output)

        # Extract Job ID
        import re
        m = re.search(r"#(\d+)", res_create.output)
        self.assertIsNotNone(m)
        job_id = m.group(1)

        # 3. schedule cancel
        res_cancel = self.runner.invoke(cli, ["schedule", "cancel", job_id, "--action", "both"])
        self.assertEqual(res_cancel.exit_code, 0)
        self.assertIn("cancelled", res_cancel.output)


if __name__ == "__main__":
    unittest.main()


