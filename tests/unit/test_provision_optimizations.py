from unittest.mock import Mock

import pytest

from objects.connections import CurrentConnections, NewConnections
from objects.heat import HeatStack
from objects.swift import SwiftContainer
from objects.users import CurrentUsers, NewUsers
from provision import guac, heat


def test_swift_lookup_uses_prefix_filtered_listing():
    conn = Mock()
    container = {'name': 'assets'}
    conn.list_containers.return_value = [{'name': 'assets-old'}, container]

    result = SwiftContainer(conn, 'assets', 'assets')

    assert result.container is container
    conn.list_containers.assert_called_once_with(prefix='assets')
    conn.search_containers.assert_not_called()


def test_swift_lookup_ignores_other_containers_with_same_prefix():
    conn = Mock()
    conn.list_containers.return_value = [{'name': 'assets-old'}]

    result = SwiftContainer(conn, 'assets', 'assets')

    assert result.container is None


def test_swift_wildcard_lookup_keeps_legacy_search():
    conn = Mock()
    container = {'name': 'assets-1'}
    conn.search_containers.return_value = [container]

    result = SwiftContainer(conn, 'assets-*', 'assets')

    assert result.container is container
    conn.search_containers.assert_called_once_with(name='assets-*')
    conn.list_containers.assert_not_called()


def test_swift_empty_name_keeps_legacy_search():
    conn = Mock()
    conn.search_containers.return_value = [{'name': 'assets'}]

    result = SwiftContainer(conn, '', 'assets')

    assert result.container['name'] == 'assets'
    conn.search_containers.assert_called_once_with(name='')
    conn.list_containers.assert_not_called()


def test_swift_lookup_propagates_errors():
    conn = Mock()
    conn.list_containers.side_effect = RuntimeError('cloud unavailable')

    with pytest.raises(RuntimeError, match='cloud unavailable'):
        SwiftContainer(conn, 'assets', 'assets')


def test_heat_stack_resolves_outputs_by_default():
    conn = Mock()
    HeatStack(conn, 'range')

    conn.get_stack.assert_called_once_with(name_or_id='range')


def test_heat_provision_skips_output_resolution(monkeypatch):
    monkeypatch.delenv('num_ranges', raising=False)
    monkeypatch.setattr(heat.load_template, 'load_yaml_file',
                        lambda *args, **kwargs: {'parameters': {}})
    conn = Mock()

    heat.provision(conn, {'organization': 'range'}, {
        'provision': True,
        'update': False,
        'heat_file': 'heat.yaml',
        'pause': 0,
        'stack_delay': 0,
    }, dry_run=True)

    conn.get_stack.assert_called_once_with(name_or_id='range', resolve_outputs=False)


def test_heat_jinja_dry_run_does_not_create_temp_file(monkeypatch):
    monkeypatch.delenv('num_ranges', raising=False)
    monkeypatch.setattr(heat.load_template, 'load_yaml_file',
                        lambda *args, **kwargs: {'parameters': {}})
    temp_file = Mock()
    monkeypatch.setattr(heat, 'NamedTemporaryFile', temp_file)
    monkeypatch.setattr(heat, 'HeatStack', Mock())

    heat.provision(Mock(), {'organization': 'range'}, {
        'provision': True,
        'update': False,
        'heat_file': 'heat.yaml',
        'jinja': True,
        'pause': 0,
        'stack_delay': 0,
    }, dry_run=True)

    temp_file.assert_not_called()


def test_guacamole_without_templates_skips_server_discovery():
    gconn = Mock()
    gconn.list_connection_groups.return_value = {}
    oconn = Mock()

    result = NewConnections(gconn, oconn, {'groups': {}})

    assert result.connections == []
    oconn.list_servers.assert_not_called()


def test_guacamole_with_templates_still_discovers_servers():
    gconn = Mock()
    oconn = Mock()
    oconn.list_servers.return_value = [{
        'name': 'server', 'public_v4': '', 'private_v4': '10.0.0.1',
    }]

    result = NewConnections(gconn, oconn, {
        'groups': {},
        'connectionTemplates': {'server': {'pattern': 'server'}},
    })

    oconn.list_servers.assert_called_once_with()
    assert result.connections[0].parameters['hostname'] == '10.0.0.1'


def test_guacamole_existing_object_details_are_loaded_by_default():
    gconn = Mock()
    gconn.list_users.return_value = {
        'student': {'username': 'student', 'attributes': {'guac-organization': 'range'}}
    }
    gconn.detail_user_permissions.return_value = {}
    gconn.detail_connection_group_connections.return_value = {
        'identifier': 'ROOT',
        'name': 'ROOT',
        'childConnections': [{
            'identifier': '2', 'name': 'server', 'protocol': 'ssh',
            'parentIdentifier': 'ROOT',
            'sharingProfiles': [{
                'identifier': '3', 'name': 'shared',
                'primaryConnectionIdentifier': '2',
            }],
        }],
    }
    gconn.detail_connection.return_value = {'hostname': '10.0.0.1'}
    gconn.detail_sharing_profile.return_value = {'read-only': 'true'}

    users = CurrentUsers(gconn, 'range')
    connections = CurrentConnections(gconn)

    gconn.detail_user_permissions.assert_called_once_with('student')
    gconn.detail_connection.assert_called_once_with('2', 'parameters')
    gconn.detail_sharing_profile.assert_called_once_with('3', 'parameters')
    assert users.users[0].username == 'student'
    assert connections.connections[0].parameters['hostname'] == '10.0.0.1'


def test_password_matching_preserves_first_existing_username():
    current = [Mock(username='student', password='first'),
               Mock(username='student', password='second')]
    desired = [Mock(username='student', password='new'),
               Mock(username='other', password='other')]
    users = NewUsers.__new__(NewUsers)
    users.current_users = current
    users.users = desired

    users._update_passwords()

    assert desired[0].password == 'first'
    assert desired[1].password == 'other'


@pytest.mark.parametrize('dry_run', [False, True])
def test_guacamole_delete_skips_connection_and_user_detail_requests(monkeypatch, dry_run):
    gconn = Mock()
    gconn.detail_connection_group_connections.return_value = {
        'identifier': 'ROOT',
        'name': 'ROOT',
        'childConnectionGroups': [{
            'identifier': '1',
            'name': 'range',
            'type': 'ORGANIZATIONAL',
            'parentIdentifier': 'ROOT',
            'childConnections': [{
                'identifier': '2',
                'name': 'server',
                'protocol': 'ssh',
                'parentIdentifier': '1',
                'sharingProfiles': [{
                    'identifier': '3', 'name': 'shared',
                    'primaryConnectionIdentifier': '2',
                }],
            }],
        }],
    }
    gconn.list_users.return_value = {
        'student': {'username': 'student', 'attributes': {'guac-organization': 'range'}}
    }
    monkeypatch.setattr(guac.load_template, 'load_yaml_file',
                        lambda *args, **kwargs: {'groups': {'range': {'parent': 'ROOT'}}})

    guac.provision(Mock(), gconn, {'organization': 'range'}, {
        'provision': False,
        'update': False,
        'guac_file': 'guac.yaml',
        'pause': 0,
    }, debug=False, dry_run=dry_run)

    if dry_run:
        gconn.delete_connection_group.assert_not_called()
        gconn.delete_user.assert_not_called()
    else:
        gconn.delete_connection_group.assert_called_once_with('1')
        gconn.delete_user.assert_called_once_with('student')
    gconn.detail_connection.assert_not_called()
    gconn.detail_sharing_profile.assert_not_called()
    gconn.detail_user_permissions.assert_not_called()
