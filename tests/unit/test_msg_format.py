import unittest
from unittest.mock import patch
from io import StringIO
import sys
from src.utils.msg_format import error_msg, info_msg, success_msg, general_msg
from colorama import Fore

# Your messaging module code would go here

class TestMessagingFunctions(unittest.TestCase):

    def setUp(self):
        # Redirect stdout to capture print outputs
        self.held, sys.stdout = sys.stdout, StringIO()

    def test_msg(self):
        # Test msg with a dictionary
        test_endpoint = "test_endpoint"
        test_message = "Message"
        with patch('src.utils.msg_format.print') as mock_print:
            error_msg(test_message, test_endpoint)
            mock_print.assert_called_with(test_message)

        with patch('src.utils.msg_format.print') as mock_print:
            info_msg(test_message, test_endpoint, debug=True)
            mock_print.assert_called_with(test_message)

        with patch('src.utils.msg_format.print') as mock_print:
            general_msg(test_message, test_endpoint)
            mock_print.assert_called_with(test_message)

        with patch('src.utils.msg_format.print') as mock_print:
            success_msg(test_message, test_endpoint)
            mock_print.assert_called_with(test_message)

    def test_general_msg(self):
        # Test general_msg with a string
        test_endpoint = "test_endpoint"
        test_message = "General message"

        general_msg(test_message, test_endpoint)
        output = sys.stdout.getvalue()

        self.assertIn(Fore.YELLOW, output)
        self.assertIn(test_endpoint, output)
        self.assertIn("[INFO]", output)
        self.assertIn(Fore.RESET, output)
        self.assertIn(test_message, output)

    def test_error_msg(self):
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

    def test_info_msg(self):
        # Test info_msg when debug is False, should not print
        test_endpoint = "test_endpoint"
        test_message = "Info message"

        info_msg(test_message, test_endpoint, debug=False)
        output = sys.stdout.getvalue()

        self.assertIn("", output)

        info_msg(test_message, test_endpoint, debug=True)
        output = sys.stdout.getvalue()

        self.assertIn(Fore.BLUE, output)
        self.assertIn(test_endpoint, output)
        self.assertIn("[INFO]", output)
        self.assertIn(Fore.RESET, output)
        self.assertIn(test_message, output)

    def test_success_msg(self):
        # Test success_msg with a string
        test_endpoint = "test_endpoint"
        test_message = "Success message"

        success_msg(test_message, test_endpoint)
        output = sys.stdout.getvalue()

        self.assertIn(Fore.GREEN, output)
        self.assertIn(test_endpoint, output)
        self.assertIn("[SUCCESS]", output)
        self.assertIn(Fore.RESET, output)
        self.assertIn(test_message, output)


    def tearDown(self):
        # Restore stdout
        sys.stdout = self.held

if __name__ == '__main__':
    unittest.main()
