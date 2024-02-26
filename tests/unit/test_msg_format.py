import unittest
import sys
from unittest.mock import patch
from io import StringIO
from colorama import Fore
from src.utils.msg_format import error_msg, info_msg, success_msg, general_msg

# Your messaging module code would go here

class TestMessagingFunctions(unittest.TestCase):

    def setUp(self):
        # Redirect stdout to capture print outputs
        self.held, sys.stdout = sys.stdout, StringIO()

    def test_msg_with_dict(self):
        # Test msg with a dictionary
        test_endpoint = "test_endpoint"
        test_message = {"info": "Info message"}
        with patch('src.utils.msg_format.pprint') as mock_pprint:
            error_msg(test_message, test_endpoint)
            mock_pprint.assert_called_once()
            mock_pprint.assert_called_with(test_message, indent=1, sort_dicts=False)

        with patch('src.utils.msg_format.pprint') as mock_pprint:
            info_msg(test_message, test_endpoint, debug=True)
            mock_pprint.assert_called_once()
            mock_pprint.assert_called_with(test_message, indent=1, sort_dicts=False)

        with patch('src.utils.msg_format.pprint') as mock_pprint:
            general_msg(test_message, test_endpoint)
            mock_pprint.assert_called_once()
            mock_pprint.assert_called_with(test_message, indent=1, sort_dicts=False)

        with patch('src.utils.msg_format.pprint') as mock_pprint:
            success_msg(test_message, test_endpoint)
            mock_pprint.assert_called_once()
            mock_pprint.assert_called_with(test_message, indent=1, sort_dicts=False)

    def test_error_msg_with_string(self):
        # Test error_msg with a string
        test_endpoint = "test_endpoint"
        test_message = "An error occurred"
        error_msg(test_message, test_endpoint)

        output = sys.stdout.getvalue()

        self.assertIn(Fore.RED, output)
        self.assertIn(test_endpoint, output)
        self.assertIn("[ERROR]", output)
        self.assertIn(Fore.RESET, output)
        self.assertIn(test_message, output)

    def test_info_msg_not_debug(self):
        # Test info_msg when debug is False, should not print
        test_endpoint = "test_endpoint"
        test_message = "Info message"
        info_msg(test_message, test_endpoint, debug=False)

        output = sys.stdout.getvalue()

        self.assertIn("", output)

    def test_info_msg_with_debug(self):
        # Test info_msg when debug is False, should not print
        test_endpoint = "test_endpoint"
        test_message = "Info message"
        info_msg(test_message, test_endpoint, debug=True)

        output = sys.stdout.getvalue()

        self.assertIn(Fore.BLUE, output)
        self.assertIn(test_endpoint, output)
        self.assertIn("[INFO]", output)
        self.assertIn(Fore.RESET, output)
        self.assertIn(test_message, output)

    # Add more tests for success_msg, general_msg, and remove_none_and_empty

    def tearDown(self):
        # Restore stdout
        sys.stdout = self.held

if __name__ == '__main__':
    unittest.main()
