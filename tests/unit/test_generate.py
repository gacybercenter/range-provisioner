import unittest
from unittest.mock import patch
from src.utils.generate import (
    generate_names,
    read_multi_stack_environment,
    update_heat_params,
)

class TestGenerate(unittest.TestCase):
    """
    Test the generate.py functions.
    """
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

    def test_generate_names_rejects_non_positive_range_count(self):
        with self.assertRaises(ValueError):
            generate_names(0, 'test')

    def test_multi_stack_environment_is_read_at_call_time(self):
        with patch.dict('os.environ', {'num_ranges': '2', 'org_name': 'team'}):
            settings = read_multi_stack_environment()

        self.assertEqual(settings['num_ranges'], 2)
        self.assertEqual(settings['org_name'], 'team')

    def test_multi_stack_environment_rejects_invalid_range_count(self):
        with patch.dict('os.environ', {'num_ranges': 'invalid'}):
            with self.assertRaisesRegex(ValueError, 'positive integer'):
                read_multi_stack_environment()

    def test_update_heat_params_uses_multi_stack_environment(self):
        with patch.dict(
            'os.environ',
            {'num_ranges': '2', 'domain_name': 'range.example'},
            clear=True
        ):
            result = update_heat_params(
                {'parameters': [{'domain_name': 'configured.example'}]},
                {'domain_name': {'default': 'default.example'}}
            )

        self.assertEqual(result['domain_name'], 'range.example')

    def test_update_heat_params_requires_multi_stack_values(self):
        with patch.dict('os.environ', {'num_ranges': '2'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'domain_name'):
                update_heat_params(
                    {'parameters': [{'domain_name': 'configured.example'}]},
                    {'domain_name': {'default': 'default.example'}}
                )

    def test_update_heat_params_rejects_unknown_parameter(self):
        with self.assertRaisesRegex(ValueError, 'not found'):
            update_heat_params(
                {'parameters': [{'missing': 'value'}]},
                {'known': {'default': 'default'}}
            )

    def test_update_heat_params_accepts_parameter_without_default(self):
        result = update_heat_params(
            {'parameters': [{'required': 'configured'}]},
            {'required': {'type': 'string'}}
        )

        self.assertEqual(result['required'], 'configured')

    def test_update_heat_params_preserves_order_and_single_range_values(self):
        definitions = {
            'domain_name': {'default': 'default.example'},
            'count': {'default': 1},
        }
        with patch.dict(
            'os.environ',
            {'num_ranges': '1', 'domain_name': 'environment.example'},
            clear=True,
        ):
            result = update_heat_params(
                {'parameters': [
                    {'domain_name': 'configured.example', 'count': 2},
                    {'count': 3},
                ]},
                definitions,
            )

        self.assertEqual(result, {'domain_name': 'configured.example', 'count': 3})
        self.assertEqual(definitions['count'], {'default': 1})


if __name__ == '__main__':
    unittest.main()
