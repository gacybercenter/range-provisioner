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
|       |___ users.yaml   (Optional)
|___ globals.yaml
|___ README.md
|___ requirements.txt
```
_This provides the foundational directory structure for storing Heat Orchestration 
Templates in `templates`, `assets` to be uploaded to the object store and the base `globals.yaml` which defines specifics for how to deploy the Cyber Range_

### **Heat Orchestration Templates** 

_Expected parameters within the `env.yaml`_
```yaml
parameters: {}
```

_Expected parameters within the `main.yaml`_  
```yaml
parameters:
  username: 
    type: string
    default: deafualt_username

  password:
    type: string
    default: default_password

  count:
    type: string
    default: 3

  tenant_id: 
    type: string
    default: openstack_project_id_value

  container_name:
    type: string
    default: range_provisioner

  conn_proto:
    type: string
    default: ssh

```

_Expected parameters within the `sec.yaml`_
```yaml
parameters:
  name: 
    type: string
    default: sec_group
```

_Expected parameters within the `users.yaml`_
```yaml
parameters:
  Alice:
    password: password1
    sharing: write
    permissions:
      - CREATE_USER
      - CREATE_USER_GROUP
      - CREATE_CONNECTION
      - CREATE_CONNECTION_GROUP
      - CREATE_SHARING_PROFILE
      - ADMINISTER
    instances:
      - Test_Range.Test_Name.1
      - Test_Range.Test_Name.2
      - Test_Range.Test_Name.3
```
#### Note: Part of a stack name in the instances section maps all stacks containing the entry. <sub><i>Your welcome Brent</i></sub>


#### Mappings to `globals.yaml`
```yaml
globals:
  debug: True             # debug mode (True) or not (False)
  cloud: cloud_name       # name of cloud to use
  num_users: 3            # number of user systems to provision
  num_ranges: 1           # number of ranges to provision
  user_name: user_name    # user name prefix
  range_name: range_name  # range name prefix
  org_name: org_name      # name of organization
  artifacts: True         # artifacts (True) or not (False)
  provision:              # provision range (True) or not (False) or None

guacamole:
  provision: True         # provision guacamole (True) or not (False)
  update: False           # update guacamole users (True) or not (False)
  mapped_only: True       # only create connections for user mapped instances (True) or not (False)
  recording: True         # enable session recording (True) or not (False)
  sharing: write          # enable link sharing read (read), write (write) or not (False)

heat:
  provision: True         # provision heat (True) or not (False)
  update: True            # update heat (True) or not (False)
  template_dir: templates # directory containing heat templates
  pause: 2                # pause between each heat stack action

swift:
  provision: True         # provision swift (True) or not (False)
  update: True            # update swift (True) or not (False)
  asset_dir: assets       # directory containing swift assets
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