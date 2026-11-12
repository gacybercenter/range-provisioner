#!/usr/bin/env python3
"""
Range Provisioner

Provisioning and deprovisioning for swift, heat, and guacamole
"""


import sys
import time
import traceback
import argparse
from typing import Dict, Any
from provision import heat, swift, guac
from utils import connections, load_template, msg_format, ranges


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Range Provisioner CLI')
    parser.add_argument(
        'action',
        choices=['swift', 'heat', 'guacamole', 'full'],
        help='Provisioning action to run'
    )
    parser.add_argument('--debug', help="Enable debug mode", action='store_true')
    parser.add_argument('--range', help="Select a named range from ranges.yaml")
    parser.add_argument(
        '--ranges-file',
        help="Range definitions file (default: templates/ranges.yaml)"
    )
    parser.add_argument(
        '--dry-run',
        help="Inspect the requested changes without applying them",
        action='store_true'
    )
    args = parser.parse_args(argv)
    if args.range is not None and not args.range.strip():
        parser.error('--range must not be empty')
    if args.ranges_file is not None and not args.range:
        parser.error('--ranges-file requires --range')
    if args.ranges_file is not None and not args.ranges_file.strip():
        parser.error('--ranges-file must not be empty')
    return args


def main(argv: list[str] | None = None) -> None:
    """
    The main function that handles the provisioning process based on command line arguments.

    Parameters:
    None

    Returns:
    None
    """

    start_time = time.time()
    endpoint = 'Pipeline'

    try:
        msg_format.general_msg("Starting Range Provisioner...", endpoint)    
        args = parse_args(argv)
        arg = args.action

        globals_vars = load_template.load_template("globals.yaml")
        if args.range is not None:
            globals_vars = ranges.apply_range(
                globals_vars, args.range, args.ranges_file or 'templates/ranges.yaml'
            )
        globals_dict: Dict[str, Any] = globals_vars['globals']
        swift_globals: Dict[str, Any] = globals_vars['swift']
        heat_globals: Dict[str, Any] = globals_vars['heat']
        guacamole_globals: Dict[str, Any] = globals_vars['guacamole']

        debug: bool = args.debug or globals_dict['debug']
        heat_file = heat_globals.get('heat_file')
        guac_file = guacamole_globals.get('guac_file')

        # Backwards Compatibility
        if not heat_file:
            heat_file = heat_globals['template_dir'] + '/main.yaml'
            heat_globals['heat_file'] = heat_file
        if not guac_file:
            guac_file = guacamole_globals['user_dir'] + '/guac.yaml'
            guacamole_globals['guac_file'] = guac_file

        clouds = load_template.load_template('clouds.yaml')['clouds']

        try:
            openstack_clouds = clouds[heat_globals['cloud']]
        except KeyError as err:
            raise KeyError(
                f"Cloud '{heat_globals['cloud']}' not found in clouds.yaml") from err

        openstack_connect = connections.openstack_connection(heat_globals['cloud'],
                                                             openstack_clouds,
                                                             debug)

        if arg in ["full", "guacamole"]:
            try:
                guacamole_clouds = clouds[guacamole_globals['cloud']]
            except KeyError as err:
                raise KeyError(
                    f"Cloud '{guacamole_globals['cloud']}' not found in clouds.yaml") from err
            guacamole_connect = connections.guacamole_connection(guacamole_globals['cloud'],
                                                                 guacamole_clouds,
                                                                 debug)
        else:
            guacamole_connect = None

        if arg == "swift":
            swift.provision(openstack_connect,
                            globals_dict,
                            swift_globals,
                            debug,
                            args.dry_run)
        elif arg == "heat":
            heat.provision(openstack_connect,
                           globals_dict,
                           heat_globals,
                           debug,
                           args.dry_run)
        elif arg == "guacamole":
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals_dict,
                           guacamole_globals,
                           debug,
                           args.dry_run)
        elif arg == "full":
            swift.provision(openstack_connect,
                            globals_dict,
                            swift_globals,
                            debug,
                            args.dry_run)
            heat.provision(openstack_connect,
                           globals_dict,
                           heat_globals,
                           debug,
                           args.dry_run)
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals_dict,
                           guacamole_globals,
                           debug,
                           args.dry_run)

        if args.dry_run:
            msg_format.success_msg("Dry run complete; no changes were applied.",
                                   endpoint)
            return

    except Exception as error:
        msg_format.error_msg(f"{error}\n\n {traceback.format_exc()}",
                             endpoint)
        sys.exit(1)

    msg_format.success_msg("Provisioning complete.",
                           endpoint)

    end_time = time.time()
    msg_format.general_msg(f"Total time: {end_time - start_time:.2f} seconds",
                           endpoint)

    sys.exit(0)


if __name__ == '__main__':
    main()
