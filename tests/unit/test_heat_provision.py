import os
from unittest.mock import Mock

import pytest

from provision import heat as heat_provision


def test_jinja_temp_file_is_removed_when_stack_operation_fails(monkeypatch):
    monkeypatch.delenv('num_ranges', raising=False)
    monkeypatch.setattr(
        heat_provision.load_template,
        'load_yaml_file',
        lambda *args, **kwargs: {'parameters': {}}
    )
    temp_paths = []
    create_temp_file = heat_provision.NamedTemporaryFile

    def track_temp_file(*args, **kwargs):
        temp_file = create_temp_file(*args, **kwargs)
        temp_paths.append(temp_file.name)
        return temp_file

    monkeypatch.setattr(heat_provision, 'NamedTemporaryFile', track_temp_file)
    stack = Mock()
    stack.create.side_effect = RuntimeError('stack create failed')
    monkeypatch.setattr(heat_provision, 'HeatStack', Mock(return_value=stack))

    with pytest.raises(RuntimeError, match='stack create failed'):
        heat_provision.provision(
            conn=Mock(),
            globals_dict={'organization': 'range'},
            heat_globals={
                'provision': True,
                'update': False,
                'amount': 1,
                'heat_file': 'main.yaml',
                'stack_name': 'range',
                'stack_delay': 0,
                'pause': 0,
                'jinja': True,
            },
        )

    assert len(temp_paths) == 1
    assert not os.path.exists(temp_paths[0])
