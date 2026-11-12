from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from provision import heat
from utils import heat_environment


def resource(kind, name, identifier):
    return SimpleNamespace(
        resource_type=kind, logical_resource_id=name,
        physical_resource_id=identifier
    )


@pytest.mark.parametrize('update', [False, True])
def test_env_parameters_are_applied_before_explicit_heat_overrides(tmp_path, monkeypatch, update):
    monkeypatch.delenv('num_ranges', raising=False)
    (tmp_path / 'main.yaml').write_text(
        'parameters:\n  network_id:\n    default: default-id\n'
        '  username:\n    default: default-user\n',
        encoding='utf-8',
    )
    (tmp_path / 'env.yaml').write_text(
        'parameters:\n  network_id: env-id\n  username: env-user\n',
        encoding='utf-8',
    )
    conn = Mock()
    conn.get_stack.return_value = {'id': 'existing'} if update else None

    heat.provision(conn, {'organization': 'range', 'template_dir': str(tmp_path)}, {
        'provision': True, 'update': update, 'heat_file': 'main.yaml', 'env_file': 'env.yaml',
        'parameters': [{'username': 'configured-user'}], 'pause': 0, 'stack_delay': 0,
    })

    kwargs = {
        'template_file': 'main.yaml', 'wait': True, 'rollback': False,
        'network_id': 'env-id', 'username': 'configured-user',
    }
    if update:
        conn.update_stack.assert_called_once_with(name_or_id='range', **kwargs)
        conn.create_stack.assert_not_called()
    else:
        conn.create_stack.assert_called_once_with(name='range', **kwargs)
    conn.orchestration.resources.assert_not_called()


def test_env_discovers_selected_stacks_without_writing_file(tmp_path, monkeypatch):
    monkeypatch.delenv('num_ranges', raising=False)
    (tmp_path / 'main.yaml').write_text(
        'parameters:\n  network_id: {}\n  subnet_id: {}\n', encoding='utf-8'
    )
    env_file = tmp_path / 'env.yaml'
    contents = 'parameters:\n  network_id: null\n  subnet_id: null\n'
    env_file.write_text(contents, encoding='utf-8')
    conn = Mock()
    conn.get_stack.return_value = None
    conn.orchestration.resources.return_value = [
        resource('OS::Neutron::Net', 'network', 'net-id'),
        resource('OS::Neutron::Subnet', 'subnet', 'sub-id'),
        resource('OS::Nova::Server', 'server', 'server-id'),
    ]
    conn.network.find_network.return_value.name = 'shared-network'
    conn.network.find_subnet.return_value.name = 'shared.subnet'

    settings = {
        'provision': True, 'heat_file': 'main.yaml', 'env_file': 'env.yaml',
        'env_stacks': ['shared'], 'pause': 0, 'stack_delay': 0,
    }
    globals_dict = {'organization': 'range', 'template_dir': str(tmp_path)}
    heat.provision(conn, globals_dict, settings, dry_run=True)
    conn.create_stack.assert_not_called()
    heat.provision(conn, globals_dict, settings)

    conn.orchestration.resources.assert_any_call('shared')
    assert conn.create_stack.call_args.kwargs['network_id'] == 'net-id'
    assert conn.create_stack.call_args.kwargs['subnet_id'] == 'sub-id'
    assert env_file.read_text(encoding='utf-8') == contents


def test_env_rejects_ambiguous_and_missing_discovered_ids(tmp_path):
    (tmp_path / 'env.yaml').write_text('parameters:\n  network_id: null\n', encoding='utf-8')
    conn = Mock()
    conn.orchestration.resources.side_effect = [
        [resource('OS::Neutron::Net', 'net', 'one')],
        [resource('OS::Neutron::Net', 'net', 'two')],
    ]
    conn.network.find_network.return_value.name = 'network'
    with pytest.raises(ValueError, match='Multiple resources'):
        heat_environment.load_parameters(conn, 'env.yaml', str(tmp_path), ['a', 'b'])

    conn.orchestration.resources.side_effect = None
    conn.orchestration.resources.return_value = []
    with pytest.raises(ValueError, match='Could not resolve.*network_id'):
        heat_environment.load_parameters(conn, 'env.yaml', str(tmp_path), ['a'])


def test_env_rejects_resources_without_physical_ids(tmp_path):
    (tmp_path / 'env.yaml').write_text('parameters:\n  network_id: null\n', encoding='utf-8')
    conn = Mock()
    conn.orchestration.resources.return_value = [resource('OS::Neutron::Net', 'net', None)]

    with pytest.raises(ValueError, match='Missing physical ID'):
        heat_environment.load_parameters(conn, 'env.yaml', str(tmp_path), ['a'])
    conn.network.find_network.assert_not_called()


@pytest.mark.parametrize('content', [
    'parameters: []\n', 'parameters: {}\nresource_registry: {}\n',
])
def test_env_rejects_unsupported_shape(tmp_path, content):
    (tmp_path / 'env.yaml').write_text(content, encoding='utf-8')
    with pytest.raises(ValueError, match='parameters.*mapping'):
        heat_environment.load_parameters(Mock(), 'env.yaml', str(tmp_path), [])


def test_env_rejects_unknown_heat_parameter(tmp_path, monkeypatch):
    monkeypatch.delenv('num_ranges', raising=False)
    (tmp_path / 'main.yaml').write_text('parameters: {}\n', encoding='utf-8')
    (tmp_path / 'env.yaml').write_text('parameters:\n  typo: value\n', encoding='utf-8')
    conn = Mock()

    with pytest.raises(ValueError, match="Heat env parameter 'typo'"):
        heat.provision(conn, {'organization': 'range', 'template_dir': str(tmp_path)}, {
            'provision': True, 'heat_file': 'main.yaml', 'env_file': 'env.yaml',
            'pause': 0, 'stack_delay': 0,
        })
    conn.get_stack.assert_not_called()


def test_env_stacks_require_an_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv('num_ranges', raising=False)
    (tmp_path / 'main.yaml').write_text('parameters: {}\n', encoding='utf-8')
    with pytest.raises(ValueError, match="'env_stacks' requires 'env_file'"):
        heat.provision(Mock(), {'organization': 'range', 'template_dir': str(tmp_path)}, {
            'provision': True, 'heat_file': 'main.yaml', 'env_stacks': ['shared'],
            'pause': 0, 'stack_delay': 0,
        })
