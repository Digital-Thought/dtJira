
class Workflow:

    def __init__(self, details, client):
        self.details = details
        self.client = client

    @property
    def default(self):
        return self.details['default']

    @property
    def id(self):
        return self.details['id']

    @property
    def description(self):
        return self.details['description']

    @property
    def last_modified_date(self):
        return self.details['lastModifiedDate']

    @property
    def last_modified_user(self):
        return self.details['lastModifiedUser']

    @property
    def last_modified_user_account_id(self):
        return self.details['lastModifiedUserAccountId']

    @property
    def name(self):
        return self.details['name']

    @property
    def entity_id(self):
        return self.details.get('entityId', self.details.get('id',{}).get('entityId'))

    @property
    def steps(self):
        return self.details['steps']


class WorkflowScheme:

    def __init__(self, details, client):
        self.details = details
        self.client = client

    @property
    def name(self):
        return self.details['name']

    @property
    def description(self):
        return self.details['description']

    @property
    def id(self):
        return self.details['id']

    @property
    def issue_type_mappings(self):
        return self.details['issueTypeMappings']

    def add_workflow_issue_type(self, issue_type, workflow):
        payload = {
            "issueType": issue_type.id,
            "updateDraftIfNeeded": True,
            "workflow": workflow
        }
        resp = self.client.put(f"/rest/api/3/workflowscheme/{self.id}/issuetype/{issue_type.id}", data=payload)
        resp.raise_for_status()
       

class Workflows:

    def __init__(self, client):
        self.client = client

    def get_all(self, active=True):
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(
                path=f'/rest/api/3/workflow/search?startAt={start_at}&maxResults={max_results}&isActive={active}')
            is_last = resp.json()['isLast']
            start_at += max_results
            for p in resp.json()['values']:
                _l.append(Workflow(p, self.client))
        return _l

    def create(self, name, description, workflow_definition, project):
        statuses = self.client.statuses().get_all()
        workflow_statuses = []
        transitions = []
        for status in workflow_definition.get('statuses', []):
            workflow_status = None
            for s in statuses:
                if s.name == status['name']:
                    workflow_status = s
                    break
            if workflow_status is None:
                workflow_status = self.client.statuses().create(status['name'], status['type'])

            if workflow_status.status_category != status['type']:
                raise Exception(f"A status of {status['name']} already exists but has a different status category")
            workflow_statuses.append(workflow_status)

        for transition in workflow_definition.get('transitions', []):
            t = {
                'name': transition['name'],
                'type': transition['type'],
                'to': self.get_status_id_from_name(transition['to']),
                'rules': {}
            }

            if 'from' in transition:
                t['from'] = []
                for trf in transition['from']:
                    t['from'].append(self.get_status_id_from_name(trf))

            if 'conditions' in transition:
                t['rules']['conditions'] = transition['conditions']
                for condition in t['rules']['conditions']['conditions']:
                    if 'configuration' in condition:
                        condition['configuration'] = self.map_replace_configurations(condition['configuration'], project)

            if 'validators' in transition:
                t['rules']['validators'] = transition['validators']
                for condition in t['rules']['validators']:
                    if 'configuration' in condition:
                        condition['configuration'] = self.map_replace_configurations(condition['configuration'], project)

            transitions.append(t)

        status_ids = []
        for status in workflow_statuses:
            status_ids.append({'id': status.id})
        payload = {
            'name': name,
            'description': description,
            'statuses': status_ids,
            'transitions': transitions,
        }

        resp = self.client.post('/rest/api/3/workflow', data=payload)
        resp.raise_for_status()
        return Workflow(resp.json(), self.client)

    def map_replace_configurations(self, configuration, project):
        if 'statuses' in configuration:
            statuses = []
            for status in configuration['statuses']:
                statuses.append({"id": self.get_status_id_from_name(status)})
            configuration['statuses'] = statuses

        if 'fieldId' in configuration:
            configuration['fieldId'] = self.get_field_id_from_name(configuration['fieldId'], project.project_fields)

        if 'fieldIds' in configuration:
            field_ids = []
            for field_id in configuration['fieldIds']:
                field_ids.append(self.get_field_id_from_name(field_id, project.project_fields))
            configuration['fieldIds'] = field_ids

        return configuration

    def get_field_id_from_name(self, name, project_fields):
        for field in project_fields:
            if field.name == name:
                return field.id

    def get_status_id_from_name(self, name):
        statuses = self.client.statuses().get_all()
        for status in statuses:
            if status.name == name:
                return status.id

    def get_all_workflow_schemes(self) -> list:
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/workflowscheme?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(WorkflowScheme(val, self.client))
        return _l

    def get_workflow_scheme_for_project(self, project) -> WorkflowScheme:
        resp = self.client.get(f"/rest/api/3/workflowscheme/project?projectId={project.id}")
        resp.raise_for_status()
        for v in resp.json()['values']:
            return WorkflowScheme(v.get('workflowScheme'), self.client)
        return None

    def delete_workflow_scheme(self, workflow: WorkflowScheme):
        resp = self.client.delete(f"/rest/api/3/workflowscheme/{workflow.id}")
        resp.raise_for_status()

    def delete_inactive_workflow(self, workflow: Workflow):
        resp = self.client.delete(f"/rest/api/3/workflow/{workflow.entity_id}")
        resp.raise_for_status()