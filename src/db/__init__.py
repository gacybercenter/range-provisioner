"""
Database package for Range Provisioner.
"""
from .database import engine, SessionLocal, Base, get_db
from .models import User, OpenStackDataSource, GuacamoleDataSource, SavedRange, ApiKey, SystemSetting, ScheduledJob
from .security import hash_password, verify_password, create_access_token, get_current_user, require_user, require_admin


def init_db():
    """Create database tables and seed initial admin account if not present."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                hashed_password=hash_password("admin"),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()

        # Migrate missing columns in saved_ranges if table already existed
        from sqlalchemy import text
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(saved_ranges)")).fetchall()]
            if "users_per_system" not in cols:
                conn.execute(text("ALTER TABLE saved_ranges ADD COLUMN users_per_system INTEGER DEFAULT 2"))
            if "protocol" not in cols:
                conn.execute(text("ALTER TABLE saved_ranges ADD COLUMN protocol VARCHAR(32) DEFAULT 'rdp'"))
            if "port" not in cols:
                conn.execute(text("ALTER TABLE saved_ranges ADD COLUMN port INTEGER DEFAULT 3389"))
            if "student_user" not in cols:
                conn.execute(text("ALTER TABLE saved_ranges ADD COLUMN student_user VARCHAR(64) DEFAULT 'student'"))
            if "student_pass" not in cols:
                conn.execute(text("ALTER TABLE saved_ranges ADD COLUMN student_pass VARCHAR(64) DEFAULT 'RangeP@ss123!'"))
            if "enable_swift" not in cols:
                conn.execute(text("ALTER TABLE saved_ranges ADD COLUMN enable_swift BOOLEAN DEFAULT 0"))
            if "config_json" not in cols:
                conn.execute(text("ALTER TABLE saved_ranges ADD COLUMN config_json TEXT"))
            conn.commit()

        # Seed initial cyber ranges into SQLite if none exist
        if db.query(SavedRange).count() == 0:
            starter_hot = """heat_template_version: 2018-03-02
description: Cyber Range Exercise Deployment

parameters:
  username:
    type: string
    default: rangeuser
  password:
    type: string
    default: RangeP@ss123!

resources:
  range_network:
    type: OS::Neutron::Net
    properties:
      name: range_exercise_net

  range_subnet:
    type: OS::Neutron::Subnet
    properties:
      network_id: { get_resource: range_network }
      cidr: 10.10.10.0/24
      dns_nameservers: [8.8.8.8, 1.1.1.1]

  workstation_1:
    type: OS::Nova::Server
    properties:
      name: workstation.alpha
      image: ubuntu-22.04
      flavor: m1.medium
      networks:
        - network: { get_resource: range_network }

  workstation_2:
    type: OS::Nova::Server
    properties:
      name: workstation.bravo
      image: kali-linux
      flavor: m1.large
      networks:
        - network: { get_resource: range_network }

outputs:
  network_id:
    description: Primary network identifier
    value: { get_resource: range_network }
"""
            default_ranges = [
                SavedRange(
                    name="Kali Linux Penetration Testing Range",
                    organization="pentest",
                    description="2 attacking systems with dedicated RDP GUI connections and isolated target subnet.",
                    stack_count=2,
                    users_per_system=2,
                    protocol="rdp",
                    port=3389,
                    student_user="kali",
                    student_pass="kali",
                    enable_swift=False,
                    heat_yaml=starter_hot,
                    globals_yaml="",
                    guac_yaml="",
                    config_json="{}",
                ),
                SavedRange(
                    name="SOC Analyst Defensive Range",
                    organization="socdefense",
                    description="Defensive monitoring environment with analyst workstations, SIEM dashboards, and RDP access.",
                    stack_count=1,
                    users_per_system=4,
                    protocol="rdp",
                    port=3389,
                    student_user="analyst",
                    student_pass="DefendTheRange2026!",
                    enable_swift=True,
                    heat_yaml=starter_hot,
                    globals_yaml="",
                    guac_yaml="",
                    config_json="{}",
                ),
                SavedRange(
                    name="CTF Competition Blue/Red Team",
                    organization="ctfchallenge",
                    description="Multi-team competitive cyber range with 4 isolated student stacks and terminal SSH scoring.",
                    stack_count=4,
                    users_per_system=2,
                    protocol="ssh",
                    port=22,
                    student_user="competitor",
                    student_pass="CTF@2026Challenge!",
                    enable_swift=False,
                    heat_yaml=starter_hot,
                    globals_yaml="",
                    guac_yaml="",
                    config_json="{}",
                ),
            ]
            for r in default_ranges:
                db.add(r)
            db.commit()

        # Seed initial OpenStack and Guacamole datasources if none exist
        if db.query(OpenStackDataSource).count() == 0:
            default_os = OpenStackDataSource(
                name="Default OpenStack",
                auth_url="http://openstack.local:5000/v3",
                username="admin",
                password="password",
                project_name="admin",
                user_domain_name="Default",
                project_domain_name="Default",
                is_default=True,
            )
            db.add(default_os)
            db.commit()

        if db.query(GuacamoleDataSource).count() == 0:
            default_guac = GuacamoleDataSource(
                name="Default Guacamole",
                host="http://guacamole.local:8080/guacamole",
                data_source="mysql",
                username="guacadmin",
                password="guacadmin",
                is_default=True,
            )
            db.add(default_guac)
            db.commit()

        # Seed global system settings
        if db.query(SystemSetting).count() == 0:
            default_settings = [
                SystemSetting(key="site_title", value="Range Provisioner Studio", category="general", description="Application branding and title header"),
                SystemSetting(key="default_organization", value="cyberrange", category="general", description="Default organization slug for new stacks"),
                SystemSetting(key="default_stack_count", value="2", category="general", description="Default stack count for ranges"),
                SystemSetting(key="default_users_per_system", value="2", category="general", description="Default user accounts allocated per VM instance"),
                SystemSetting(key="default_protocol", value="rdp", category="provisioning", description="Default remote display protocol (rdp, ssh, vnc)"),
                SystemSetting(key="default_port", value="3389", category="provisioning", description="Default remote port"),
                SystemSetting(key="default_student_user", value="student", category="provisioning", description="Default initial VM username"),
                SystemSetting(key="default_student_pass", value="RangeP@ss123!", category="provisioning", description="Default initial student password"),
                SystemSetting(key="default_stack_delay", value="5", category="provisioning", description="Delay between individual Heat stack builds (seconds)"),
                SystemSetting(key="default_pause", value="0.1", category="provisioning", description="Rate limiting pause between API requests (seconds)"),
                SystemSetting(key="auto_enable_swift", value="false", category="provisioning", description="Default Swift object storage container state"),
                SystemSetting(key="dry_run_default", value="true", category="provisioning", description="Default to dry-run simulation mode"),
                SystemSetting(key="token_expire_hours", value="24", category="security", description="Session JWT token expiration lifetime in hours"),
                SystemSetting(key="require_login_to_view", value="true", category="security", description="Require authentication before accessing any views"),
                SystemSetting(key="rate_limit_per_minute", value="120", category="security", description="Maximum requests per minute per IP or API key"),
                SystemSetting(key="webhook_url", value="", category="notifications", description="HTTP webhook endpoint for provisioning completion alerts"),
                SystemSetting(key="notify_on_complete", value="false", category="notifications", description="Send webhook notification on successful deployment"),
                SystemSetting(key="notify_on_failure", value="true", category="notifications", description="Send webhook notification on deployment errors"),
            ]
            for s in default_settings:
                db.add(s)
            db.commit()
    finally:
        db.close()


__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "User",
    "OpenStackDataSource",
    "GuacamoleDataSource",
    "SavedRange",
    "ApiKey",
    "SystemSetting",
    "ScheduledJob",
    "hash_password",
    "verify_password",
    "create_access_token",
    "get_current_user",
    "require_user",
    "require_admin",
]

