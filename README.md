# Range Provisioner

Range Provisioner integrates various technologies to assist in the deployment
and management of CYber Range environments. While leveraged within GitLab's
CI/CD capability to interact with available API's for both Open
Infrastructure's OpenStack project and Apache Foundation's Guacamole project,
it can leveraged as a standalone utility.

## Features

This utility provides various features and is built in such a way that
further capabilities and can added to meet future requirements and identified
needs.

### Containerization

- Docker Image availability for easy implementation

### OpenStack API Integrations

- Create, Update, and Delete Swift Object Store Containers and Objects
- Create, Update, and Delete Heat Orchestration Stacks

### Guacamole API Integration

- Create, Update, and Delete Connection Groups
- Create, Update, and Delete Connections
- Create, Update, and Delete Sharing Profiles
- Create, Update, and Delete Users
- Update Connection Permissions for Users

## Requirements

To ensure proper functionality and usage, identified below is the baseline
directory structure and HOT parameters required for use of Range Provisioner.

**Project Repository Structure**  

```shell
DIR
|___ assets
|       |___ config.sh
|___ scr
|       |___ objects
|       |       |___ __init__.py
|       |       |___ connections.py
|       |       |___ heat.py
|       |       |___ swift.py
|       |       |___ users.py
|       |___ provision
|       |       |___ __init__.py
|       |       |___ guac.py
|       |       |___ heat.py
|       |       |___ swift.py
|       |___ utils
|       |       |___ __init__.py
|       |       |___ connections.py
|       |       |___ generate.py
|       |       |___ load_template.py
|       |       |___ msg_format.py
|       |       |___ parse.py
|       |___ provisioner.py
|___ templates
|       |___ main.yaml
|       |___ guac.yaml
|___ globals.yaml
|___ clouds.yaml          (Hidden)
|___ README.md
|___ requirements.txt
```

_This provides the foundational directory structure for storing Heat Orchestration
Templates in `templates`, `assets` to be uploaded to the object store and the base
`globals.yaml` which defines specifics for how to deploy the Cyber Range_

### Fields for the configuration files

_Example parameters within the `globals.yaml`_  

```yaml
#YAML for storing range provisioning parameters
globals:
  debug: False # debug mode (True) or not (False)
  artifacts: True # artifacts (True) or not (False)
  organization: organization # top level identifier for guac users
  provision: # provision range (True) or not (False)

guacamole:
  provision: True # provision guacamole (True) or not (False)
  update: True # update guacamole users (True) or not (False)
  cloud: guacamole # name of cloud to use
  guac_file: templates/guac.yaml # name of guacamole config file
  org_name: organization # name of the guacamole organization. Default is organization's name
  pause: 0.5 # pause between each guacamole action in seconds

heat:
  provision: True # provision heat (True) or not (False)
  update: True # update heat (True) or not (False)
  cloud: openstack # name of cloud to use
  amount: 2 # number of heat stacks to provision
  heat_file: templates/main.yaml # name of guacamole config file
  stack_name: stack # name of the heat stack. Default is organization's name
  stack_delay: 30 # delay between each heat stack in seconds
  pause: 0.5 # pause between each heat action in seconds
  parameters: # Update existing heat parameters
  - username: test
  - count: 2

swift:
  provision: True # provision swift (True) or not (False)
  update: True # update swift (True) or not (False)
  cloud: gcr # name of cloud to use
  assets_dir: assets # directory containing swift assets
  container_name: container # name of the swift container. Default is organization's name
  pause: 0.5 # pause between each swift action in seconds
```

_Example parameters within the `clouds.yaml`_  

```yaml
clouds:
  openstack:
    auth:
      auth_url: https://openstack.domain.net:5000/v3
      project_id: 0123456789abcdef0123456789abcdef
      project_name: project
      username: username
      password: password
      user_domain_name: Default
      project_domain_name: Default
    region_name: RegionOne
    identity_api_version: 3
  guacamole:
    host: https://guacamole.domain.net
    data_source: mysql
    username: username
    password: password
```

### Heat Orchestration Templates

_Example parameters within the `main.yaml`_  

```yaml
parameters:
  username:
    type: string
    label: Default username
    description: Sets the username for the instances
    default: user
  password:
    type: string
    label: Default password
    description: Sets the password for the instances
    default: password
  count:
    type: string
    label: Default count
    description: Sets the instance count
    default: 1
  kali.image:
    type: string
    label: Default Kali image
    description: Sets the Kali linux image
    default: kali-24.04

resources:
  kali.server:
    type: OS::Heat::ResourceGroup
    properties:
      count: { get_param: count }
      removal_policies: [{'resource_list': ['0']}]
      resource_def:
        type: OS::Nova::Server
        properties:
          name:
            list_join: [ '.', [ { get_param: "OS::stack_name"}, 'kali', '%index%']]
          image: { get_param: kali.image }
          flavor: m1.medium
          config_drive: true
          networks:
          - network: public
          security_groups: []
          user_data_format: RAW
          user_data: 
            str_replace:
              template: |
                #!/bin/bash

                apt update

                useradd -m -U -s /bin/bash __username__
                usermod -aG sudo,netdev __username__
                timedatectl set-timezone America/New_York
                echo "root:__rootpass__" | chpasswd
                echo "__username__:__password__" | chpasswd

                reboot
              params:
                __rootpass__: "P@ssw0rd123"
                __username__: { get_param: username }
                __password__: { get_param: password }
```

_Example parameters within the `guac.yaml`_

```yaml
# JINJA Variables
{% set systems = 2 %}
{% set organization = "organization" %}

# Stacks
stacks:
  - {{ organization }}

# Groups
groups:
  {{ organization }}:
    parent: ROOT
    attributes:
      max-connections: 10

# Connection Templates
connectionTemplates:
  {{ organization }}.screen.server:
    parent: {{ organization }}
    pattern: {{ organization }}.kali.(\d+)
    parameters:
      username: user
      password: password

# Users
users:
  {% for system in range(1, systems+1) %}
  {{ organization }}.user.{{ system }}:
    username: {{ organization }}.kali.{{ system }}
    password: P@ssw0rd
    permissions:
      connectionPermissions:
        - {{ organization }}.kali.{{ system }}
  {% endfor %}
```

### Usage Examples

#### Running manually

To run Range Provisioner manually, use the following command.

```bash
python3 ./src/provisioner.py ARGUMENT
```

##### Arguments

- swift
- heat
- guacamole
- full

#### Using Gitlab CI/CD pipeline

To ensure easy of use the following provides an example CI/CD implementation utilizing Range
Provisioner to facilitate to creation and deletion of cyber range environments.
The main source for the Docker Image is from
`registry.gitlab.com/gacybercenter/gacyberrange/cloud-imaging/container-factory/range-provisioner:latest`,
where you can also find previous versions.

```yaml
default:
  image: registry.gitlab.com/gacybercenter/gacyberrange/cloud-imaging/container-factory/range-provisioner:latest
  before_script:
    - mv $(echo $clouds) clouds.yaml

stages:
  - Swift
  - Heat
  - Guacamole

object_upload:
  stage: Swift
  script: |
      python3 /range-provisioner/src/provisioner.py swift
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/) || ($CI_COMMIT_MESSAGE =~ /\[build-swift]/) || ($CI_COMMIT_MESSAGE =~ /\[delete-swift]/)
      when: always

heat_deploy:
  stage: Heat
  script: |
      python3 /range-provisioner/src/provisioner.py swift
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/) || ($CI_COMMIT_MESSAGE =~ /\[build-heat]/) || ($CI_COMMIT_MESSAGE =~ /\[delete-heat]/)
      when: always

guac_provision:
  stage: Guacamole
  script: |
      python3 /range-provisioner/src/provisioner.py swift
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/) || ($CI_COMMIT_MESSAGE =~ /\[build-guacamole]/) || ($CI_COMMIT_MESSAGE =~ /\[delete-guacamole]/)
      when: always
```

Within the `rules` portion, this ensures that you will not have a double
pipeline trigger when you have an open merge request:

```yaml
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
```

This allows determines when specific jobs will trigger based on the `$CI_COMMIT_MESAGE`
variable, as seen here by looking for `[build]` or `[delete]` at the beginning of a
commit message:

```yaml
  rules:
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/)
      when: always
```

## Unit Tests

To run the unit tests, run the following commands.

### Activate the Python Virtual Environment

```bash
python3 -m venv .venv
. .venv/bin/activate
```

### Install required Python Modules

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run the tests

```bash
pytest tests/unit
```
