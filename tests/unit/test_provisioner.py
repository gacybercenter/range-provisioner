import unittest

from provisioner import parse_args


class TestProvisionerArguments(unittest.TestCase):
    def test_parse_supported_action(self):
        args = parse_args(['heat', '--debug', '--dry-run'])

        self.assertEqual(args.action, 'heat')
        self.assertTrue(args.debug)
        self.assertTrue(args.dry_run)

    def test_reject_unsupported_action(self):
        with self.assertRaises(SystemExit):
            parse_args(['invalid'])


if __name__ == '__main__':
    unittest.main()
