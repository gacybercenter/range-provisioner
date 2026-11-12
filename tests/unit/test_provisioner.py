import unittest
from unittest.mock import Mock, patch

from provisioner import main, parse_args


class TestProvisionerArguments(unittest.TestCase):
    def test_parse_supported_action(self):
        args = parse_args(['heat', '--debug', '--dry-run'])

        self.assertEqual(args.action, 'heat')
        self.assertTrue(args.debug)
        self.assertTrue(args.dry_run)

    def test_reject_unsupported_action(self):
        with self.assertRaises(SystemExit):
            parse_args(['invalid'])

    def test_cli_dispatches_selected_range_and_dry_run(self):
        config = {
            'globals': {'debug': False},
            'swift': {},
            'heat': {'cloud': 'openstack', 'heat_file': 'main.yaml',
                     'env_file': 'env.yaml'},
            'guacamole': {'guac_file': 'guac.yaml'},
        }
        clouds = {'clouds': {'openstack': {}}}
        connection = Mock()
        with patch('provisioner.load_template.load_template',
                   side_effect=[config, clouds]), \
             patch('provisioner.ranges.apply_range', return_value=config) as apply_range, \
             patch('provisioner.connections.openstack_connection',
                   return_value=connection), \
             patch('provisioner.heat.provision') as provision:
            main(['heat', '--range', 'training', '--dry-run'])

        apply_range.assert_called_once_with(config, 'training', 'templates/ranges.yaml')
        provision.assert_called_once_with(connection, config['globals'], config['heat'],
                                          False, True)


if __name__ == '__main__':
    unittest.main()
