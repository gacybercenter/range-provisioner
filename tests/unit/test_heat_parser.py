"""
Unit tests for Heat HOT Template Parser, Dependency Loop Detection,
and D3 Cyber Range Topology Generator.
"""
import pytest
from fastapi.testclient import TestClient
from src.web.app import app
from src.config.heat_parser import (
    HeatTemplateParser,
    build_range_topology,
    HeatValidationResult,
)


@pytest.fixture
def client():
    return TestClient(app)


SAMPLE_VALID_HOT = """
heat_template_version: 2018-03-02
description: Valid Test Range HOT Template

parameters:
  student_user:
    type: string
    default: student
  student_pass:
    type: string
    default: P@ss123!

resources:
  range_net:
    type: OS::Neutron::Net
    properties:
      name: range_network

  range_subnet:
    type: OS::Neutron::Subnet
    properties:
      network_id: { get_resource: range_net }
      cidr: 10.20.0.0/24

  db_server:
    type: OS::Nova::Server
    properties:
      name: database.srv
      image: ubuntu-22.04
      flavor: m1.medium
    depends_on:
      - range_subnet

  app_server:
    type: OS::Nova::Server
    properties:
      name: webapp.srv
      image: debian-12
      flavor: m1.large
    depends_on:
      - db_server

outputs:
  net_id:
    description: Range Network ID
    value: { get_resource: range_net }
"""

SAMPLE_CYCLE_HOT = """
heat_template_version: 2018-03-02
description: Circular Dependency HOT Template

resources:
  service_a:
    type: OS::Nova::Server
    properties:
      name: srv_a
    depends_on:
      - service_b

  service_b:
    type: OS::Nova::Server
    properties:
      name: srv_b
    depends_on:
      - service_c

  service_c:
    type: OS::Nova::Server
    properties:
      name: srv_c
    depends_on:
      - service_a
"""


class TestHeatParser:
    def test_parse_valid_template(self):
        parser = HeatTemplateParser(SAMPLE_VALID_HOT)
        result = parser.parse()

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.version == "2018-03-02"
        assert result.resource_count == 4
        assert result.parameter_count == 2
        assert result.output_count == 1

        # Check topological execution order
        # range_net must come before range_subnet; range_subnet before db_server; db_server before app_server
        order = result.execution_order
        assert order.index("range_net") < order.index("range_subnet")
        assert order.index("range_subnet") < order.index("db_server")
        assert order.index("db_server") < order.index("app_server")

    def test_syntax_error_handling(self):
        invalid_yaml = "heat_template_version: [unclosed list"
        parser = HeatTemplateParser(invalid_yaml)
        result = parser.parse()

        assert result.is_valid is False
        assert any("syntax error" in e.lower() for e in result.errors)

    def test_missing_version_error(self):
        missing_ver = """
resources:
  vm1:
    type: OS::Nova::Server
"""
        parser = HeatTemplateParser(missing_ver)
        result = parser.parse()

        assert result.is_valid is False
        assert any("heat_template_version" in e for e in result.errors)

    def test_unknown_resource_reference(self):
        broken_ref = """
heat_template_version: 2018-03-02
resources:
  vm1:
    type: OS::Nova::Server
    depends_on:
      - nonexistent_resource
"""
        parser = HeatTemplateParser(broken_ref)
        result = parser.parse()

        assert result.is_valid is False
        assert any("nonexistent_resource" in e for e in result.errors)

    def test_dependency_loop_detection(self):
        parser = HeatTemplateParser(SAMPLE_CYCLE_HOT)
        result = parser.parse()

        assert result.is_valid is False
        cycle_errors = [e for e in result.errors if "dependency loop detected" in e.lower()]
        assert len(cycle_errors) > 0
        # Cycle error should report the chain
        assert any("service_a" in e and "service_b" in e and "service_c" in e for e in cycle_errors)

    def test_self_dependency_loop(self):
        self_dep = """
heat_template_version: 2018-03-02
resources:
  loop_server:
    type: OS::Nova::Server
    properties:
      name: looper
    depends_on:
      - loop_server
"""
        parser = HeatTemplateParser(self_dep)
        result = parser.parse()

        assert result.is_valid is False
        assert any("dependency loop detected" in e.lower() for e in result.errors)


class TestTopologyBuilder:
    def test_build_range_topology_nodes_and_links(self):
        topology = build_range_topology(
            hot_template=SAMPLE_VALID_HOT,
            stack_count=2,
            organization="test-range",
            protocol="rdp",
            port=3389,
            student_user="student",
            users_per_system=2,
            enable_swift=True,
        )

        assert "nodes" in topology
        assert "links" in topology
        assert "summary" in topology

        nodes = topology["nodes"]
        links = topology["links"]
        groups = {n["group"] for n in nodes}

        # Check required node groups exist
        assert "gateway" in groups
        assert "guac" in groups
        assert "network" in groups
        assert "server" in groups
        assert "user" in groups
        assert "storage" in groups

        # Verify Swift node present
        swift_nodes = [n for n in nodes if n["group"] == "storage"]
        assert len(swift_nodes) == 1
        assert "Swift" in swift_nodes[0]["label"]

        # Verify student seat scaling (2 stacks * 2 servers per stack * 2 users = 8 users)
        user_nodes = [n for n in nodes if n["group"] == "user"]
        assert len(user_nodes) == 8

        # Verify links connect nodes properly
        node_ids = {n["id"] for n in nodes}
        for link in links:
            assert link["source"] in node_ids
            assert link["target"] in node_ids


class TestTopologyEndpoints:
    def test_heat_validate_api(self, client):
        res = client.post("/api/heat/validate", json={"heat_yaml": SAMPLE_VALID_HOT})
        assert res.status_code == 200
        data = res.json()
        assert data["is_valid"] is True
        assert data["resource_count"] == 4
        assert len(data["execution_order"]) == 4

    def test_heat_validate_api_with_loop(self, client):
        res = client.post("/api/heat/validate", json={"heat_yaml": SAMPLE_CYCLE_HOT})
        assert res.status_code == 200
        data = res.json()
        assert data["is_valid"] is False
        assert any("dependency loop detected" in e.lower() for e in data["errors"])

    def test_topology_api(self, client):
        res = client.post("/api/topology", json={
            "heat_yaml": SAMPLE_VALID_HOT,
            "stack_count": 1,
            "organization": "web-range",
            "protocol": "ssh",
            "port": 22,
            "student_user": "operator",
            "users_per_system": 1,
            "enable_swift": False,
        })
        assert res.status_code == 200
        data = res.json()
        assert "nodes" in data
        assert "links" in data
        assert data["summary"]["organization"] == "web-range"
        assert data["summary"]["stack_count"] == 1
