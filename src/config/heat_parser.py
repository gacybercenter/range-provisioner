"""
OpenStack Heat Orchestration Template (HOT) Parser and Validator.
Performs comprehensive validation of YAML syntax, template version, resource schema,
intrinsic function resolution (get_resource, get_param, get_attr), and dependency loop detection.
Also extracts network and compute topology for D3 visualizer.
"""
import re
import yaml
from typing import Dict, Any, List, Set, Optional, Tuple
from dataclasses import dataclass, field


VALID_TEMPLATE_VERSIONS = {
    "2013-05-23", "2014-10-16", "2015-04-30", "2015-10-15",
    "2016-04-08", "2016-10-14", "2017-02-24", "2017-09-01",
    "2018-03-02", "2018-08-31", "2021-04-16", "wallaby",
    "xena", "yoga", "zed", "2023.1", "2023.2", "2024.1", "2024.2",
}

PSEUDO_PARAMETERS = {
    "OS::stack_name",
    "OS::stack_id",
    "OS::project_id",
    "OS::project_name",
    "OS::user_id",
    "OS::username",
}

KNOWN_RESOURCE_PREFIXES = {
    "OS::Nova::",
    "OS::Neutron::",
    "OS::Heat::",
    "OS::Cinder::",
    "OS::Glance::",
    "OS::Keystone::",
    "OS::Swift::",
}


@dataclass
class HeatValidationResult:
    is_valid: bool
    version: Optional[str] = None
    description: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    resource_count: int = 0
    parameter_count: int = 0
    output_count: int = 0
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "version": self.version,
            "description": self.description,
            "errors": self.errors,
            "warnings": self.warnings,
            "resource_count": self.resource_count,
            "parameter_count": self.parameter_count,
            "output_count": self.output_count,
            "dependency_graph": self.dependency_graph,
            "execution_order": self.execution_order,
            "resources": self.resources,
        }


class HeatTemplateParser:
    """Parser and validator for OpenStack Heat Orchestration Templates."""

    def __init__(self, template_str_or_dict: Any):
        self.raw_data = template_str_or_dict
        self.parsed_dict: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def parse(self) -> HeatValidationResult:
        if isinstance(self.raw_data, str):
            try:
                self.parsed_dict = yaml.safe_load(self.raw_data)
            except yaml.YAMLError as exc:
                mark = getattr(exc, "problem_mark", None)
                loc = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
                self.errors.append(f"Heat YAML syntax error{loc}: {exc}")
                return HeatValidationResult(is_valid=False, errors=self.errors)
        elif isinstance(self.raw_data, dict):
            self.parsed_dict = self.raw_data
        else:
            self.errors.append("Invalid template format: expected YAML string or dictionary")
            return HeatValidationResult(is_valid=False, errors=self.errors)

        if not isinstance(self.parsed_dict, dict):
            self.errors.append("Top-level template structure must be a YAML mapping/dictionary")
            return HeatValidationResult(is_valid=False, errors=self.errors)

        # 1. Template Version check
        version = self.parsed_dict.get("heat_template_version")
        if not version:
            self.errors.append("Missing required field 'heat_template_version'")
        else:
            version_str = str(version)
            if version_str not in VALID_TEMPLATE_VERSIONS:
                self.warnings.append(
                    f"Template version '{version_str}' is non-standard or unrecognized. Standard versions include: "
                    + ", ".join(sorted(list(VALID_TEMPLATE_VERSIONS))[-5:])
                )

        description = self.parsed_dict.get("description", "")

        # 2. Parameters validation
        params_section = self.parsed_dict.get("parameters", {})
        param_names: Set[str] = set()
        if params_section is not None:
            if not isinstance(params_section, dict):
                self.errors.append("'parameters' section must be a dictionary")
            else:
                param_names = set(params_section.keys())
                for p_name, p_def in params_section.items():
                    if not isinstance(p_def, dict):
                        self.errors.append(f"Parameter '{p_name}' definition must be a dictionary")
                    elif "type" not in p_def:
                        self.errors.append(f"Parameter '{p_name}' is missing required 'type' field")
                    else:
                        p_type = p_def["type"].lower()
                        valid_types = {"string", "number", "json", "comma_delimited_list", "boolean"}
                        if p_type not in valid_types:
                            self.warnings.append(
                                f"Parameter '{p_name}' uses uncommon type '{p_type}'. Valid types: {', '.join(sorted(valid_types))}"
                            )

        # 3. Resources validation
        resources_section = self.parsed_dict.get("resources")
        if resources_section is None:
            self.errors.append("Missing required 'resources' section in Heat template")
            return HeatValidationResult(
                is_valid=False,
                version=str(version) if version else None,
                description=description,
                errors=self.errors,
                warnings=self.warnings,
            )

        if not isinstance(resources_section, dict):
            self.errors.append("'resources' section must be a dictionary of resource definitions")
            return HeatValidationResult(
                is_valid=False,
                version=str(version) if version else None,
                description=description,
                errors=self.errors,
                warnings=self.warnings,
            )

        if len(resources_section) == 0:
            self.errors.append("Heat template 'resources' section cannot be empty; at least one resource is required")

        resource_names = set(resources_section.keys())
        resources_summary = []

        # Graph of: Resource -> Set of resources it depends on
        dep_graph: Dict[str, Set[str]] = {r: set() for r in resource_names}

        for r_name, r_def in resources_section.items():
            if not isinstance(r_def, dict):
                self.errors.append(f"Resource '{r_name}' definition must be a dictionary")
                continue

            r_type = r_def.get("type")
            if not r_type:
                self.errors.append(f"Resource '{r_name}' is missing required 'type' property")
                continue

            is_known_prefix = any(r_type.startswith(prefix) for prefix in KNOWN_RESOURCE_PREFIXES)
            if not is_known_prefix:
                self.warnings.append(
                    f"Resource '{r_name}' has unrecognized resource type '{r_type}'"
                )

            # Check explicit depends_on
            explicit_deps = r_def.get("depends_on", [])
            if isinstance(explicit_deps, str):
                explicit_deps = [explicit_deps]
            elif not isinstance(explicit_deps, list):
                self.errors.append(f"Resource '{r_name}' has invalid 'depends_on' (must be string or list of strings)")
                explicit_deps = []

            for dep in explicit_deps:
                if dep not in resource_names:
                    self.errors.append(
                        f"Resource '{r_name}' depends on '{dep}', but '{dep}' is not defined in resources"
                    )
                else:
                    dep_graph[r_name].add(dep)

            # Check intrinsic functions: get_resource, get_param, get_attr
            props = r_def.get("properties", {})
            self._scan_intrinsic_functions(
                r_name, props, resource_names, param_names, dep_graph[r_name]
            )

            # Metadata scan
            meta = r_def.get("metadata", {})
            self._scan_intrinsic_functions(
                r_name, meta, resource_names, param_names, dep_graph[r_name]
            )

            is_server = r_type in ["OS::Nova::Server", "OS::Heat::ResourceGroup"]
            is_net = r_type in ["OS::Neutron::Net", "OS::Neutron::Subnet", "OS::Neutron::Router", "OS::Neutron::Port"]
            resources_summary.append({
                "name": r_name,
                "type": r_type,
                "is_server": is_server,
                "is_network": is_net,
                "dependencies": sorted(list(dep_graph[r_name])),
            })

        # 4. Circular Dependency / Dependency Loop Detection
        has_cycles, cycle_paths = self._detect_cycles(dep_graph)
        if has_cycles:
            for cycle in cycle_paths:
                cycle_str = " -> ".join(cycle)
                self.errors.append(f"Dependency loop detected: {cycle_str}")

        # 5. Execution Order (Topological Sort)
        execution_order = []
        if not has_cycles and len(self.errors) == 0:
            execution_order = self._topological_sort(dep_graph)

        # 6. Outputs validation
        outputs_section = self.parsed_dict.get("outputs", {})
        if outputs_section:
            if not isinstance(outputs_section, dict):
                self.errors.append("'outputs' section must be a dictionary")
            else:
                for out_name, out_def in outputs_section.items():
                    if isinstance(out_def, dict):
                        if "value" not in out_def:
                            self.warnings.append(f"Output '{out_name}' is missing a 'value' definition")

        is_valid = len(self.errors) == 0

        return HeatValidationResult(
            is_valid=is_valid,
            version=str(version) if version else None,
            description=description,
            errors=self.errors,
            warnings=self.warnings,
            resource_count=len(resources_section) if isinstance(resources_section, dict) else 0,
            parameter_count=len(param_names),
            output_count=len(outputs_section) if isinstance(outputs_section, dict) else 0,
            dependency_graph={k: sorted(list(v)) for k, v in dep_graph.items()},
            execution_order=execution_order,
            resources=resources_summary,
        )

    def _scan_intrinsic_functions(
        self,
        current_res: str,
        obj: Any,
        resource_names: Set[str],
        param_names: Set[str],
        dep_set: Set[str],
    ) -> None:
        """Recursively scan data structures for get_resource, get_param, and get_attr calls."""
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key == "get_resource":
                    target_res = val if isinstance(val, str) else None
                    if target_res:
                        if target_res not in resource_names:
                            self.errors.append(
                                f"Resource '{current_res}' references unknown resource '{target_res}' via get_resource"
                            )
                        else:
                            dep_set.add(target_res)
                    else:
                        self.errors.append(f"Resource '{current_res}' has malformed get_resource call: {val}")

                elif key == "get_attr":
                    if isinstance(val, list) and len(val) >= 2:
                        target_res = val[0]
                        if isinstance(target_res, str):
                            if target_res not in resource_names:
                                self.errors.append(
                                    f"Resource '{current_res}' references unknown resource '{target_res}' via get_attr"
                                )
                            else:
                                dep_set.add(target_res)
                    else:
                        self.errors.append(f"Resource '{current_res}' has malformed get_attr call: {val}")

                elif key == "get_param":
                    target_param = val[0] if isinstance(val, list) and val else val
                    if isinstance(target_param, str):
                        if target_param not in param_names and target_param not in PSEUDO_PARAMETERS:
                            self.warnings.append(
                                f"Resource '{current_res}' references parameter '{target_param}', which is not declared in 'parameters'"
                            )
                    else:
                        self.errors.append(f"Resource '{current_res}' has malformed get_param call: {val}")

                else:
                    self._scan_intrinsic_functions(current_res, val, resource_names, param_names, dep_set)

        elif isinstance(obj, list):
            for item in obj:
                self._scan_intrinsic_functions(current_res, item, resource_names, param_names, dep_set)

    def _detect_cycles(self, graph: Dict[str, Set[str]]) -> Tuple[bool, List[List[str]]]:
        """Detect cycles using Depth First Search with 3-state coloring."""
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {node: WHITE for node in graph}
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(node: str):
            colors[node] = GRAY
            path.append(node)

            for neighbor in graph.get(node, []):
                if colors.get(neighbor) == GRAY:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle_path = path[cycle_start:] + [neighbor]
                    cycles.append(cycle_path)
                elif colors.get(neighbor) == WHITE:
                    dfs(neighbor)

            path.pop()
            colors[node] = BLACK

        for n in graph:
            if colors[n] == WHITE:
                dfs(n)

        return len(cycles) > 0, cycles

    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Kahn's algorithm for topological sorting of resource dependencies."""
        # Compute in-degrees: A depends on B means edge B -> A (B must be built before A)
        dependents: Dict[str, Set[str]] = {node: set() for node in graph}
        in_degree: Dict[str, int] = {node: 0 for node in graph}

        for node, deps in graph.items():
            in_degree[node] = len(deps)
            for dep in deps:
                dependents[dep].add(node)

        queue = [n for n, deg in in_degree.items() if deg == 0]
        order: List[str] = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for dep_of in dependents[curr]:
                in_degree[dep_of] -= 1
                if in_degree[dep_of] == 0:
                    queue.append(dep_of)

        return order


def build_range_topology(
    hot_template: str,
    stack_count: int = 1,
    organization: str = "cyberrange",
    protocol: str = "rdp",
    port: int = 3389,
    student_user: str = "student",
    users_per_system: int = 2,
    enable_swift: bool = False,
) -> Dict[str, Any]:
    """
    Builds a complete, graph-based cyber range topology representation
    for rendering with D3.js.
    """
    parser = HeatTemplateParser(hot_template)
    validation = parser.parse()

    nodes = []
    links = []
    node_ids = set()

    def add_node(node_id: str, label: str, group: str, icon: str, details: Dict[str, Any] = None):
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({
                "id": node_id,
                "label": label,
                "group": group,  # 'gateway', 'network', 'server', 'guac', 'user', 'storage'
                "icon": icon,
                "details": details or {},
            })

    def add_link(source_id: str, target_id: str, link_type: str = "network", label: str = ""):
        if source_id in node_ids and target_id in node_ids:
            links.append({
                "source": source_id,
                "target": target_id,
                "type": link_type,  # 'network', 'route', 'access', 'user'
                "label": label,
            })

    # 1. External Gateway / Internet Node
    gateway_id = "ext-gateway"
    add_node(gateway_id, "External Gateway / Internet", "gateway", "fa-globe", {
        "type": "Network Gateway",
        "ip": "0.0.0.0/0",
        "description": "Provider uplink router connecting range to external access."
    })

    # 2. Apache Guacamole Remote Access Gateway Node
    guac_id = "guac-gateway"
    add_node(guac_id, "Guacamole Remote Gateway", "guac", "fa-desktop", {
        "type": "Remote Access Gateway",
        "protocol": protocol.upper(),
        "port": port,
        "description": "Central proxy brokering clientless web sessions."
    })
    add_link(gateway_id, guac_id, "route", "HTTPS")

    # 3. Swift Object Storage Node (if enabled)
    if enable_swift:
        swift_id = f"swift-{organization}"
        add_node(swift_id, f"Swift Assets ({organization})", "storage", "fa-database", {
            "type": "Object Storage Container",
            "container": organization,
            "description": "Range provisioning artifacts and scripts repository."
        })
        add_link(gateway_id, swift_id, "network", "Storage API")

    # Parse resources from HOT template
    resources = parser.parsed_dict.get("resources", {}) if parser.parsed_dict else {}

    # Find network definitions in HOT
    hot_networks = []
    hot_subnets = []
    hot_servers = []

    for r_name, r_def in resources.items():
        if not isinstance(r_def, dict):
            continue
        r_type = r_def.get("type", "")
        if r_type == "OS::Neutron::Net":
            hot_networks.append((r_name, r_def))
        elif r_type == "OS::Neutron::Subnet":
            hot_subnets.append((r_name, r_def))
        elif r_type in ["OS::Nova::Server", "OS::Heat::ResourceGroup"]:
            hot_servers.append((r_name, r_def))

    # If no networks defined in template, create a default range network
    if not hot_networks:
        hot_networks.append(("range_network", {"properties": {"name": f"{organization}_net"}}))
        hot_subnets.append(("range_subnet", {"properties": {"cidr": "10.10.10.0/24"}}))

    # Build stacks
    user_counter = 1
    for s_idx in range(1, stack_count + 1):
        stack_prefix = f"stack.{s_idx}" if stack_count > 1 else organization

        # Networks for this stack
        for net_name, net_def in hot_networks:
            net_node_id = f"{stack_prefix}-{net_name}"
            cidr = "10.10.10.0/24"
            for _, sub_def in hot_subnets:
                props = sub_def.get("properties", {})
                if props.get("cidr"):
                    cidr = props.get("cidr")
                    break

            add_node(net_node_id, f"{net_name} ({stack_prefix})", "network", "fa-network-wired", {
                "type": "Neutron Network",
                "subnet": cidr,
                "stack": stack_prefix,
            })
            add_link(gateway_id, net_node_id, "route", "Routing")
            add_link(guac_id, net_node_id, "access", "VPC Link")

            # Servers in this stack
            if hot_servers:
                for srv_name, srv_def in hot_servers:
                    srv_node_id = f"{stack_prefix}-{srv_name}"
                    flavor = srv_def.get("properties", {}).get("flavor", "m1.medium")
                    image = srv_def.get("properties", {}).get("image", "ubuntu-22.04")
                    ip_addr = f"10.10.10.{100 + s_idx * 10 + len(nodes) % 50}"

                    add_node(srv_node_id, f"{srv_name} ({stack_prefix})", "server", "fa-server", {
                        "type": "Compute VM",
                        "image": image,
                        "flavor": flavor,
                        "ip": ip_addr,
                        "login_user": student_user,
                        "stack": stack_prefix,
                    })
                    add_link(net_node_id, srv_node_id, "network", "Internal IP")
                    add_link(guac_id, srv_node_id, "access", f"{protocol.upper()}:{port}")

                    # Student Users connecting to this server
                    for _ in range(users_per_system):
                        user_node_id = f"user-{organization}-{user_counter}"
                        u_name = f"{organization}.screen.{user_counter}"
                        add_node(user_node_id, u_name, "user", "fa-user-shield", {
                            "type": "Student Seat",
                            "username": u_name,
                            "target_server": srv_name,
                            "protocol": protocol.upper(),
                        })
                        add_link(guac_id, user_node_id, "user", "Session")
                        user_counter += 1
            else:
                # Default server if HOT doesn't specify one
                default_srv_id = f"{stack_prefix}-workstation"
                add_node(default_srv_id, f"workstation ({stack_prefix})", "server", "fa-server", {
                    "type": "Compute VM",
                    "ip": f"10.10.10.{100 + s_idx}",
                    "login_user": student_user,
                    "stack": stack_prefix,
                })
                add_link(net_node_id, default_srv_id, "network", "Internal IP")
                add_link(guac_id, default_srv_id, "access", f"{protocol.upper()}:{port}")

                for _ in range(users_per_system):
                    user_node_id = f"user-{organization}-{user_counter}"
                    u_name = f"{organization}.screen.{user_counter}"
                    add_node(user_node_id, u_name, "user", "fa-user-shield", {
                        "type": "Student Seat",
                        "username": u_name,
                        "target_server": "workstation",
                        "protocol": protocol.upper(),
                    })
                    add_link(guac_id, user_node_id, "user", "Session")
                    user_counter += 1

    return {
        "nodes": nodes,
        "links": links,
        "summary": {
            "node_count": len(nodes),
            "link_count": len(links),
            "stack_count": stack_count,
            "organization": organization,
            "user_count": user_counter - 1,
        }
    }
