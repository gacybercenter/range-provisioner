import unittest
from guacamole import session
from unittest.mock import Mock
from src.objects.connections import SharingProfile


class TestSharingProfile(unittest.TestCase):

    def setUp(self):
        self.mock_gconn = Mock(session)
        self.sharing_profile = SharingProfile(
            gconn=self.mock_gconn,
            name='TestSharingProfile',
            parent_identifier='TestConnectionInstance',
            parameters={'key1': 'value1'},
            identifier=None,
            debug=False
        )

    def test_init(self):
        self.assertEqual(self.sharing_profile.name, 'TestSharingProfile')
        self.assertEqual(self.sharing_profile.parent_identifier, 'TestConnectionInstance')
        self.assertEqual(self.sharing_profile.parameters, {'key1': 'value1'})
        self.assertIsNone(self.sharing_profile.identifier)
        self.assertFalse(self.sharing_profile.debug)

    def test_create_sharing_profile(self):
        self.sharing_profile.create()
        self.mock_gconn.create_sharing_profile.assert_called_once_with(
            self.sharing_profile.parent_identifier,
            self.sharing_profile.name,
            self.sharing_profile.parameters
        )

    def test_delete_sharing_profile(self):
        self.sharing_profile.identifier = 'sharing_profile_id'
        self.sharing_profile.delete()
        self.mock_gconn.delete_sharing_profile.assert_called_once_with('sharing_profile_id')

    def test_update_sharing_profile(self):
        self.sharing_profile.identifier = 'sharing_profile_id'
        self.sharing_profile.update()
        self.mock_gconn.update_sharing_profile.assert_called_once_with(
            self.sharing_profile.parent_identifier,
            self.sharing_profile.name,
            'sharing_profile_id',
            self.sharing_profile.parameters
        )

    def test_detail_sharing_profile(self):
        self.sharing_profile.identifier = 'sharing_profile_id'
        self.sharing_profile.detail()
        self.mock_gconn.detail_sharing_profile.assert_called_once_with(
            'sharing_profile_id',
            'parameters'
        )


if __name__ == '__main__':
    unittest.main()