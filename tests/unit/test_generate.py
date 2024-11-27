import unittest
from src.utils.generate import generate_names

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


if __name__ == '__main__':
    unittest.main()
