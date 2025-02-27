# dtJira

## Overview

`dtJira` is a Python module that provides a client to interact with Jira Cloud via its REST API. It enables users to manage Jira projects, issues, workflows, fields, and groups programmatically. The library leverages the `jira` Python package and `requests` for API communication.

## Features

- Authenticate and interact with Jira Cloud using Basic Authentication.
- Manage Jira issues, projects, workflows, and fields.
- Retrieve and modify issue types, statuses, and groups.
- Access project configurations such as screen schemes and field mappings.
- Perform HTTP requests with session management.
- Deploy project setups defined in YAML files.

## Installation

Ensure you have Python 3.7+ installed, then install the required dependencies:

```sh
pip install jira requests
```

## Usage

### Initializing the Jira Client

```python
from dtJira import JiraClient

jira = JiraClient(url='https://your-jira-instance.atlassian.net', username='your-email', password='your-api-token')
```

### Retrieving Projects

```python
from dtJira.projects import Project

project = Project(jira.get_project('PROJECT_KEY'), jira)
print(project.name)
```

### Managing Issues

```python
from dtJira.issues.types import IssueType

issue_type = IssueType(jira.get_issue_type('10001'), jira)
print(issue_type.name)
```

### Handling Workflows

```python
from dtJira.workflows import Workflow

workflow = Workflow(jira.get_workflow('workflow_name'), jira)
print(workflow.details)
```

### Managing Fields

```python
from dtJira.fields import Field

field = Field(jira.get_field('customfield_10000'), jira)
print(field.id)
```

### Managing Groups

```python
from dtJira.groups import Group

group = Group(jira.get_group('group_name'), jira)
print(group.name)
```

## Deployment via YAML

### Overview
The `dtJira` module allows deploying Jira project configurations using YAML files. This feature enables users to define issue types, workflows, screen schemes, groups, and fields in a structured manner, which can then be deployed programmatically.

### Example YAML File
Below is an example YAML file that defines a Jira project setup:

```yaml
name: Template Name

groups:
  - group-1
  - group-2
  - group-3

fields:
  - name: Outcome
    description: Description of field
    type: select
    options:
      - value: Approved
      - value: Approved with Conditions
      - value: Not Approved

  - name: Rating
    description: Description of field
    type: select
    options:
      - value: High
      - value: Medium
      - value: Low

issue_types:
  - name: My Issue
    description: Description of Issue
    subtask: false

workflows:
  - name: Issue Workflow
    description: Workflow Issue
    statuses:
      - name: Request Submitted
        type: TODO
      - name: Approved
        type: DONE
```

### Deploying a YAML Configuration

To deploy a YAML configuration file, use the following command:

```python
from dtJira import JiraClient

jira = JiraClient(url='https://your-jira-instance.atlassian.net', username='your-email', password='your-api-token')

jira.deploy_from_yaml('config.yaml')
```

This will read the YAML file and apply the specified configuration to the Jira instance.

## Module Structure

- `dtJira`
  - `JiraClient`: Main client for interacting with Jira Cloud.
  - `fields`: Manages Jira fields and metadata.
  - `issues`: Handles Jira issue types.
  - `projects`: Manages project configurations.
  - `workflows`: Handles Jira workflows and statuses.
  - `groups`: Manages Jira user groups and permissions.

## Authentication

This library uses Basic Authentication with an API token. You can generate an API token from Atlassian here.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Feel free to submit a pull request or raise an issue.

## Support

For any issues or feature requests, please open an issue in the repository.
