"""
Unit tests for SwiftContainer object and Swift provisioning with private access and dry-run simulation.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.objects.swift import SwiftContainer
from src.provision.engine import ProvisionEngine


class TestSwiftContainer:
    def test_init_defaults_to_private(self):
        conn = MagicMock()
        conn.search_containers.return_value = []
        sc = SwiftContainer(conn, name="test-container", assets_dir=None)
        assert sc.name == "test-container"
        assert sc.access == "private"
        assert sc.assets_dir is None

    def test_create_sets_private_access_and_skips_none_assets(self):
        conn = MagicMock()
        conn.search_containers.return_value = []
        conn.object_store.create_container.return_value = {"name": "test-container"}
        conn.set_container_access.return_value = {"name": "test-container", "access": "private"}

        sc = SwiftContainer(conn, name="test-container", assets_dir=None, access="private")
        container = sc.create(delay=0)

        assert container is not None
        conn.object_store.create_container.assert_called_once_with(name="test-container")
        conn.set_container_access.assert_called_once_with(name="test-container", access="private")

    def test_create_with_missing_assets_dir_does_not_crash(self, tmp_path):
        conn = MagicMock()
        conn.search_containers.return_value = []
        conn.object_store.create_container.return_value = {"name": "test-container"}
        conn.set_container_access.return_value = {"name": "test-container", "access": "private"}

        non_existent_dir = str(tmp_path / "does_not_exist")
        sc = SwiftContainer(conn, name="test-container", assets_dir=non_existent_dir)
        container = sc.create(delay=0)

        assert container is not None
        conn.set_container_access.assert_called_once_with(name="test-container", access="private")

    def test_upload_objects_when_dir_exists(self, tmp_path):
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        test_file = assets_dir / "sample.sh"
        test_file.write_text("echo hello")

        conn = MagicMock()
        conn.search_containers.return_value = []
        conn.object_store.create_container.return_value = {"name": "test-container"}
        conn.set_container_access.return_value = {"name": "test-container", "access": "private"}

        sc = SwiftContainer(conn, name="test-container", assets_dir=str(assets_dir))
        container = sc.create(delay=0)

        assert container is not None
        conn.create_object.assert_called_once()

    def test_dry_run_simulation_with_swift(self):
        config = {
            "globals": {"organization": "pentest", "provision": True, "amount": 1, "debug": False},
            "swift": {"provision": True, "update": False, "cloud": "openstack", "container_name": "pentest", "access": "private"},
            "heat": {"provision": False},
            "guacamole": {"provision": False}
        }
        engine = ProvisionEngine(globals_config=config, dry_run=True, debug=False)
        res = engine.run(target="swift", action="create")
        assert res.success is True
        assert len(res.errors) == 0
