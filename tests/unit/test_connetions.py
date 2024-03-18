"""

"""

import unittest
from unittest.mock import patch, MagicMock
from src.utils.connections import openstack_connection, guacamole_connection

class TestConnections(unittest.TestCase):
    """
    Tests the OpenStack and Guacamole connectionss.
    """
    @patch('src.utils.connections.connect')
    @patch('src.utils.connections.general_msg')
    @patch('src.utils.connections.info_msg')
    @patch('src.utils.connections.success_msg')
    @patch('src.utils.connections.error_msg')
    def test_openstack_connection_successful(self,
                                             mock_error_msg,
                                             mock_success_msg,
                                             mock_info_msg,
                                             mock_general_msg,
                                             mock_connect):
        """
        Test for successful openstack connection.

        Args:
            self: the object itself
            mock_error_msg: MagicMock for error message patch
            mock_success_msg: MagicMock for success message patch
            mock_info_msg: MagicMock for info message patch
            mock_general_msg: MagicMock for general message patch
            mock_connect: MagicMock for connect patch

        Returns:
            None
        """
        mock_connect.return_value = MagicMock()

        cloud = 'test_cloud'
        openstack_clouds = {
            'auth': {
                'auth_url': 'http://example.com'
            }
        }
        debug = True

        result = openstack_connection(cloud, openstack_clouds, debug)

        self.assertEqual(result, mock_connect.return_value)
        mock_general_msg.assert_called_once()
        mock_success_msg.assert_called_once()
        mock_info_msg.assert_called_once()
        mock_error_msg.assert_not_called()

    @patch('src.utils.connections.connect')
    @patch('src.utils.connections.general_msg')
    @patch('src.utils.connections.info_msg')
    @patch('src.utils.connections.success_msg')
    @patch('src.utils.connections.error_msg')
    def test_openstack_connection_failure(self,
                                          mock_error_msg,
                                          mock_success_msg,
                                          mock_info_msg,
                                          mock_general_msg,
                                          mock_connect):
        """
        Test for unsuccessful openstack connection.

        Args:
            self: the object itself
            mock_error_msg: MagicMock for error message patch
            mock_success_msg: MagicMock for success message patch
            mock_info_msg: MagicMock for info message patch
            mock_general_msg: MagicMock for general message patch
            mock_connect: MagicMock for connect patch

        Returns:
            None
        """
        mock_connect.return_value = None

        cloud = 'test_cloud'
        openstack_clouds = {
            'auth': {
                'auth_url': 'http://example.com'
            }
        }
        debug = True

        result = openstack_connection(cloud, openstack_clouds, debug)

        self.assertEqual(result, mock_connect.return_value)
        mock_general_msg.assert_called_once()
        mock_error_msg.assert_called_once()
        mock_success_msg.assert_not_called()
        mock_info_msg.assert_not_called()

    @patch('src.utils.connections.session')
    @patch('src.utils.connections.general_msg')
    @patch('src.utils.connections.info_msg')
    @patch('src.utils.connections.success_msg')
    @patch('src.utils.connections.error_msg')
    def test_guacamole_connection_successful(self,
                                             mock_error_msg,
                                             mock_success_msg,
                                             mock_info_msg,
                                             mock_general_msg,
                                             mock_session):
        """
        Test for successful guacamole connection.

        Args:
            self: the object itself
            mock_error_msg: MagicMock for error message patch
            mock_success_msg: MagicMock for success message patch
            mock_info_msg: MagicMock for info message patch
            mock_general_msg: MagicMock for general message patch
            mock_connect: MagicMock for connect patch

        Returns:
            None
        """
        mock_session.return_value = MagicMock()

        cloud = 'test_cloud'
        guacamole_clouds = {
            'host': 'guacamole.example.com',
            'data_source': 'mysql',
            'username': 'user',
            'password': 'pass'
        }
        debug = True

        result = guacamole_connection(cloud, guacamole_clouds, debug)

        self.assertEqual(result, mock_session.return_value)
        mock_general_msg.assert_called_once()
        mock_success_msg.assert_called_once()
        mock_error_msg.assert_not_called()
        mock_info_msg.assert_called_once()

    @patch('src.utils.connections.session')
    @patch('src.utils.connections.general_msg')
    @patch('src.utils.connections.info_msg')
    @patch('src.utils.connections.success_msg')
    @patch('src.utils.connections.error_msg')
    def test_guacamole_connection_failure(self,
                                          mock_error_msg,
                                          mock_success_msg,
                                          mock_info_msg,
                                          mock_general_msg,
                                          mock_session):
        """
        Test for successful openstack connection.

        Args:
            self: the object itself
            mock_error_msg: MagicMock for error message patch
            mock_success_msg: MagicMock for success message patch
            mock_info_msg: MagicMock for info message patch
            mock_general_msg: MagicMock for general message patch
            mock_connect: MagicMock for connect patch

        Returns:
            None
        """
        mock_session.return_value = None

        cloud = 'test_cloud'
        guacamole_clouds = {
            'host': 'guacamole.example.com',
            'data_source': 'mysql',
            'username': 'user',
            'password': 'pass'
        }
        debug = True

        result = guacamole_connection(cloud, guacamole_clouds, debug)

        self.assertEqual(result, mock_session.return_value)
        mock_general_msg.assert_called_once()
        mock_error_msg.assert_called_once()
        mock_success_msg.assert_not_called()
        mock_info_msg.assert_not_called()

if __name__ == '__main__':
    unittest.main()
