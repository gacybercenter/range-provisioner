#!/usr/bin/env python3
"""
Range Provisioner Main Entry Point.
Maintains backward compatibility with legacy scripts while exposing new features.
"""
import sys
import argparse

try:
    from src.provision.engine import ProvisionEngine
    from src.cli import cli
except ImportError:
    from provision.engine import ProvisionEngine
    from cli import cli


def legacy_main() -> None:
    """Legacy entry point handler supporting --action and --debug flags."""
    parser = argparse.ArgumentParser(description="Range Provisioner CLI")
    parser.add_argument(
        "--action",
        choices=["swift", "heat", "guacamole", "full"],
        default=None,
        help="Provision target: swift, heat, guacamole, or full"
    )
    parser.add_argument(
        "--mode",
        choices=["create", "update", "delete"],
        default="create",
        help="Action mode: create, update, or delete"
    )
    parser.add_argument("--dry-run", action="store_true", default=False, help="Simulate execution")
    parser.add_argument("--debug", action="store_true", default=False, help="Enable debug logging")

    # If subcommands are passed or no args, delegate to Click CLI
    if len(sys.argv) > 1 and sys.argv[1] in ["provision", "validate", "inspect", "export-users", "init", "test-connection", "serve", "--help", "-h"]:
        cli()
        return

    args = parser.parse_args()

    if not args.action:
        # Default to interactive CLI help if no arguments are given
        cli()
        return

    engine = ProvisionEngine(debug=args.debug, dry_run=args.dry_run)
    result = engine.run(target=args.action, action=args.mode)

    if not result.success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    legacy_main()
