import unittest
from unittest.mock import patch
from src.utils import load_template

class TestTemplateLoader(unittest.TestCase):
    
    def setUp(self):
        self.template_content = 'key: value'
        self.yaml_content = 'key: value'
        self.template_name = 'template.j2'
        self.yaml_file_name = 'main.yaml'
        self.invalid_yaml_file_name = 'main.txt'
        self.nonexistent_file_name = 'nonexistent.yaml'


    @patch('src.utils.load_template.load_template', return_value={'key': 'value'})
    @patch('src.utils.load_template.os.path.exists', return_value=True)
    @patch('src.utils.load_template.os.path.getsize', return_value=10)
    def test_load_yaml_file_success(self, mock_getsize, mock_exists, mock_load_template):
        result = load_template.load_yaml_file(self.yaml_file_name)
        self.assertEqual(result, {'key': 'value'})
    
    @patch('src.utils.load_template.os.path.exists', return_value=True)
    @patch('src.utils.load_template.os.path.getsize', return_value=0)
    def test_load_yaml_file_empty(self, mock_getsize, mock_exists):
        with self.assertRaisesRegex(ValueError, 'is empty'):
            load_template.load_yaml_file(self.nonexistent_file_name)
    
    def test_load_yaml_file_invalid_extension(self):
        with self.assertRaisesRegex(ValueError, 'not a YAML file'):
            load_template.load_yaml_file(self.invalid_yaml_file_name)

    @patch('src.utils.load_template.os.path.exists', return_value=False)
    def test_load_yaml_file_missing(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            load_template.load_yaml_file(self.nonexistent_file_name)
    
    @patch('src.utils.load_template.safe_load', return_value={'key': 'value'})
    @patch('src.utils.load_template.Environment.get_template')
    def test_load_template_success(self, mock_template, mock_safe_load):
        mock_template.return_value.render.return_value = self.template_content
        result = load_template.load_template(self.template_name)
        self.assertEqual(result, {'key': 'value'})
    
    @patch('src.utils.load_template.Environment.get_template')
    def test_load_template_syntax_error(self, mock_get_template):
        mock_get_template.side_effect = load_template.TemplateSyntaxError(
            message='error',
            lineno=1
        )
        with self.assertRaisesRegex(ValueError, 'syntax error'):
            load_template.load_template(self.template_name)

    @patch('src.utils.load_template.safe_load', return_value=None)
    @patch('src.utils.load_template.Environment.get_template')
    def test_load_template_requires_yaml_mapping(self,
                                                 mock_template,
                                                 mock_safe_load):
        mock_template.return_value.render.return_value = ''
        with self.assertRaisesRegex(ValueError, 'YAML mapping'):
            load_template.load_template(self.template_name)


if __name__ == '__main__':
    unittest.main()
