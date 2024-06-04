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

**Containerization**  
- Docker Image availability for easy implementation

**OpenStack API Integrations**  
- Create, Update, and Delete Swift Object Store Containers and Objects
- Create, Update, and Delete Heat Orchestration Stacks

**Guacamole API Integration**  
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
|___ example
|       |___ globals.yaml
|___ scr
|       |___ orchestration
|       |       |___ guac.py
|       |       |___ heat.py
|       |       |___ swift.py
|       |___ provision
|       |       |___ guac.py
|       |       |___ heat.py
|       |       |___ swift.py
|       |___ utils
|       |       |___ generate.py
|       |       |___ load_template.py
|       |       |___ manage_ids.py
|       |       |___ msg_format.py
|       |___ provisioner.py
|___ templates
|       |___ main.yaml
|       |___ sec.yaml     (Optional)
|       |___ env.yaml     (Optional)
|       |___ guac.yaml   (Optional)
|___ globals.yaml
|___ clouds.yaml          (Hidden)
|___ README.md
|___ requirements.txt
```
_This provides the foundational directory structure for storing Heat Orchestration 
Templates in `templates`, `assets` to be uploaded to the object store and the base `globals.yaml` which defines specifics for how to deploy the Cyber Range_

### **Heat Orchestration Templates** 

_Example parameters within the `env.yaml`_
```yaml
parameters: {}
```

_Example parameters within the `main.yaml`_  
```yaml
parameters: {}
resources: {}
```

_Example parameters within the `sec.yaml`_
```yaml
parameters:
  name: 
    type: string
    default: sec_group
```

_Example parameters within the `guac.yaml`_
```yaml
stacks:
  - your_stack

groups:
  your_group:
    parent: ROOT
    attributes:
      max-connections: 200

connectionTemplates:
  your_connection:
    parent: your_group
    parameters:
      username: username
      password: password
    attributes:
      guacd-hostname: guacd # Name gets translated to heat IP address

users:
  your_user:
    count: 3
    username: user.%index% # Index starts at 1 and goes to count
    password: user_pass
    permissions:
      connectionPermissions:
        - your_connection.%index% # Name gets translated to heat IP address
      systemPermissions:
        - ADMINISTER
        - CREATE_USER
        - CREATE_USER_GROUP
        - CREATE_CONNECTION
        - CREATE_CONNECTION_GROUP
        - CREATE_SHARING_PROFILE

defaults:
  groups:
    type: ORGANIZATIONAL
    attributes:
      enable-session-affinity: ''
      max-connections: '50'
      max-connections-per-user: '10'

  connectionTemplates:
    protocol: rdp
    parameters:
      port: 3389
      security: any
      ignore-cert: 'true'
    sharingProfiles:
      - parameters:
          read-only: 'true'

  users:
    attributes: {}
      # guac-organization: This field becomes the organization to identify users
```
#### Note: Part of a stack name followed by a '*' maps all stacks containing the entry. <sub><i>Your welcome Brent</i></sub>


#### Mappings to `globals.yaml`
```yaml
#YAML for storing range provisioning parameters
globals:
  debug: False # debug mode (True) or not (False)
  artifacts: True # artifacts (True) or not (False)
  organization: your_org # range name prefix
  amount: 1 # number of ranges to provision
  provision: # provision range (True) or not (False)

guacamole:
  provision: True # provision guacamole (True) or not (False)
  update: True # update guacamole users (True) or not (False)
  cloud: guac_cloud # name of cloud to use
  user_dir: templates # directory containing guacamole templates
  pause: 0.5 # pause between each guacamole action in seconds

heat:
  provision: True # provision heat (True) or not (False)
  update: True # update heat (True) or not (False)
  cloud: openstack_cloud # name of cloud to use
  template_dir: templates # directory containing heat templates
  pause: 60 # pause between each heat stack action in seconds
  parameters: # Update existing heat parameters
  - username: new_user_param

swift:
  provision: True # provision swift (True) or not (False)
  update: True # update swift (True) or not (False)
  cloud: openstack_cloud # name of cloud to use
  asset_dir: assets # directory containing swift assets
```
### Usage Example
To ensure easy of use the following provides an example CI/CD implementation utilizing Range
Provisioner to facilitate to creation and deletion of cyber range environments. The main source for the Docker Image is from `registry.gitlab.com/gacybercenter/gacyberrange/cloud-imaging/container-factory/range-provisioner:latest`, where you can also find previous versions.


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
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/)
      when: always

heat_deploy:
  stage: Heat
  script: |
      python3 /range-provisioner/src/provisioner.py swift
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/)
      when: always

guac_provision:
  stage: Guacamole
  script: |
      python3 /range-provisioner/src/provisioner.py swift
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: $CI_COMMIT_MESSAGE =~ /\[build]/
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