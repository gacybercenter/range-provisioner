import unittest
from unittest.mock import Mock, patch
from guacamole import session
from src.objects.connections import Connection

class TestConnection(unittest.TestCase):

    def setUp(self):
        self.mock_gconn = Mock(session)
        self.connection = Connection(
            gconn=self.mock_gconn,
            name='TestConnection',
            parent_identifier='ROOT',
            identifier=None,
            debug=False
        )

    def test_init(self):
        self.assertEqual(self.connection.name, 'TestConnection')
        self.assertEqual(self.connection.parent_identifier, 'ROOT')
        self.assertIsNone(self.connection.identifier)
        self.assertFalse(self.connection.debug)

    def test_eq(self):
        other = Connection(
            gconn=self.mock_gconn,
            name='TestConnection',
            parent_identifier='ROOT',
            identifier=None,
            debug=False
        )
        self.assertEqual(self.connection, other)

    def test_not_implemented_methods(self):
        with self.assertRaises(NotImplementedError):
            self.connection._create_connection()
        with self.assertRaises(NotImplementedError):
            self.connection._delete_connection()
        with self.assertRaises(NotImplementedError):
            self.connection._update_connection()
        with self.assertRaises(NotImplementedError):
            self.connection.detail()

    @patch('src.objects.connections.sleep')
    @patch('src.objects.connections.Connection._create_connection')
    def test_create(self, mock_create_connection: Mock, mock_sleep: Mock):
        test_delay = 0.1
        result = self.connection.create(test_delay)
        self.assertIsNotNone(result)
        mock_create_connection.assert_called_once()
        mock_sleep.assert_called_once_with(test_delay)

    @patch('src.objects.connections.sleep')
    @patch('src.objects.connections.Connection._delete_connection')
    def test_delete(self, mock_delete_connection: Mock, mock_sleep: Mock):
        test_delay = 0.1
        self.connection.identifier = 'existing_id'
        result = self.connection.delete(test_delay)
        self.assertIsNotNone(result)
        mock_delete_connection.assert_called_once()
        mock_sleep.assert_called_once_with(test_delay)

    @patch('src.objects.connections.sleep')
    @patch('src.objects.connections.Connection._update_connection')
    def test_update(self, mock_update_connection: Mock, mock_sleep: Mock):
        test_delay = 0.1
        self.connection.identifier = 'existing_id'
        result = self.connection.update(test_delay)
        self.assertIsNotNone(result)
        mock_update_connection.assert_called_once()
        mock_sleep.assert_called_once_with(test_delay)

    @patch('src.objects.connections.msg_format')
    def test_create_with_identifier(self, mock_msg_format: Mock):
        self.connection.identifier = 'existing_id'
        result = self.connection.create()
        self.assertIsNone(result)
        mock_msg_format.error_msg.assert_called_once()

    @patch('src.objects.connections.msg_format')
    def test_create_without_parent(self, mock_msg_format: Mock):
        self.connection.parent_identifier = None
        result = self.connection.create()
        self.assertIsNone(result)
        mock_msg_format.error_msg.assert_called_once()

    @patch('src.objects.connections.msg_format')
    def test_delete_without_identifier(self, mock_msg_format: Mock):
        result = self.connection.delete()
        self.assertIsNone(result)
        mock_msg_format.error_msg.assert_called_once()

    @patch('src.objects.connections.msg_format')
    def test_update_without_identifier(self, mock_msg_format: Mock):
        result = self.connection.update()
        self.assertIsNone(result)
        mock_msg_format.error_msg.assert_called_once()

    @patch('src.objects.connections.msg_format')
    def test_update_without_parent(self, mock_msg_format: Mock):
        self.connection.parent_identifier = None
        result = self.connection.update()
        self.assertIsNone(result)
        mock_msg_format.error_msg.assert_called_once()


if __name__ == '__main__':
    unittest.main()