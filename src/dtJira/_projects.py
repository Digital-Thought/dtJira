import logging

from dtJira._issues import Issues


class Project:

    def __init__(self, project_detail, client, skip_load=False):
        self.project_detail = project_detail
        self.client = client
        self.project_fields = []
        self.issue_types = []
        self.issue_type_schemes = []
        self.issue_type_scheme_mappings = {}
        self.screens = []
        self.screen_tabs = {}
        self.screen_schemes = []
        self.issue_type_screen_schemes = []
        self.workflows = []

        if not skip_load:
            self._load_project_settings()

    def issues(self) -> Issues:
        return Issues(self, self.client)

    def _load_project_settings(self):
        self.issue_type_schemes = self.client.issue_types().get_all_issue_type_schemes_for_project(self)
        self.issue_type_screen_schemes = self.client.issue_types().get_issue_type_screen_schemes(self)
        for i in self.issue_type_screen_schemes:
            resp = self.client.get(
                path=f'/rest/api/3/issuetypescreenscheme/mapping?issueTypeScreenSchemeId={i.id}')
            resp.raise_for_status()
            self.issue_type_scheme_mappings[i.id] = resp.json()['values']

        processed_screen_scheme_ids = []
        for i in self.issue_type_scheme_mappings:
            for v in self.issue_type_scheme_mappings[i]:
                screen_scheme_id = v['screenSchemeId']
                if screen_scheme_id not in processed_screen_scheme_ids:
                    self.screen_schemes.append(self.client.screens().get_screen_scheme(screen_scheme_id))
                    processed_screen_scheme_ids.append(screen_scheme_id)


        self.issue_types.extend(self.client.issue_types().get_all(self.id))

        processed_screen_ids = []
        for ss in self.screen_schemes:
            for screen_id in ss.get_screen_ids():
                if screen_id not in processed_screen_ids:
                    self.screens.append(self.client.screens().get_screen(screen_id))
                    processed_screen_ids.append(screen_id)

        for screen in self.screens:
            self.screen_tabs[screen.id] = screen.get_tabs(self)

        field_ids = []
        for screen_id, tabs in self.screen_tabs.items():
            for tab in tabs:
                resp = self.client.get(path=f"/rest/api/3/screens/{screen_id}/tabs/{tab['id']}/fields")
                resp.raise_for_status()
                for field in resp.json():
                    if field['id'] not in field_ids:
                        field_ids.append(field['id'])

        all_fields = self.client.fields().get_all()
        for i in field_ids:
            for f in all_fields:
                if f.id == i:
                    self.project_fields.append(f)

    @property
    def id(self):
        return self.project_detail['id']

    @property
    def key(self):
        return self.project_detail['key']

    @property
    def name(self):
        return self.project_detail['name']

    @property
    def project_type_key(self):
        return self.project_detail['projectTypeKey']

    @property
    def simplified(self):
        return self.project_detail['simplified']

    @property
    def style(self):
        return self.project_detail['style']

    @property
    def is_private(self):
        return self.project_detail['isPrivate']

    @property
    def properties(self):
        return self.project_detail['properties']

    @property
    def entity_id(self):
        return self.project_detail['entityId']

    @property
    def uuid(self):
        return self.project_detail['isPrivate']

    def assign_fields(self, field_defs: list, auto_create: bool = True):
        for field_def in field_defs:
            field = self.client.fields().get_custom_field(field_def.get('name'), field_def.get('description', ''),
                                                          field_def.get('type'))
            if field is None and auto_create:
                field = self.client.fields().create_field(field_def.get('type'), field_def.get('name'),
                                                  field_def.get('description', ''), field_def.get('options'))

            if field is not None:
                self.project_fields.append(field)


    def assign_issue_type_screen_scheme(self, issue_type_screen_scheme):
        payload = {
            "issueTypeScreenSchemeId": issue_type_screen_scheme.id,
            "projectId": self.id
        }
        resp = self.client.put(f"/rest/api/3/issuetypescreenscheme/project", data=payload)
        resp.raise_for_status()
        self.issue_type_screen_schemes.append(issue_type_screen_scheme)

    def assign_issue_type_scheme(self, issue_type_scheme):
        payload = {
            "issueTypeSchemeId": issue_type_scheme.id,
            "projectId": self.id
        }
        resp = self.client.put(f"/rest/api/3/issuetypescheme/project", data=payload)
        resp.raise_for_status()
        self.issue_type_schemes.append(issue_type_scheme)

    def assign_workflow_scheme(self, workflow_scheme):
        payload = {
            "workflowSchemeId": workflow_scheme.id,
            "projectId": self.id
        }

        resp = self.client.put(f"/rest/api/3/workflowscheme/project", data=payload)
        resp.raise_for_status()

    def get_screen(self, name):
        for screen in self.screens:
            if screen.name == name:
                return screen
        return None

    def get_issue_type(self, name):
        for issue_type in self.issue_types:
            if issue_type.name == name:
                return issue_type
        return None

    def get_screen_scheme(self, name):
        for screen_scheme in self.screen_schemes:
            if screen_scheme.name == name:
                return screen_scheme
        return None

class Projects:

    def __init__(self, client):
        self.client = client

    def delete_project(self, project, enable_undo=False):
        resp = self.client.delete(f"/rest/api/3/project/{project.id}?enableUndo={enable_undo}")
        resp.raise_for_status()

    def get_all(self, status='live'):
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(path=f'/rest/api/3/project/search?startAt={start_at}&maxResults={max_results}&status={status}')
            is_last = resp.json()['isLast']
            start_at += max_results
            for p in resp.json()['values']:
                _l.append(Project(p, self.client, skip_load=status=='deleted'))
        return _l

    def get_project(self, project_key):
        _l = []
        resp = self.client.get(path=f'/rest/api/3/project/{project_key}')
        resp.raise_for_status()
        return Project(resp.json(), self.client)

    def apply_template(self, project: Project, template: dict):
        logging.info(f'Applying Template "{template.get('name')}" to {project.key}')
        project.assign_fields(template.get('fields'))
        workflow_scheme = self.client.workflows().get_workflow_scheme_for_project(project)

        self.client.groups().create_groups(template.get('groups', []))

        target_issue_type_scheme = None
        for issue_type_scheme in project.issue_type_schemes:
            if not issue_type_scheme.is_default:
                target_issue_type_scheme = issue_type_scheme
                break

        for issue_type_def in template.get('issue_types'):
            logging.info(f'Applying Issue Type "{issue_type_def.get("name")}" to {project.key}')
            issue_type = self.client.issue_types().create(f"{project.key}: {issue_type_def['name']}", issue_type_def['description'],
                                                              issue_type_def['subtask'])
            project.issue_types.append(issue_type)
            target_issue_type_scheme.add_issue_type([issue_type])

        for screen_def in template.get('screens', []):
            logging.info(f'Applying Screen Def "{screen_def.get("name")}" to {project.key}')
            screen = self.client.screens().create(f"{project.key}: {screen_def['name']}", screen_def['description'])
            project.screens.append(screen)

        logging.info(f'Applying Screen Tabs to {project.key}')
        for screen_tab_def in template.get('screen_tabs', []):
            for screen in project.screens:
                if screen.name == f"{project.key}: {screen_tab_def['screen']}":
                    field_ids = []
                    for field in project.project_fields:
                        for field_name in screen_tab_def['fields']:
                            if field.name == field_name:
                                field_ids.append(field.id)
                                break

                    tab = screen.create_tab(screen_tab_def['name'], field_ids)
                    if screen.id not in project.screen_tabs:
                        project.screen_tabs[screen.id] = []
                    project.screen_tabs[screen.id].append(tab)

        for screen_schemes_def in template.get('screen_schemes', []):
            logging.info(f'Applying Screen Scheme Def "{screen_schemes_def['name']}" to {project.key}')
            name = f"{project.key}: {screen_schemes_def['name']}"
            resp = self.client.screens().create_screen_scheme(name, screen_schemes_def['description'],
                                                              default=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                                                              edit=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                                                              view=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id)

            project.screen_schemes.append(resp)

        for issue_type_screen_scheme_def in template.get('issue_type_screen_schemes', []):
            logging.info(f'Applying Screen/Issue Scheme to {project.key}')
            issue_type_screen_scheme = project.issue_type_screen_schemes[0]
            for mapping_def in issue_type_screen_scheme_def['mappings']:
                issue_type_screen_scheme.add_mapping(project.get_issue_type(f"{project.key}: {mapping_def['issue_type']}"),
                                                     project.get_screen_scheme(f"{project.key}: {mapping_def['screen_scheme']}"))

        for workflow_def in template.get('workflows', []):
            logging.info(f'Applying Workflow "{workflow_def['name']}" to {project.key}')
            workflow_name = f"{project.key}: {workflow_def['name']}"
            workflow = self.client.workflows().create(workflow_name, workflow_def['description'], workflow_def, project)
            project.workflows.append(workflow)

        logging.info(f'Applying Workflow Scheme to {project.key}')
        for workflow_scheme_def in template.get('workflow_schemes', []):
            for mapping in workflow_scheme_def['issueTypeMappings']:
                workflow_scheme.add_workflow_issue_type(project.get_issue_type(f"{project.key}: {mapping['issue_type']}"),
                                                        f"{project.key}: {mapping['workflow']}")

        return project


    def create(self, name: str, key: str, template: dict):
        payload = {
            "key": key,
            "name": name,
            "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-kanban-classic",
            "projectTypeKey": "software",
            "assigneeType": "UNASSIGNED",
            "leadAccountId": self.client.get_me()['accountId']
        }
        self.client.groups().create_groups(template.get('groups', []))
        resp = self.client.post(path='/rest/api/3/project', data=payload)
        resp.raise_for_status()
        project = Project(resp.json(), self.client)
        logging.info(f'Applying Template "{template.get('name')}" to {project.key}')
        project.assign_fields(template.get('fields'))

        for issue_type_def in template.get('issue_types'):
            logging.info(f'Applying Issue Type "{issue_type_def.get("name")}" to {project.key}')
            issue_type = self.client.issue_types().create(f"{project.key}: {issue_type_def['name']}", issue_type_def['description'],
                                                              issue_type_def['subtask'])
            project.issue_types.append(issue_type)

        for issue_type_scheme_def in template.get('issue_type_schemes'):
            target_issue_type_ids = []
            for target_issue_type in issue_type_scheme_def.get('issue_types'):
                for issue_type in project.issue_types:
                    if issue_type.name == f"{project.key}: {target_issue_type}":
                        target_issue_type_ids.append(issue_type.id)

            issue_type_scheme = self.client.issue_types().create_issue_type_scheme(f"{project.key}: {issue_type_scheme_def['name']}",
                                                                           issue_type_scheme_def['description'],
                                                                           target_issue_type_ids)
            project.assign_issue_type_scheme(issue_type_scheme)

        for screen_def in template.get('screens', []):
            logging.info(f'Applying Screen Def "{screen_def.get("name")}" to {project.key}')
            screen = self.client.screens().create(f"{project.key}: {screen_def['name']}", screen_def['description'])
            project.screens.append(screen)

        logging.info(f'Applying Screen Tabs to {project.key}')
        for screen_tab_def in template.get('screen_tabs', []):
            for screen in project.screens:
                if screen.name == f"{project.key}: {screen_tab_def['screen']}":
                    field_ids = []
                    for field in project.project_fields:
                        for field_name in screen_tab_def['fields']:
                            if field.name == field_name:
                                if field.id not in field_ids:
                                    field_ids.append(field.id)
                                break

                    tab = screen.create_tab(screen_tab_def['name'], field_ids)
                    if screen.id not in project.screen_tabs:
                        project.screen_tabs[screen.id] = []
                    project.screen_tabs[screen.id].append(tab)

        for screen_schemes_def in template.get('screen_schemes', []):
            logging.info(f'Applying Screen Scheme Def "{screen_schemes_def['name']}" to {project.key}')
            name = f"{project.key}: {screen_schemes_def['name']}"
            resp = self.client.screens().create_screen_scheme(name, screen_schemes_def['description'],
                                                              default=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                                                              edit=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                                                              view=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id)

            project.screen_schemes.append(resp)

        for issue_type_screen_scheme_def in template.get('issue_type_screen_schemes', []):
            logging.info(f'Applying Screen/Issue Scheme to {project.key}')
            issue_type_screen_scheme_name = f"{project.key}: {issue_type_screen_scheme_def['name']}"
            mappings = []
            for mapping_def in issue_type_screen_scheme_def['mappings']:
                    mappings.append({
                        'issueTypeId': project.get_issue_type(f"{project.key}: {mapping_def['issue_type']}").id,
                        'screenSchemeId': project.get_screen_scheme(f"{project.key}: {mapping_def['screen_scheme']}").id
                    })
            mappings.append({'issueTypeId': 'default',
                             'screenSchemeId': project.get_screen_scheme(f"{project.key}: {issue_type_screen_scheme_def['default_screen_scheme']}").id})

            i = self.client.issue_types().create_issue_type_screen_scheme(issue_type_screen_scheme_name,
                                                                  issue_type_screen_scheme_def['description'],
                                                                   mappings)
            project.assign_issue_type_screen_scheme(i)

        for workflow_def in template.get('workflows', []):
            logging.info(f'Applying Workflow "{workflow_def['name']}" to {project.key}')
            workflow_name = f"{project.key}: {workflow_def['name']}"
            workflow = self.client.workflows().create(workflow_name, workflow_def['description'], workflow_def, project)
            project.workflows.append(workflow)

        logging.info(f'Applying Workflow Scheme to {project.key}')
        for workflow_scheme_def in template.get('workflow_schemes', []):
            payload = {
                "name": f"{project.key}: {workflow_scheme_def['name']}",
                "description": workflow_scheme_def['description'],
                "defaultWorkflow": workflow_scheme_def['defaultWorkflow'],
                "issueTypeMappings": {}
            }

            for mapping in workflow_scheme_def['issueTypeMappings']:
                issue_type_id = project.get_issue_type(f"{project.key}: {mapping['issue_type']}").id
                workflow_name = f"{project.key}: {mapping['workflow']}"
                payload["issueTypeMappings"][f"{issue_type_id}"] = workflow_name

            resp = self.client.post(path='/rest/api/3/workflowscheme', data=payload)
            resp.raise_for_status()
            workflow_scheme_id = resp.json()['id']

            payload = {
                "projectId": project.id,
                "workflowSchemeId": workflow_scheme_id
            }

            resp = self.client.put(path='/rest/api/3/workflowscheme/project', data=payload)
            resp.raise_for_status()

        return project