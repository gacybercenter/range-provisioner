import yaml
import jinja2

# Load the YAML file
with open('archive/test.yaml', 'r', encoding='utf-8') as file:
    template_string = file.read()

# Define the template
template = jinja2.Template(template_string)

config = {
    'amount': 8,
}

# Render the template with the data
rendered_data = template.render(**config)

# Print the rendered data
print(yaml.safe_load(rendered_data))
