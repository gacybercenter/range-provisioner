import unittest
from src.utils.generate import (generate_password, generate_names,
                                generate_instance_names, generate_conns)

class TestGenerate(unittest.TestCase):
    """
    Test the generate.py functions.
    """
    def test_generate_password(self):
        """
        Test the generate_password function to ensure it returns a password
        of length 16 containing only alphanumeric characters.
        """
        password = generate_password()
        self.assertEqual(len(password), 16)
        self.assertTrue(all(c.isalnum() for c in password))

    def test_generate_names(self):
        """
        Test the generate_names function for a single range
        and multiple ranges.
        """

        test_cases = [
            {
                'ranges': 1,
                'prefix': 'test',
                'expected_names': ['test']
            },
            {
                'ranges': 2,
                'prefix': 'test',
                'expected_names': ['test.1', 'test.2']
            }
        ]

        for test_case in test_cases:
            range_names = generate_names(test_case['ranges'],
                                         test_case['prefix'])
            self.assertEqual(range_names, test_case['expected_names'])


    def test_generate_instance_names(self):
        """
        Test the generate_instance_names function with different combinations of num_users.
        """

        test_range_name = 'range'
        test_user_name = 'user'
        test_cases = [
            {
                'num_ranges': 1,
                'num_users': 1,
                'expected_names': [
                    'range.user'
                ]
            },
            {
                'num_ranges': 1,
                'num_users': 2,
                'expected_names': [
                    'range.user.1',
                    'range.user.2'
                ]
            },
            {
                'num_ranges': 2,
                'num_users': 1,
                'expected_names': [
                    'range.1.user',
                    'range.2.user'
                ]
            },
            {
                'num_ranges': 2,
                'num_users': 2,
                'expected_names': [
                    'range.1.user.1',
                    'range.1.user.2',
                    'range.2.user.1',
                    'range.2.user.2'
                ]
            }
        ]

        for test_case in test_cases:
            instance_names = generate_instance_names(test_range_name,
                                                     test_case['num_ranges'],
                                                     test_user_name,
                                                     test_case['num_users'])
            self.assertEqual(instance_names, test_case['expected_names'])


    def test_generate_conns(self):
        """
        Test the generation of connections with the given parameters.
        """

        params = {}
        guac_params = {
            'org_name': 'test_org',
            'new_groups': [
                'range.1',
                'range.2',
            ],
            'instances': [
                {
                    'name': 'test_instance',
                    'hostname': '1.1.1.1'
                }
            ],
            'recording': True,
            'sharing': 'read',
            'protocol': 'rdp',
            'username': 'user',
            'password': 'pass',
            'domain_name': 'domain'
        }

        result = generate_conns(params, guac_params, True)
        self.assertIsNot({}, result)


if __name__ == '__main__':
    unittest.main()
