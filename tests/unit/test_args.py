# import unittest
# from unittest.mock import patch, MagicMock
# from src.provisioner import main  # Replace 'src.provisioner' with the actual name of your module

# class TestMainFunction(unittest.TestCase):

#     @patch('src.provisioner.msg_format')
#     @patch('src.provisioner.sys.argv', ['script_name', 'swift'])
#     def test_main_with_swift_argument(self, mock_msg_format):
#         # Call the main function and check the expected calls on msg_format
#         main()
#         mock_msg_format.error_msg.assert_not_called()
#         mock_msg_format.success_msg.assert_called_once_with("Provisioning complete.", 'Pipeline')

#     @patch('src.provisioner.msg_format')
#     @patch('src.provisioner.sys.argv', ['script_name', 'heat'])
#     def test_main_with_heat_argument(self, mock_msg_format):
#         # Call the main function and check the expected calls on msg_format
#         main()
#         mock_msg_format.error_msg.assert_not_called()
#         mock_msg_format.success_msg.assert_called_once_with("Provisioning complete.", 'Pipeline')

#     @patch('src.provisioner.msg_format')
#     @patch('src.provisioner.sys.argv', ['script_name', 'guacamole'])
#     def test_main_with_guacamole_argument(self, mock_msg_format):
#         # Call the main function and check the expected calls on msg_format
#         main()
#         mock_msg_format.error_msg.assert_not_called()
#         mock_msg_format.success_msg.assert_called_once_with("Provisioning complete.", 'Pipeline')

#     @patch('src.provisioner.msg_format')
#     @patch('src.provisioner.sys.argv', ['script_name', 'full'])
#     def test_main_with_full_argument(self, mock_msg_format):
#         # Call the main function and check the expected calls on msg_format
#         main()
#         mock_msg_format.error_msg.assert_not_called()
#         mock_msg_format.success_msg.assert_called_once_with("Provisioning complete.", 'Pipeline')

#     @patch('src.provisioner.msg_format')
#     @patch('src.provisioner.sys.argv', ['script_name'])
#     def test_main_with_no_arguments(self, mock_msg_format):
#         # Call the main function and check the expected calls on msg_format
#         main()
#         mock_msg_format.error_msg.assert_called_once_with("No arguments provided.", 'Pipeline')

#     @patch('src.provisioner.msg_format')
#     @patch('src.provisioner.sys.argv', ['script_name', 'invalid'])
#     def test_main_with_invalid_argument(self, mock_msg_format):
#         # Call the main function and check the expected calls on msg_format
#         main()
#         mock_msg_format.error_msg.assert_called_once_with("'invalid' is an invalid arguement.", 'Pipeline')

# if __name__ == '__main__':
#     unittest.main()
