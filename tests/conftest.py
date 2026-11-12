"""
Test configuration
"""

# import tempfile
from unittest.mock import create_autospec
# import yaml
import pytest
from openstack import connect
from guacamole import session


# with open('globals.yaml', 'r') as f:
#   GLOBALS = f.read()

# with open('clouds.yaml', 'r') as f:
#   CLOUDS = f.read()

# # Create a temporary file
# with tempfile.NamedTemporaryFile('w', delete=False) as temp_yaml_file:
#     yaml.dump(GLOBALS, temp_yaml_file, default_flow_style=False)
#     temp_yaml_file.flush()

# with tempfile.NamedTemporaryFile('w', delete=False) as temp_yaml_file:
#     yaml.dump(CLOUDS, temp_yaml_file, default_flow_style=False)
#     temp_yaml_file.flush()

# Now you can use 'temp_yaml_file.name' as the path to your temporary YAML file
# For example, in a test:
# def test_yaml_file():
#     with open(temp_yaml_file.name, 'r') as file:
#         data = yaml.safe_load(file)
#         assert data['servers'][0]['name'] == 'server1'
#         assert data['servers'][1]['status'] == 'SHUTOFF'

# # Cleanup - delete the temporary file after the test
# os.remove(temp_yaml_file.name)

@pytest.fixture
def mock_connection():
    # Create an autospec of the OpenStack Connection class.
    mock_openstack_connection = create_autospec(connect(cloud="cloud"), instance=True)
    mock_openstack_connection.list_servers.return_value = []
    return mock_openstack_connection

@pytest.fixture
def mock_session():
    # Create an autospec of the OpenStack Connection class.
    mock_guacamole_session = create_autospec(session("endpoint",
                                                     "username",
                                                     "password",
                                                     "database"), instance=True)
    mock_guacamole_session.list_users.return_value = []
    return mock_guacamole_session
