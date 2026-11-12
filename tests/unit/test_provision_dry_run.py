from unittest.mock import Mock

from provision import guac, heat, swift


def test_heat_dry_run_does_not_apply_stack_changes(monkeypatch):
    monkeypatch.delenv('num_ranges', raising=False)
    monkeypatch.setattr(
        heat.load_template,
        'load_yaml_file',
        lambda *args, **kwargs: {'parameters': {}}
    )
    stack = Mock()
    monkeypatch.setattr(heat, 'HeatStack', Mock(return_value=stack))

    heat.provision(
        Mock(),
        {'organization': 'range'},
        {
            'provision': True,
            'update': False,
            'stack_name': 'range',
            'amount': 1,
            'heat_file': 'main.yaml',
            'pause': 0,
            'stack_delay': 0,
        },
        dry_run=True,
    )

    stack.create.assert_not_called()
    stack.update.assert_not_called()
    stack.delete.assert_not_called()


def test_swift_dry_run_does_not_apply_container_changes(monkeypatch):
    container = Mock()
    monkeypatch.setattr(swift, 'SwiftContainer', Mock(return_value=container))

    swift.provision(
        Mock(),
        {'organization': 'range'},
        {
            'provision': True,
            'update': False,
            'container_name': 'range-assets',
            'assets_dir': 'assets',
            'pause': 0,
        },
        dry_run=True,
    )

    container.create.assert_not_called()
    container.update.assert_not_called()
    container.delete.assert_not_called()


def test_guacamole_dry_run_does_not_apply_changes(monkeypatch):
    connection = Mock()
    connection.connections = [object()]
    user = Mock()
    user.users = [object()]
    monkeypatch.setattr(guac, 'NewConnections', Mock(return_value=connection))
    monkeypatch.setattr(guac, 'NewUsers', Mock(return_value=user))
    monkeypatch.setattr(
        guac.load_template,
        'load_yaml_file',
        lambda *args, **kwargs: {'groups': {}, 'connectionTemplates': {}, 'users': {}}
    )

    guac.provision(
        Mock(),
        Mock(),
        {'organization': 'range'},
        {
            'provision': True,
            'update': False,
            'org_name': 'range',
            'guac_file': 'guac.yaml',
            'pause': 0,
        },
        debug=False,
        dry_run=True,
    )

    connection.create.assert_not_called()
    connection.update.assert_not_called()
    user.create.assert_not_called()
    user.update.assert_not_called()
