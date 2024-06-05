import unittest
from guacamole import session
from unittest.mock import Mock
from src.objects.connections import ConnectionGroup


class TestConnectionGroup(unittest.TestCase):

    def setUp(self):
        self.mock_gconn = Mock(session)
        self.connection_group = ConnectionGroup(
            gconn=self.mock_gconn,
            name='TestConnectionGroup',
            parent_identifier='ROOT',
            group_type='ORGANIZATIONAL',
            attributes={'key1': 'value1'},
            identifier=None,
            debug=False
        )

    def test_init(self):
        self.assertEqual(self.connection_group.name, 'TestConnectionGroup')
        self.assertEqual(self.connection_group.parent_identifier, 'ROOT')
        self.assertEqual(self.connection_group.type, 'ORGANIZATIONAL')
        self.assertEqual(self.connection_group.attributes, {'key1': 'value1'})
        self.assertIsNone(self.connection_group.identifier)
        self.assertFalse(self.connection_group.debug)

    def test_create_connection_group(self):
        self.connection_group.create()
        self.mock_gconn.create_connection_group.assert_called_once_with(
            self.connection_group.name,
            self.connection_group.type,
            self.connection_group.parent_identifier,
            self.connection_group.attributes
        )

    def test_delete_connection_group(self):
        self.connection_group.identifier = 'group_id'
        self.connection_group.delete()
        self.mock_gconn.delete_connection_group.assert_called_once_with('group_id')

    def test_update_connection_group(self):
        self.connection_group.identifier = 'group_id'
        self.connection_group.update()
        self.mock_gconn.update_connection_group.assert_called_once_with(
            'group_id',
            self.connection_group.name,
            self.connection_group.type,
            self.connection_group.parent_identifier,
            self.connection_group.attributes
        )

    def test_detail_connection_group(self):
        self.connection_group.identifier = 'group_id'
        self.connection_group.detail()
        self.mock_gconn.detail_connection_group_connections.assert_called_once_with('group_id')
