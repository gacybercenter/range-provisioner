"""_summary_:

Returns:
    _type_: _description_
"""
import unittest
import yaml
import openstack
from unittest.mock import Mock, patch
from src.utils.manage_ids import update_ids, update_env


class UpdateIDsTestCase(unittest.TestCase):
    """
    Test case for the update IDs functionality.

    This test case contains various test methods to validate the functionality of the update IDs feature.
    The test methods cover scenarios like updating the env.yaml file with new resource IDs.

    Attributes:
        mock_connection (MockConnection): A mock connection object.
        globals_dict (MockGlobalsDict): A mock object containing global dictionaries.
    """

    def setUp(self):
        """
        Set up the test environment.

        This function is used to prepare the test environment before each test method is executed.

        Returns:
            None
        """
        self.reset_env_file()
        self.mock_connection = Mock(openstack.connect)
        self.mock_connection.current_project_id = "mock_project_id"
        self.mock_connection.orchestration = MockOrchestration()
        self.mock_connection.close = Mock()
        self.globals_dict = MockGlobalsDict()

    def tearDown(self):
        """
        Clean up the test environment.

        This function is used to clean up the test environment after each test method is executed.

        Returns:
            None
        """
        self.reset_env_file()

    def reset_env_file(self):
        """
        Resets the env.yaml file to its original state.

        This function is used to reset the env.yaml file to its original state after each test method is run.

        Returns:
            None
        """
        encoding = 'utf-8'
        template_path = 'tests/templates/env.yaml'
        env_template = {
            'parameters': {
                'stack1.network_id': None,
                'stack1.subnet_id': None
            }
        }
        with open(template_path, 'w', encoding=encoding) as template_file:
            yaml.dump(
                env_template,
                template_file,
                encoding=encoding,
                default_flow_style=False,
                sort_keys=True
            )

    def test_update_env_with_new_ids(self):
        """
        Test updating env.yaml file with new resource IDs.

        This test method verifies the correctness of the update_env function by comparing the
        output with the expected output. It checks if the env.yaml file is updated correctly.

        Returns:
            None
        """
        conn = self.mock_connection
        globals_dict = self.globals_dict
        make_entries = False
        debug = False
        correct_output = {
            'parameters': {
                'stack1.network_id': 'network_id',
                'stack1.subnet_id': 'subnet_id'
            }
        }
        output = update_env(conn, globals_dict, make_entries, debug)
        self.assertEqual(output, correct_output)

class MockConnection:
    """
    Simulates an Openstack connection.
    """
    def __init__(self):
        self.current_project_id = "mock_project_id"
        self.orchestration = MockOrchestration()

class MockOrchestration:
    """
    Simulates the Openstack orchestration.
    """
    def stacks(self, project_id):
        """
        Retrieves the stacks associated with the given project ID.

        Args:
            project_id (str): The ID of the project.

        Returns:
            list of Stack: A list of Stack objects representing the stacks associated
            with the project ID. If the project ID is "mock_project_id", a list of
            MockStack objects with names "stack1" and "stack2" is returned. If the
            project ID is not "mock_project_id", returns None.
        """
        if project_id == "mock_project_id":
            return [MockStack("stack1"), MockStack("stack2")]
        return None

    def find_stack(self, stack_name):
        """
        Finds a stack based on its name.

        Args:
            stack_name (str): The name of the stack to find.

        Returns:
            MockStack or None: The found stack if it exists, otherwise None.
        """
        if stack_name == "stack1":
            return MockStack(stack_name)
        return None

    def resources(self, stack_name):
        """
        Returns a list of resources for a given stack name.

        Parameters:
            stack_name (str): The name of the stack.

        Returns:
            list: A list of resources for the given stack name.
        """
        if stack_name in ("stack1", "stack2"):
            return [
                MockResource(stack_name, "network"),
                MockResource(stack_name, "subnet")
            ]

class MockStack:
    """
    Simulates a stack.
    """
    def __init__(self, name):
        self.name = name

class MockResource:
    """
    Simulates a resource.
    """
    def __init__(self, stack_name, resource_type):
        self.logical_resource_id = f"{stack_name}.{resource_type}"
        self.physical_resource_id = f"{resource_type}_id"


class MockGlobalsDict:
    """
    Simulates a global dictionary.
    """
    def __init__(self):
        self.globals = {
            "debug": True,
            "cloud": "gcr",
            "num_users": 3,
            "num_ranges": 3,
            "user_name": "analyst",
            "range_name": "alphanox",
            "guacd": True,
            "provision": None
        }
        self.guacamole = {
            "provision": True,
            "update": False,
            "secure": True,
            "guac_host": "https://training.gacyberrange.org",
            "conn_group_name": "range_team",
            "user_org": "",
            "instance_mapping": "user.instance"
        }
        self.heat = {
            "provision": False,
            "main": True,
            "sec": False,
            "update": False,
            "template_dir": "tests/templates",
            "wait": False,
            "pause": 2
        }
        self.swift = {
            "provision": False,
            "update": False,
            "asset_dir": "assets"
        }


if __name__ == '__main__':
    unittest.main()
