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
- Create and Delete Users
- Create and Delete Connection Groups
- Create and Delete SSH and RDP Connections
- Associate Users and Connections 

## Requirements
To ensure proper functionality and usage, identified below is the baseline
directory structure and HOT parameters required for use of Range Provisioner.

**Project Repository Structure**  
```shell
DIR
|___ assets
|       |___ config.sh
|       |___ config.ps1
|
|___ templates
|       |___ main.yaml
|       |___ sec.yaml
|
|___ globals.yaml
```
_This provides the foundational directory structure for storing Heat Orchestration 
Templates in `templates`, `assets` to be uploaded to the object store and the base `globals.yaml` which defines specifics for how to deploy the Cyber Range_

### **Heat Orchestration Templates** 

_Expected parameters within the `main.yaml`_  
```shell
parameters:
  username: 
    type: string
    default: deafualt_username

  password:
    type: string
    default: default_password

  instance.num:
    type: string
    default: 2

  count:
    type: string
    default: default_instance_name

  tenant_id: 
    type: string
    default: openstack_project_id_value

  container_name:
    type: string
    default: range_provisioner

  conn_proto:
    type: comma_delimited_list
    default: "ssh"

```

_Expected parameters within the `sec.yaml`_
```shell
parameters:
  name: 
    type: string
    default: sec_group
```

#### Mappings to `globals.yaml`
**username**
- This maps to the `username_prefix` field

**password**
- This maps to the `guac_user_password` field in the `clouds.yaml` file

**count**
- This maps to the `num_users` field

**tenant_id**
- This maps to the `project_id` field in the `clouds.yaml` file

**container_name**
- This maps to the `container_name` field in the `main.yaml` file

**conn_proto**
- This defines the type of connections that will be created for the users. 
  - `ssh` - This will create SSH connections for the users
  - `rdp` - This will create RDP connections for the users
  - `ssh,rdp` - This will create both SSH and RDP connections for the users

**name**
- This maps to the `sec_group_name` field in the `sec.yaml` file

### Usage Example
To ensure easy of use the following provides an example CI/CD implementation utilizing Range
Provisioner to facilitate to creation and deletion of cyber range environments. The main source for the Docker Image is from `registry.gitlab.com/gacybercenter/gacyberrange/cloud-imaging/container-factory/range-provisioner:latest`, where you can also find previous versions.


```shell
default:
  image: registry.gitlab.com/gacybercenter/gacyberrange/cloud-imaging/container-factory/range-provisioner:latest
  before_script:
    - mv $(echo $clouds) clouds.yaml

stages:
  - Swift
  - Heat
  - Guacamole

guac_deprovision:
  stage: Guacamole
  script: |
      python3 /range-provisioner/manage_guac.py
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: $CI_COMMIT_MESSAGE =~ /\[delete]/
      allow_failure: true
      when: always

object_upload:
  stage: Swift
  script: |
      python3 /range-provisioner/manage_objects.py
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/)
      when: always

heat_deploy:
  stage: Heat
  script: |
      python3 /range-provisioner/manage_heat.py
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/)
      when: always

guac_provision:
  stage: Guacamole
  script: |
      python3 /range-provisioner/manage_guac.py
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - if: $CI_COMMIT_MESSAGE =~ /\[build]/
      when: always
```

Within the `rules` portion, this ensures that you will not have a double
pipeline trigger when you have an open merge request:
```shell
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
```

This allows determines when specific jobs will trigger based on the `$CI_COMMIT_MESAGE`
variable, as seen here by looking for `[build]` or `[delete]` at the beginning of a
commit message:
```shell
  rules:
    - if: ($CI_COMMIT_MESSAGE =~ /\[build]/ || $CI_COMMIT_MESSAGE =~ /\[delete]/)
      when: always
```