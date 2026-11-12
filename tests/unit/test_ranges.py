from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

import pytest

import provisioner
from provision import heat
from utils import load_template
from utils.ranges import apply_range


@pytest.fixture
def base_config():
    return {
        'globals': {'organization': 'base', 'debug': False},
        'heat': {
            'cloud': 'openstack',
            'heat_file': 'templates/main.yaml',
            'parameters': [{'count': 1}, {'username': 'base'}],
        },
        'guacamole': {'guac_file': 'templates/guac.yaml'},
        'swift': {'container_name': 'base-assets'},
    }


def test_range_overrides_preserve_base_and_replace_lists(tmp_path, base_config):
    range_file = tmp_path / 'ranges.yaml'
    range_file.write_text(
        'ranges:\n'
        '  training:\n'
        '    globals:\n'
        '      organization: training\n'
        '    heat:\n'
        '      stack_name: training\n'
        '      parameters:\n'
        '        - count: 2\n',
        encoding='utf-8',
    )
    original = deepcopy(base_config)

    result = apply_range(base_config, 'training', str(range_file))

    assert result['globals'] == {'organization': 'training', 'debug': False}
    assert result['heat']['cloud'] == 'openstack'
    assert result['heat']['stack_name'] == 'training'
    assert result['heat']['parameters'] == [{'count': 2}]
    assert base_config == original
    result['swift']['container_name'] = 'changed'
    assert base_config == original


@pytest.mark.parametrize(
    ('contents', 'name', 'message'),
    [
        ('other: {}\n', 'training', "'ranges' mapping"),
        ('ranges: {}\n', 'missing', "Range 'missing' was not found"),
        ('ranges:\n  training: invalid\n', 'training', 'must be a mapping'),
        ('ranges:\n  training:\n    typo: {}\n', 'training', "Unknown section 'typo'"),
        ('ranges:\n  training:\n    heat: invalid\n', 'training', "'heat'.*must be a mapping"),
    ],
)
def test_invalid_range_configs_fail(tmp_path, base_config, contents, name, message):
    range_file = tmp_path / 'ranges.yaml'
    range_file.write_text(contents, encoding='utf-8')
    with pytest.raises(ValueError, match=message):
        apply_range(base_config, name, str(range_file))


def test_ranges_file_requires_range():
    with pytest.raises(SystemExit) as error:
        provisioner.parse_args(['heat', '--ranges-file', 'ranges.yaml'])
    assert error.value.code == 2


def test_range_name_cannot_be_empty():
    with pytest.raises(SystemExit) as error:
        provisioner.parse_args(['heat', '--range', ''])
    assert error.value.code == 2


def test_selected_range_reaches_provisioning(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'globals.yaml').write_text(
        'globals: {debug: false, organization: base}\n'
        'heat: {cloud: openstack, heat_file: heat.yaml, amount: 1}\n'
        'guacamole: {guac_file: guac.yaml}\n'
        'swift: {}\n',
        encoding='utf-8',
    )
    (tmp_path / 'clouds.yaml').write_text(
        'clouds:\n  openstack:\n    auth:\n      auth_url: https://example.invalid\n',
        encoding='utf-8',
    )
    range_file = tmp_path / 'ranges.yaml'
    range_file.write_text(
        'ranges:\n  training:\n    heat:\n      stack_name: training\n      amount: 2\n',
        encoding='utf-8',
    )
    connect = Mock(return_value=object())
    provision = Mock()
    monkeypatch.setattr(provisioner.connections, 'openstack_connection', connect)
    monkeypatch.setattr(provisioner.heat, 'provision', provision)

    provisioner.main(['heat', '--range', 'training', '--ranges-file', str(range_file), '--dry-run'])

    provision.assert_called_once()
    assert provision.call_args.args[2]['stack_name'] == 'training'
    assert provision.call_args.args[2]['amount'] == 2
    assert provision.call_args.args[2]['cloud'] == 'openstack'
    assert provision.call_args.args[4] is True


def test_existing_command_does_not_load_range_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'globals.yaml').write_text(
        'globals: {debug: false, organization: base}\n'
        'heat: {cloud: openstack, heat_file: heat.yaml, stack_name: base}\n'
        'guacamole: {guac_file: guac.yaml}\n'
        'swift: {}\n',
        encoding='utf-8',
    )
    (tmp_path / 'clouds.yaml').write_text(
        'clouds:\n  openstack:\n    auth:\n      auth_url: https://example.invalid\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(provisioner.connections, 'openstack_connection', Mock())
    provision = Mock()
    monkeypatch.setattr(provisioner.heat, 'provision', provision)

    provisioner.main(['heat', '--dry-run'])

    assert provision.call_args.args[2]['stack_name'] == 'base'


def test_missing_range_fails_before_connecting(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'globals.yaml').write_text(
        'globals: {}\nheat: {}\nguacamole: {}\nswift: {}\n',
        encoding='utf-8',
    )
    range_file = tmp_path / 'ranges.yaml'
    range_file.write_text('ranges: {}\n', encoding='utf-8')
    connect = Mock()
    monkeypatch.setattr(provisioner.connections, 'openstack_connection', connect)

    with pytest.raises(SystemExit) as error:
        provisioner.main(['heat', '--range', 'missing', '--ranges-file', str(range_file)])

    assert error.value.code == 1
    connect.assert_not_called()


def test_example_range_drives_heat_dry_run(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(root)
    monkeypatch.delenv('num_ranges', raising=False)
    base = load_template.load_template('globals.yaml')
    selected = apply_range(base, 'training', 'templates/ranges.yaml')
    stack = Mock()
    stack_factory = Mock(return_value=stack)
    monkeypatch.setattr(heat, 'HeatStack', stack_factory)

    heat.provision(Mock(), selected['globals'], selected['heat'], dry_run=True)

    stack_factory.assert_called_once()
    assert stack_factory.call_args.args[1] == 'training'
    assert stack_factory.call_args.args[3]['count'] == 2
    assert stack_factory.call_args.args[3]['username'] == 'student'
    stack.create.assert_not_called()
    stack.update.assert_not_called()
    stack.delete.assert_not_called()
