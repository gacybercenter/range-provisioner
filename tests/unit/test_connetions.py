"""

"""

import unittest
from unittest.mock import patch, mock_open
from src.utils.load_template import load_template

class TestConnections(unittest.TestCase):

    def setUp(self):
        pass

    @patch(
        'src.utils.load_template.open',
        new_callable=mock_open, read_data='name: Test\nvalue: 42'
    )
    @patch('src.utils.load_template.Munch')
    @patch('src.utils.load_template.info_msg')
    def test_open_connection(self, mock_info_msg, mock_munch, mock_file):
        # Arrange
        template_path = 'path/to/template.yaml'
        mock_munch.return_value = {'name': 'Test', 'value': 42}

        # Act
        result = load_template(template_path)

        # Assert
        self.assertEqual(result, {'name': 'Test', 'value': 42})
        mock_info_msg.assert_called_with(f"Loading {template_path}", 'Templates', False)
        mock_file.assert_called_with(template_path, 'r', encoding='utf-8')


    def tearDown(self):
        pass

# Add more test cases for other functions in a similar manner.

if __name__ == '__main__':
    unittest.main()
