import unittest
from unittest.mock import Mock, patch
from guacamole import session
from src.objects.users import User


class TestUser(unittest.TestCase):

    def setUp(self):
        self.mock_gconn = Mock(session)
        self.user = User(
            gconn=self.mock_gconn,
            username='test_username',
            password='test_password',
            attributes={'attribute1': 'value1', 'attribute2': 'value2'},
            permissions={
                'connectionGroupPermissions': ['group1', 'group2'],
                'connectionPermissions': ['conn1', 'conn2'],
                'sharingProfilePermissions': ['sharing1', 'sharing2'],
                'userGroupPermissions': ['user1', 'user2'],
                'systemPermissions': ['perm1', 'perm2']
            },
            debug=False
        )

    @patch('src.objects.users.sleep')
    def test_create(self, mock_sleep: Mock):
        test_delay = 0.1
        result = self.user.create(test_delay)
        self.assertIsNotNone(result)
        self.mock_gconn.create_user.assert_called_once_with(self.user.username,
                                                            self.user.password,
                                                            self.user.attributes)
        mock_sleep.assert_any_call(test_delay)
        self.assertEqual(mock_sleep.call_count, 2)
        self.assertEqual(self.mock_gconn.update_connection_permissions.call_count, 3)
        # Check the add permissions calls
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      self.user.permissions['connectionGroupPermissions'],
                                                                      'add',
                                                                      'group')
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      self.user.permissions['connectionPermissions'],
                                                                      'add',
                                                                      'connection')
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      self.user.permissions['sharingProfilePermissions'],
                                                                      'add',
                                                                      'sharing profile')
        self.mock_gconn.update_user_group.assert_called_once_with(self.user.username,
                                                                  self.user.permissions['userGroupPermissions'],
                                                                  'add')
        self.mock_gconn.update_user_permissions.assert_called_once_with(self.user.username,
                                                                        self.user.permissions['systemPermissions'],
                                                                        'add')

    @patch('src.objects.users.sleep')
    def test_delete(self, mock_sleep: Mock):
        test_delay = 0.1
        result = self.user.delete(test_delay)
        self.assertIsNotNone(result)
        self.mock_gconn.delete_user.assert_called_once_with(self.user.username)
        mock_sleep.assert_called_once_with(test_delay)

    @patch('src.objects.users.sleep')
    def test_update(self, mock_sleep: Mock):
        test_delay = 0.1
        old_perms = {
            'connectionGroupPermissions': ['group1', 'group3'],
            'connectionPermissions': ['conn1', 'conn3'],
            'sharingProfilePermissions': ['sharing1', 'sharing3'],
            'userGroupPermissions': ['user1', 'user3'],
            'systemPermissions': ['perm1', 'perm3']
        }
        add_perms = {
            'connectionGroupPermissions': ['group2'],
            'connectionPermissions': ['conn2'],
            'sharingProfilePermissions': ['sharing2'],
            'userGroupPermissions': ['user2'],
            'systemPermissions': ['perm2']
        }
        rem_perms = {
            'connectionGroupPermissions': ['group3'],
            'connectionPermissions': ['conn3'],
            'sharingProfilePermissions': ['sharing3'],
            'userGroupPermissions': ['user3'],
            'systemPermissions': ['perm3']
        }
        result = self.user.update(old_perms, test_delay)
        self.assertIsNotNone(result)
        self.mock_gconn.update_user.assert_called_with(self.user.username,
                                                       self.user.attributes)
        mock_sleep.assert_any_call(test_delay)
        self.assertEqual(mock_sleep.call_count, 2)
        self.assertEqual(self.mock_gconn.update_connection_permissions.call_count, 6)
        self.assertEqual(self.mock_gconn.update_user_group.call_count, 2)
        self.assertEqual(self.mock_gconn.update_user_permissions.call_count, 2)
        # Check the add permissions calls
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      add_perms['connectionGroupPermissions'],
                                                                      'add',
                                                                      'group')
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      add_perms['connectionPermissions'],
                                                                      'add',
                                                                      'connection')
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      add_perms['sharingProfilePermissions'],
                                                                      'add',
                                                                      'sharing profile')
        self.mock_gconn.update_user_group.assert_any_call(self.user.username,
                                                          add_perms['userGroupPermissions'],
                                                          'add')
        self.mock_gconn.update_user_permissions.assert_any_call(self.user.username,
                                                                add_perms['systemPermissions'],
                                                                'add')
        # Check the remove permissions calls
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      rem_perms['connectionGroupPermissions'],
                                                                      'remove',
                                                                      'group')
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      rem_perms['connectionPermissions'],
                                                                      'remove',
                                                                      'connection')
        self.mock_gconn.update_connection_permissions.assert_any_call(self.user.username,
                                                                      rem_perms['sharingProfilePermissions'],
                                                                      'remove',
                                                                      'sharing profile')
        self.mock_gconn.update_user_group.assert_any_call(self.user.username,
                                                          rem_perms['userGroupPermissions'],
                                                          'remove')
        self.mock_gconn.update_user_permissions.assert_any_call(self.user.username,
                                                                rem_perms['systemPermissions'],
                                                                'remove')


if __name__ == '__main__':
    unittest.main()
