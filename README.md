# Range Provisioner (v2.0)

**Range Provisioner** is an automated orchestration platform for provisioning, updating, inspecting, and managing **Cyber Range** environments. It integrates with **OpenStack** (Heat Orchestration & Swift Object Storage) and **Apache Guacamole** (Connection Groups, Connections, Sharing Profiles, and User Permissions).

Range Provisioner can be run in two ways:
1. **Interactive Web Dashboard & REST API** built with FastAPI
2. **Subcommand CLI Tool** with colored terminal tables, inspection trees, and progress indicators

---

## What's New in Version 2.0

- **FastAPI Web Studio & REST API**:
  - Interactive browser dashboard to upload, inspect, validate, parameterize, and deploy ranges.
  - Live console streaming logs in real time via WebSockets.
  - Range Builder wizard to visually generate configuration files without writing YAML manually.
  - Downloadable configuration packages (ZIP) and user credential exports (CSV/JSON).
- **Subcommand CLI (`range-provisioner` / `provisioner`)**:
  - Modern CLI built with Click and Rich.
  - Commands: `provision`, `validate`, `inspect`, `export-users`, `init`, `test-connection`, `serve`.
- **Dry-Run Simulation**:
  - Simulate provisioning without making live API calls or modifying cloud resources.
- **Pydantic Validation**:
  - Strong schema and syntax validation for `globals.yaml`, Heat Orchestration Templates (HOT), and Guacamole YAML.
- **Visual Inspector**:
  - Tree view displaying Heat stacks, server VMs, Guacamole connection groups, connection templates, and user permission mappings.
- **Performance Optimizations**:
  - Configurable delays (eliminating unnecessary artificial sleeps during fast runs).
  - Batch retrieval of OpenStack server instances and cached lookups.
- **Backward Compatibility**:
  - Fully compatible with existing YAML configuration files and legacy script flags (`--action full --debug`).

---

## Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- OpenStack clouds configuration in `clouds.yaml` (optional for dry-runs)
- Apache Guacamole database/API credentials (optional for dry-runs)

### Install Package
```bash
# Clone the repository
git clone https://gitlab.com/your-org/range-provisioner.git
cd range-provisioner

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install in editable mode with dependencies
pip install -e .
```

---

## Web Dashboard & REST API

To start the local web application:

```bash
range-provisioner serve --host 127.0.0.1 --port 8000
```

Open your browser at **`http://127.0.0.1:8000`** to access:
- **Dashboard**: High-level metrics, active configurations, and preset range templates.
- **Config Studio**: Upload, edit, and validate `globals.yaml`, `templates/main.yaml`, and `templates/guac.yaml`.
- **Visual Inspector**: Interactive trees showing connection groups, VM instances, connection templates, and user seats.
- **Range Builder**: Form wizard to generate custom ranges (VM counts, RDP/SSH/VNC protocols, student logins, passwords).
- **Execution & Live Logs**: Trigger Dry-Run simulations or live deployments with real-time WebSocket log streaming.
- **Credential Exporter**: Instant CSV or JSON download of student accounts and generated passwords.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Healthcheck and service status |
| `POST` | `/api/auth/login` | Authenticate user & obtain JWT token |
| `GET` | `/api/auth/me` | Current authenticated user profile |
| `GET` | `/api/admin/users` | List all user accounts (Admin only) |
| `POST` | `/api/admin/users` | Create user with role (Admin only) |
| `GET` | `/api/admin/datasources/openstack` | List OpenStack cloud datasources (Admin only) |
| `POST` | `/api/admin/datasources/openstack` | Create OpenStack datasource (replaces clouds.yaml) |
| `POST` | `/api/admin/datasources/openstack/{id}/test` | Test OpenStack connection |
| `GET` | `/api/admin/datasources/guacamole` | List Guacamole datasources (Admin only) |
| `POST` | `/api/admin/datasources/guacamole` | Create Guacamole gateway (replaces clouds.yaml) |
| `POST` | `/api/admin/datasources/guacamole/{id}/test` | Test Guacamole connection |
| `GET` | `/api/ranges` | List saved cyber ranges from SQLite |
| `POST` | `/api/ranges` | Save or update cyber range in SQLite |
| `GET` | `/api/ranges/{id}` | Load complete cyber range configuration |
| `POST` | `/api/heat/validate` | AST validation of OpenStack HOT template, dependency loops, and execution order |
| `POST` | `/api/topology` | Generate interactive D3 graph topology from range parameters |
| `GET` | `/api/ranges/{id}/topology` | Generate D3 topology graph for a saved range in SQLite |
| `POST` | `/api/config/validate` | Validate globals, Heat, and Guacamole templates |
| `POST` | `/api/config/inspect` | Parse and return structured JSON hierarchy |
| `POST` | `/api/config/generate` | Generate YAML templates from parameters |
| `POST` | `/api/config/download-zip` | Export configured range bundle as a ZIP |
| `POST` | `/api/provision/run` | Launch provisioning (dry-run or live) |
| `GET` | `/api/tasks/{task_id}` | Retrieve task status, duration, and logs |
| `GET` | `/api/tasks/{task_id}/users` | Export user credentials as CSV or JSON |
| `WS` | `/api/ws/tasks/{task_id}` | Real-time WebSocket log stream |
| `GET` | `/api/presets` | List predefined cyber range templates |
| `GET` | `/api/live/openstack/stacks` | Fetch live OpenStack Heat stack statuses and telemetry |
| `GET` | `/api/live/openstack/stacks/{id}/resources` | Granular resource inspection (VMs, networks, subnets) |
| `GET` | `/api/live/guacamole/monitoring` | Query active user sessions, session history, and connections |
| `DELETE` | `/api/live/guacamole/active-connections/{id}` | Administratively terminate an active Guacamole user session |


---

## SQLite Database & Authentication

Range Provisioner replaces static `clouds.yaml` files and raw YAML management with a built-in **SQLite database** (`range_provisioner.db`):

- **Default Administrator Account**:
  - Username: `admin`
  - Password: `admin`
- **Role-Based Access Control (RBAC)**:
  - `admin`: Full access to user management, cloud datasources, range configurations, and executions.
  - `operator`: Access to build, simulate, and provision cyber ranges.
  - `viewer`: Read-only access to inspect templates and monitor task execution logs.
- **Dynamic Infrastructure Datasources**:
  - Configure OpenStack Keystone endpoints and Apache Guacamole REST credentials directly in the database.
  - Test connection health with 1-click diagnostics.
  - Provisioning tasks automatically use the default database datasource when `clouds.yaml` is not present.
- **Saved Cyber Ranges**:
  - Save named cyber range environments into SQLite.
  - Operators can load, inspect, or switch environments in Config Studio without needing raw YAML files.
- **API Key Authentication**:
  - Generate named API keys for CI/CD pipelines and external automation.
  - Authenticate using the `X-API-Key` HTTP header.
- **Live Telemetry & Guacamole Monitoring**:
  - Live OpenStack Heat stack statuses (`CREATE_COMPLETE`, `UPDATE_IN_PROGRESS`, etc.), parameters, outputs, and granular resource trees.
  - Real-time Apache Guacamole monitoring: active connected user sessions, session history audit trail, and remote session termination.

---

## Command Line Interface (CLI)

Range Provisioner provides both `range-provisioner` and `provisioner` aliases.

### 1. Validate Configurations
Validate syntax, Jinja expressions, and schema consistency:
```bash
range-provisioner validate --config globals.yaml
```

### 2. Inspect Range Hierarchy
Visually inspect declared Heat stacks, VMs, Guacamole connection groups, and users:
```bash
range-provisioner inspect --config globals.yaml
```

### 3. Dry-Run Simulation
Simulate a deployment without modifying any cloud infrastructure:
```bash
range-provisioner provision --dry-run
```

### 4. Live Provisioning
Deploy resources to OpenStack and Guacamole:
```bash
# Full deployment
range-provisioner provision --target full --action create

# Provision only Heat stacks
range-provisioner provision --target heat --action create

# Provision only Guacamole
range-provisioner provision --target guacamole --action create

# Deprovision / tear down a range
range-provisioner provision --target full --action delete
```

### 5. Export User Credentials
Generate and export student passwords and connection maps to CSV or JSON:
```bash
range-provisioner export-users -o students.csv
range-provisioner export-users -o students.json
```

### 6. Scaffold a New Project
Initialize starter templates in a new directory:
```bash
range-provisioner init --directory ./my-range --org blue-team
```

### 7. Test Cloud Connection
Verify OpenStack or Guacamole connectivity:
```bash
range-provisioner test-connection --cloud openstack --type openstack
range-provisioner test-connection --cloud guacamole --type guacamole
```

### 8. Scheduled Range Provisioning & Deprovisioning
Automate range deployment and teardown on designated schedules:
```bash
# List all scheduled exercise jobs
range-provisioner schedule list

# Schedule automated build and teardown for a range
range-provisioner schedule create \
  --name "SOC Analyst Exercise" \
  --target full \
  --build "2026-10-10 09:00" \
  --delete "2026-10-10 17:00"

# Schedule a dry-run simulation for a saved range in SQLite
range-provisioner schedule create \
  --name "Red Team Simulation" \
  --range-id 1 \
  --dry-run \
  --build "2026-10-12 08:30"

# Cancel pending build or teardown actions
range-provisioner schedule cancel 1 --action all
range-provisioner schedule cancel 1 --action build
range-provisioner schedule cancel 1 --action delete
```

### 9. Legacy Script Invocation
For existing CI/CD pipelines, backward compatibility is fully preserved:
```bash
python src/provisioner.py --action full --debug
python src/provisioner.py --action heat
python src/provisioner.py --action guacamole
```

---

## Configuration Reference

### `globals.yaml`
```yaml
globals:
  debug: false
  artifacts: true
  organization: cyberrange
  amount: 2
  provision: true

guacamole:
  provision: true
  update: false
  cloud: guacamole
  guac_file: templates/guac.yaml
  org_name: cyberrange
  pause: 0.1

heat:
  provision: true
  update: false
  cloud: openstack
  amount: 2
  heat_file: templates/main.yaml
  stack_name: cyberrange
  stack_delay: 5
  pause: 0.1
  jinja: true

swift:
  provision: false
  update: false
  cloud: openstack
  assets_dir: assets
  container_name: cyberrange
```

### `templates/guac.yaml`
```yaml
{% set systems = 2 %}
{% set organization = "cyberrange" %}

stacks:
  - {{ organization }}

groups:
  {{ organization }}:
    parent: ROOT
    attributes:
      max-connections: 10

connectionTemplates:
  {{ organization }}.screen.server:
    parent: {{ organization }}
    pattern: {{ organization }}.screen.server.(\d+)
    protocol: rdp
    parameters:
      port: 3389
      security: any
      ignore-cert: 'true'
      username: student
      password: studentpassword

users:
  {% for system in range(1, systems + 1) %}
  {{ organization }}.user.{{ system }}:
    username: {{ organization }}.screen.{{ system }}
    password: P@ssw0rd{{ system }}!
    permissions:
      connectionPermissions:
        - {{ organization }}.screen.server.{{ system }}
  {% endfor %}
```

---

## Security, Authentication & Admin Settings

### Authentication Gate & Role-Based Access Control (RBAC)
Range Provisioner features a centralized authentication gate requiring users to log in before viewing or configuring any cyber ranges.
- **Roles**:
  - `admin`: Full administrative control over users, datasources, API keys, global system settings, and database maintenance.
  - `operator`: Can build, simulate, inspect, and provision cyber ranges.
  - `viewer`: Read-only inspection of cyber ranges and topologies.
- **Default Administrator**: `admin` / `admin` (change immediately in production).

### REST API Keys & Automation Tokens
Generate programmatic, headless access tokens in **Admin Settings > API Keys**:
- Raw secret keys start with `rp_live_` and are displayed only once upon generation.
- Tokens are hashed with **SHA-256** prior to SQLite storage.
- Authenticate requests by passing either:
  ```bash
  curl -H "X-API-Key: rp_live_xxxxxxxx..." http://localhost:8000/api/ranges
  ```
  or standard Bearer authorization:
  ```bash
  curl -H "Authorization: Bearer rp_live_xxxxxxxx..." http://localhost:8000/api/ranges
  ```

### Global System Settings & Maintenance
Configure platform-wide defaults and operations directly from the browser:
- **Provisioning Defaults**: Default remote protocol (`rdp`, `ssh`, `vnc`), default port, student credentials, stack stagger delays, and auto-Swift options.
- **Security Policies**: JWT token lifetime (hours), login requirement toggles, and rate limiting.
- **Webhook Alerts**: Dispatches test alerts and execution status events to Slack, Discord, Microsoft Teams, or custom HTTP endpoints.
- **SQLite Operations**: Perform online database compaction (`VACUUM;`) and view real-time diagnostics.

---

## Running Tests

Run the full automated test suite with coverage:
```bash
pytest --cov=src tests/
```

