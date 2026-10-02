"""
Command Line Interface for Range Provisioner.
Built with Click and Rich for powerful, beautiful terminal interactions.
"""
import os
import sys
import json
import csv
from typing import Optional

_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from src.provision.engine import ProvisionEngine, ProvisioningPlan
    from src.config.validator import (
        validate_range_package,
        validate_globals,
        validate_heat_template,
        validate_guacamole_template,
    )
    from src.utils import load_template
except ImportError:
    from provision.engine import ProvisionEngine, ProvisioningPlan
    from config.validator import (
        validate_range_package,
        validate_globals,
        validate_heat_template,
        validate_guacamole_template,
    )
    from utils import load_template

console = Console(safe_box=True)


@click.group()
@click.version_option(version="2.0.0", prog_name="range-provisioner")
def cli():
    """Range Provisioner: Orchestrate OpenStack Heat, Swift, and Apache Guacamole for Cyber Ranges."""
    pass


@cli.command("provision")
@click.option("--target", "-t", type=click.Choice(["full", "heat", "guacamole", "swift"]), default="full", help="Provisioning target.")
@click.option("--action", "-a", type=click.Choice(["create", "update", "delete"]), default="create", help="Action to perform.")
@click.option("--config", "-c", "config_file", default="globals.yaml", help="Path to globals.yaml configuration.")
@click.option("--clouds", default="clouds.yaml", help="Path to clouds.yaml credentials.")
@click.option("--dry-run", is_flag=True, default=False, help="Simulate execution without modifying real cloud resources.")
@click.option("--debug", is_flag=True, default=False, help="Enable verbose debug logging.")
@click.option("--delay", type=float, default=None, help="Override pause delay between API actions in seconds.")
@click.option("--export-users", "export_path", default=None, help="Export generated users to CSV/JSON file path.")
def provision_cmd(target, action, config_file, clouds, dry_run, debug, delay, export_path):
    """Deploy, update, or tear down a cyber range."""
    mode_text = "[bold yellow]DRY-RUN SIMULATION[/bold yellow]" if dry_run else "[bold green]LIVE EXECUTION[/bold green]"
    console.print(Panel(f"Target: [cyan]{target}[/cyan] | Action: [cyan]{action}[/cyan] | Mode: {mode_text}", title="Range Provisioner", border_style="blue"))

    engine = ProvisionEngine(globals_path=config_file, clouds_path=clouds, debug=debug, dry_run=dry_run)
    result = engine.run(target=target, action=action, delay_override=delay)

    if result.success:
        console.print(f"\n[bold green][SUCCESS] Provisioning finished successfully in {result.duration_seconds}s![/bold green]")
        if export_path:
            _export_users_from_config(config_file, export_path)
    else:
        console.print(f"\n[bold red][FAILED] Provisioning failed after {result.duration_seconds}s:[/bold red]")
        for err in result.errors:
            console.print(f"  [red]- {err}[/red]")
        sys.exit(1)


@cli.command("validate")
@click.option("--config", "-c", "config_file", default="globals.yaml", help="Path to globals.yaml.")
@click.option("--heat", "heat_file", default=None, help="Path to Heat template (defaults from globals).")
@click.option("--guac", "guac_file", default=None, help="Path to Guacamole template (defaults from globals).")
def validate_cmd(config_file, heat_file, guac_file):
    """Validate template syntax, Jinja rendering, and configuration schemas."""
    console.print(f"[bold cyan]Validating Range Configuration Files...[/bold cyan]")

    if not os.path.exists(config_file):
        console.print(f"[red]Error: Config file '{config_file}' not found![/red]")
        sys.exit(1)

    globals_raw = open(config_file, "r", encoding="utf-8").read()
    g_res = validate_globals(globals_raw)

    heat_content = None
    if not heat_file:
        try:
            g_dict = load_template.load_template(config_file)
            heat_file = g_dict.get("heat", {}).get("heat_file", "templates/main.yaml")
        except Exception:
            heat_file = "templates/main.yaml"

    if os.path.exists(heat_file):
        heat_content = open(heat_file, "r", encoding="utf-8").read()

    guac_content = None
    if not guac_file:
        try:
            g_dict = load_template.load_template(config_file)
            guac_file = g_dict.get("guacamole", {}).get("guac_file", "templates/guac.yaml")
        except Exception:
            guac_file = "templates/guac.yaml"

    if os.path.exists(guac_file):
        guac_content = open(guac_file, "r", encoding="utf-8").read()

    res = validate_range_package(globals_raw, heat_content, guac_content)

    table = Table(title="Validation Report", border_style="blue")
    table.add_column("Component", style="bold")
    table.add_column("File Path")
    table.add_column("Status")
    table.add_column("Details")

    table.add_row(
        "Globals",
        config_file,
        "[green]Valid[/green]" if not g_res.errors else "[red]Invalid[/red]",
        f"Org: {g_res.info.get('organization')}, Stacks: {g_res.info.get('heat_stacks_amount')}"
    )

    if heat_content:
        h_res = validate_heat_template(heat_content)
        table.add_row(
            "Heat HOT",
            heat_file,
            "[green]Valid[/green]" if not h_res.errors else "[red]Invalid[/red]",
            f"HOT {h_res.info.get('heat_template_version')}, Servers: {h_res.info.get('server_count')}"
        )
    else:
        table.add_row("Heat HOT", heat_file or "None", "[yellow]Not Found[/yellow]", "Skipped")

    if guac_content:
        gu_res = validate_guacamole_template(guac_content)
        table.add_row(
            "Guacamole",
            guac_file,
            "[green]Valid[/green]" if not gu_res.errors else "[red]Invalid[/red]",
            f"Groups: {gu_res.info.get('group_count')}, Templates: {gu_res.info.get('connection_count')}, Users: {gu_res.info.get('user_count')}"
        )
    else:
        table.add_row("Guacamole", guac_file or "None", "[yellow]Not Found[/yellow]", "Skipped")

    console.print(table)

    if res.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in res.warnings:
            console.print(f"  [yellow]- {w}[/yellow]")

    if res.errors:
        console.print("\n[bold red]Validation Errors:[/bold red]")
        for e in res.errors:
            console.print(f"  [red]- {e}[/red]")
        sys.exit(1)
    else:
        console.print("\n[bold green][PASS] All configurations passed validation![/bold green]")


@cli.command("inspect")
@click.option("--config", "-c", "config_file", default="globals.yaml", help="Path to globals.yaml.")
def inspect_cmd(config_file):
    """Visually inspect range hierarchy, connection groups, and users."""
    if not os.path.exists(config_file):
        console.print(f"[red]Error: '{config_file}' not found![/red]")
        sys.exit(1)

    g_dict = load_template.load_template(config_file) or {}
    globals_data = g_dict.get("globals", {})
    heat_data = g_dict.get("heat", {})
    guac_data = g_dict.get("guacamole", {})

    org = globals_data.get("organization", "range")
    root_tree = Tree(f"[bold cyan]Cyber Range: {org}[/bold cyan]")

    # Stacks branch
    stacks_node = root_tree.add(f"[bold yellow]OpenStack Heat ({heat_data.get('amount', 1)} stacks)[/bold yellow]")
    stacks_node.add(f"Cloud: [cyan]{heat_data.get('cloud')}[/cyan]")
    stacks_node.add(f"Template: [cyan]{heat_data.get('heat_file')}[/cyan]")

    # Guacamole branch
    guac_file = guac_data.get("guac_file", "templates/guac.yaml")
    guac_node = root_tree.add(f"[bold green]Guacamole Service[/bold green]")
    guac_node.add(f"Cloud: [cyan]{guac_data.get('cloud')}[/cyan]")
    guac_node.add(f"Config: [cyan]{guac_file}[/cyan]")

    if os.path.exists(guac_file):
        guac_params = load_template.load_yaml_file(guac_file, debug=False) or {}
        groups_node = guac_node.add(f"Connection Groups ({len(guac_params.get('groups', {}))})")
        for grp_name, grp_info in guac_params.get("groups", {}).items():
            groups_node.add(f"[bold]{grp_name}[/bold] (parent: {grp_info.get('parent', 'ROOT')})")

        conns_node = guac_node.add(f"Connection Templates ({len(guac_params.get('connectionTemplates', {}))})")
        for c_name, c_info in guac_params.get("connectionTemplates", {}).items():
            conns_node.add(f"[magenta]{c_name}[/magenta] [dim]proto={c_info.get('protocol', 'rdp')} pattern={c_info.get('pattern')}[/dim]")

        users_node = guac_node.add(f"Users ({len(guac_params.get('users', {}))})")
        for u_name, u_info in guac_params.get("users", {}).items():
            perms = u_info.get("permissions", {}).get("connectionPermissions", [])
            users_node.add(f"[blue]{u_info.get('username', u_name)}[/blue] -> assigned: {', '.join(perms) if perms else 'None'}")

    console.print(root_tree)


@cli.command("export-users")
@click.option("--config", "-c", "config_file", default="globals.yaml", help="Path to globals.yaml.")
@click.option("--output", "-o", default="credentials.csv", help="Output file path (.csv or .json).")
def export_users_cmd(config_file, output):
    """Export generated Guacamole user accounts and passwords."""
    _export_users_from_config(config_file, output)


def _export_users_from_config(config_file: str, output_path: str) -> None:
    g_dict = load_template.load_template(config_file) or {}
    guac_data = g_dict.get("guacamole", {})
    guac_file = guac_data.get("guac_file", "templates/guac.yaml")

    if not os.path.exists(guac_file):
        console.print(f"[red]Error: Guacamole template '{guac_file}' not found![/red]")
        return

    guac_params = load_template.load_yaml_file(guac_file, debug=False) or {}
    users_dict = guac_params.get("users", {})

    user_rows = []
    for u_key, u_val in users_dict.items():
        perms = u_val.get("permissions", {}).get("connectionPermissions", [])
        user_rows.append({
            "key": u_key,
            "username": u_val.get("username", u_key),
            "password": u_val.get("password", "<auto-generated>"),
            "connections": "; ".join(perms)
        })

    if output_path.endswith(".json"):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(user_rows, f, indent=2)
    else:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "username", "password", "connections"])
            writer.writeheader()
            writer.writerows(user_rows)

    console.print(f"[green][SUCCESS] Exported {len(user_rows)} users to '{output_path}'[/green]")


@cli.command("init")
@click.option("--directory", "-d", default=".", help="Target directory for new range project.")
@click.option("--org", default="cyberrange", help="Organization name for default templates.")
def init_cmd(directory, org):
    """Scaffold starter templates and configuration for a new cyber range."""
    os.makedirs(os.path.join(directory, "templates"), exist_ok=True)
    os.makedirs(os.path.join(directory, "assets"), exist_ok=True)

    globals_content = f"""# YAML for storing range provisioning parameters
globals:
  debug: false
  artifacts: true
  organization: {org}
  amount: 1
  provision: true

guacamole:
  provision: true
  update: false
  cloud: guacamole
  guac_file: templates/guac.yaml
  org_name: {org}
  pause: 0.1

heat:
  provision: true
  update: false
  cloud: openstack
  amount: 1
  heat_file: templates/main.yaml
  stack_name: {org}
  stack_delay: 5
  pause: 0.1
  jinja: true

swift:
  provision: false
  update: false
  cloud: openstack
  assets_dir: assets
  container_name: {org}
"""

    guac_content = f"""# Guacamole configuration
{{% set systems = 2 %}}
{{% set organization = "{org}" %}}

stacks:
  - {{{{ organization }}}}

groups:
  {{{{ organization }}}}:
    parent: ROOT
    attributes:
      max-connections: 20

connectionTemplates:
  {{{{ organization }}}}.screen.server:
    parent: {{{{ organization }}}}
    pattern: {{{{ organization }}}}.screen.server.(\\d+)
    protocol: rdp
    parameters:
      port: 3389
      security: any
      ignore-cert: 'true'
      username: student
      password: studentpassword

users:
  {{% for system in range(1, systems + 1) %}}
  {{{{ organization }}}}.user.{{{{ system }}}}:
    username: {{{{ organization }}}}.screen.{{{{ system }}}}
    password: RangePassword{{{{ system }}}}!
    permissions:
      connectionPermissions:
        - {{{{ organization }}}}.screen.server.{{{{ system }}}}
  {{% endfor %}}
"""

    heat_content = """heat_template_version: 2018-03-02
description: Starter Cyber Range Stack Template

parameters:
  username:
    type: string
    default: rangeuser
  password:
    type: string
    default: rangepassword

resources:
  range_network:
    type: OS::Neutron::Net
    properties:
      name: range_network

  range_subnet:
    type: OS::Neutron::Subnet
    properties:
      network_id: { get_resource: range_network }
      cidr: 10.10.10.0/24
      dns_nameservers: [8.8.8.8, 1.1.1.1]

outputs:
  network_id:
    value: { get_resource: range_network }
"""

    with open(os.path.join(directory, "globals.yaml"), "w", encoding="utf-8") as f:
        f.write(globals_content)

    with open(os.path.join(directory, "templates", "guac.yaml"), "w", encoding="utf-8") as f:
        f.write(guac_content)

    with open(os.path.join(directory, "templates", "main.yaml"), "w", encoding="utf-8") as f:
        f.write(heat_content)

    console.print(f"[bold green][SUCCESS] Scaffolding created in '{directory}'![/bold green]")
    console.print("  - globals.yaml")
    console.print("  - templates/guac.yaml")
    console.print("  - templates/main.yaml")
    console.print("  - assets/")


@cli.command("test-connection")
@click.option("--clouds", default="clouds.yaml", help="Path to clouds.yaml.")
@click.option("--cloud", "-c", required=True, help="Cloud name to test.")
@click.option("--type", "-t", "conn_type", type=click.Choice(["openstack", "guacamole"]), default="openstack", help="Connection type.")
def test_connection_cmd(clouds, cloud, conn_type):
    """Test connection credentials to OpenStack or Guacamole."""
    if not os.path.exists(clouds):
        console.print(f"[red]Error: Clouds file '{clouds}' not found![/red]")
        sys.exit(1)

    clouds_dict = load_template.load_template(clouds) or {}
    cloud_config = clouds_dict.get("clouds", {}).get(cloud)
    if not cloud_config:
        console.print(f"[red]Error: Cloud '{cloud}' not found in '{clouds}'![/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Connecting to {conn_type} cloud '{cloud}'...[/bold cyan]")
    try:
        from src.utils import connections as conn_utils
    except ImportError:
        from utils import connections as conn_utils

    if conn_type == "openstack":
        conn = conn_utils.openstack_connection(cloud, cloud_config, debug=True)
        if conn:
            console.print("[bold green][SUCCESS] Successfully connected to OpenStack![/bold green]")
        else:
            console.print("[bold red][FAILED] Failed to connect to OpenStack[/bold red]")
            sys.exit(1)
    else:
        conn = conn_utils.guacamole_connection(cloud, cloud_config, debug=True)
        if conn:
            console.print("[bold green][SUCCESS] Successfully connected to Guacamole![/bold green]")
        else:
            console.print("[bold red][FAILED] Failed to connect to Guacamole[/bold red]")
            sys.exit(1)


@cli.command("serve")
@click.option("--host", default="127.0.0.1", help="Host address to bind.")
@click.option("--port", default=8000, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload on code change.")
def serve_cmd(host, port, reload):
    """Start the Range Provisioner FastAPI website and REST API."""
    import uvicorn
    console.print(Panel(f"Starting Web Dashboard & API at [bold cyan]http://{host}:{port}[/bold cyan]", title="Range Provisioner Studio", border_style="green"))
    uvicorn.run("src.web.app:app", host=host, port=port, reload=reload)


@cli.group("schedule")
def schedule_group():
    """Manage automated build and teardown schedules for cyber ranges."""
    pass


@schedule_group.command("list")
def schedule_list_cmd():
    """List all scheduled range builds and teardowns."""
    try:
        from src.db.database import SessionLocal
        from src.db.models import ScheduledJob
        from src.db import init_db
    except ImportError:
        from db.database import SessionLocal
        from db.models import ScheduledJob
        from db import init_db

    init_db()
    with SessionLocal() as db:
        jobs = db.query(ScheduledJob).order_by(ScheduledJob.created_at.desc()).all()
        if not jobs:
            console.print("[yellow]No scheduled range jobs found.[/yellow]")
            return

        table = Table(title="Cyber Range Provisioning & Teardown Schedules", border_style="cyan")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Name", style="bold white")
        table.add_column("Range", style="cyan")
        table.add_column("Target", style="magenta")
        table.add_column("Mode", style="yellow")
        table.add_column("Build Time (UTC)", style="green")
        table.add_column("Build Status", style="green")
        table.add_column("Delete Time (UTC)", style="red")
        table.add_column("Delete Status", style="red")

        for j in jobs:
            mode = "DRY-RUN" if j.dry_run else "LIVE"
            r_name = j.range.name if j.range else f"#{j.range_id or 'Ad-hoc'}"
            table.add_row(
                str(j.id),
                j.name,
                r_name,
                j.target,
                mode,
                j.build_at.strftime("%Y-%m-%d %H:%M") if j.build_at else "-",
                j.build_status,
                j.delete_at.strftime("%Y-%m-%d %H:%M") if j.delete_at else "-",
                j.delete_status
            )
        console.print(table)


@schedule_group.command("create")
@click.option("--name", "-n", required=True, help="Name of scheduled job.")
@click.option("--range-id", "-r", type=int, default=None, help="Database ID of saved range.")
@click.option("--target", "-t", type=click.Choice(["full", "heat", "openstack", "guacamole", "swift"]), default="full", help="Target component.")
@click.option("--build", "--build-at", "build_time", default=None, help="Build datetime (e.g. '2026-10-05 09:00' or ISO format).")
@click.option("--delete", "--delete-at", "delete_time", default=None, help="Delete datetime (e.g. '2026-10-05 17:00' or ISO format).")
@click.option("--dry-run", is_flag=True, default=False, help="Simulate without live changes.")
def schedule_create_cmd(name, range_id, target, build_time, delete_time, dry_run):
    """Create a new automated range build/delete schedule."""
    if not build_time and not delete_time:
        console.print("[red]Error: You must specify at least one of --build or --delete datetime.[/red]")
        sys.exit(1)

    from datetime import datetime, timezone

    b_dt = None
    if build_time:
        try:
            b_dt = datetime.fromisoformat(build_time)
            if b_dt.tzinfo is None:
                b_dt = b_dt.replace(tzinfo=timezone.utc)
            b_dt = b_dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception as e:
            console.print(f"[red]Error parsing build datetime: {e}[/red]")
            sys.exit(1)

    d_dt = None
    if delete_time:
        try:
            d_dt = datetime.fromisoformat(delete_time)
            if d_dt.tzinfo is None:
                d_dt = d_dt.replace(tzinfo=timezone.utc)
            d_dt = d_dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception as e:
            console.print(f"[red]Error parsing delete datetime: {e}[/red]")
            sys.exit(1)

    if b_dt and d_dt and d_dt <= b_dt:
        console.print("[red]Error: Delete time must be later than build time.[/red]")
        sys.exit(1)

    try:
        from src.db.database import SessionLocal
        from src.db.models import ScheduledJob
        from src.db import init_db
    except ImportError:
        from db.database import SessionLocal
        from db.models import ScheduledJob
        from db import init_db

    init_db()
    with SessionLocal() as db:
        job = ScheduledJob(
            name=name,
            range_id=range_id,
            target=target,
            dry_run=dry_run,
            build_at=b_dt,
            delete_at=d_dt,
            build_status="scheduled" if b_dt else "skipped",
            delete_status="scheduled" if d_dt else "skipped",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        console.print(f"[bold green]Successfully created scheduled job #{job.id} '{job.name}'![/bold green]")
        if b_dt:
            console.print(f"  [cyan]Build Scheduled:[/cyan]  {b_dt} UTC")
        if d_dt:
            console.print(f"  [red]Delete Scheduled:[/red] {d_dt} UTC")


@schedule_group.command("cancel")
@click.argument("job_id", type=int)
@click.option("--action", "-a", type=click.Choice(["build", "delete", "all", "both"]), default="all", help="Action to cancel.")
def schedule_cancel_cmd(job_id, action):
    """Cancel a pending schedule action."""
    try:
        from src.db.database import SessionLocal
        from src.db.models import ScheduledJob
    except ImportError:
        from db.database import SessionLocal
        from db.models import ScheduledJob

    with SessionLocal() as db:
        job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            console.print(f"[red]Scheduled job #{job_id} not found.[/red]")
            sys.exit(1)

        if action in ["build", "all", "both"] and job.build_status == "scheduled":
            job.build_status = "cancelled"
        if action in ["delete", "all", "both"] and job.delete_status == "scheduled":
            job.delete_status = "cancelled"

        db.commit()
        console.print(f"[bold green]Job #{job_id} updated. Build: {job.build_status}, Delete: {job.delete_status}[/bold green]")


if __name__ == "__main__":
    cli()
