import yaml
# with open('./templates/main.yaml', 'r') as file:
#     stack_template = yaml.safe_load(file)

# print(stack_template['parameters'])

with open('globals.yaml', 'r') as file2:
    stack_template = yaml.safe_load(file2)
    print(stack_template)

print(stack_template['guac']['guac_action'])