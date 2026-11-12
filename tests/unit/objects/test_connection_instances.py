import unittest
from unittest.mock import Mock, patch
from guacamole import session
from src.objects.connections import ConnectionInstance


class TestConnectionInstance(unittest.TestCase):

    def setUp(self):
        self.mock_gconn = Mock(session)
        self.connection_instance = ConnectionInstance(
            gconn=self.mock_gconn,
            protocol='rdp',
            name='TestConnectionInstance',
            parent_identifier='TestConnectionGroup',
            parameters={'key1': 'value1'},
            attributes={'key2': 'value2'},
            identifier=None,
            debug=False
        )

    def test_init(self):
        self.assertEqual(self.connection_instance.protocol, 'rdp')
        self.assertEqual(self.connection_instance.name, 'TestConnectionInstance')
        self.assertEqual(self.connection_instance.parent_identifier, 'TestConnectionGroup')
        self.assertEqual(self.connection_instance.parameters, {'key1': 'value1'})
        self.assertEqual(self.connection_instance.attributes, {'key2': 'value2'})
        self.assertIsNone(self.connection_instance.identifier)
        self.assertFalse(self.connection_instance.debug)

    def test_create_connection_group(self):
        # No identifier set
        self.connection_instance.create()
        self.mock_gconn.manage_connection.assert_called_once_with(
            self.connection_instance.protocol,
            self.connection_instance.name,
            self.connection_instance.parent_identifier,
            None,
            self.connection_instance.parameters,
            self.connection_instance.attributes
        )

    def test_delete_connection_group(self):
        self.connection_instance.identifier = 'connection_id'
        self.connection_instance.delete()
        self.mock_gconn.delete_connection.assert_called_once_with('connection_id')

    def test_update_connection_group(self):
        self.connection_instance.identifier = 'connection_id'
        self.connection_instance.update()
        self.mock_gconn.manage_connection.assert_called_once_with(
            self.connection_instance.protocol,
            self.connection_instance.name,
            self.connection_instance.parent_identifier,
            'connection_id',
            self.connection_instance.parameters,
            self.connection_instance.attributes
        )

    def test_detail_connection_group(self):
        self.connection_instance.identifier = 'connection_id'
        self.connection_instance.detail()
        self.mock_gconn.detail_connection.assert_called_once_with(
            'connection_id',
            'parameters'
        )


if __name__ == '__main__':
    unittest.main()