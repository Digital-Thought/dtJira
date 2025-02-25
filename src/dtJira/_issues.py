import logging
import re

class Issue:
    def __init__(self, detail, client, issue_type, get_field):
        self.detail = detail
        self.client = client
        self.issue_type = issue_type
        self.get_field = get_field


    def _format_doc(self, doc):
        response = ''
        if doc:
            for c in doc:
                if c['type'] == 'text':
                    response += c['text']
                elif c['type'] == 'paragraph':
                    response += f'\n{self._format_doc(c["content"])}\n'
                elif c['type'] == 'heading':
                    response += f'\n{c["text"]}\n'
                elif c['type'] == 'code':
                    response += f'\n{c["text"]}\n'
                else:
                    response += f'\n{c["text"]}\n'
        return response

    def _format_value(self, value):
        if isinstance(value, list):
            values = []
            for v in value:
                values.append(v['value'])
            return values
        if isinstance(value, dict):
            if value.get('type', '') == 'doc':
                return self._format_doc(value.get('content')).strip()
            if 'value' in value:
                v = value['value']
                if v in ['false', 'true']:
                    return v == 'true'
                else:
                    return v
        else:
            return value

    def get_value(self, field_name):
        field = self.get_field(self.issue_type, field_name)
        return self._format_value(self.detail['fields'][field['fieldId']])

    @property
    def creator(self):
        return self.detail['fields']['creator']

    @property
    def description(self):
        return self._format_value(self.detail['fields']['description'])

    @property
    def subtasks(self):
        return self.detail['fields']['subtasks']

    @property
    def reporter(self):
        return self.detail['fields']['reporter']

    @property
    def summary(self):
        return self.detail['fields']['summary']

    @property
    def assignee(self):
        return self.detail['fields']['assignee']

    @property
    def status(self):
        return self.detail['fields']['status']['name']

    @property
    def key(self):
        return self.detail['key']

    @property
    def id(self):
        return self.detail['id']

class Issues:

    def __init__(self, project, client):
        self.project = project
        self.client = client
        self.issue_types = self._get_create_meta()
        self.issue_type_field_metadata = self._get_create_meta_field_metadata()

    @staticmethod
    def strip_html_and_format(text):
        # Replace paragraph and <br> tags with a newline
        text = re.sub(r'<p.*?>', '\n', text)  # Open <p> tags replaced with \n
        text = text.replace('</p>', '\n')  # Closing </p> tags replaced with \n
        text = text.replace('<br>', '\n')  # Replace <br> with \n
        text = text.replace('<br />', '\n')  # Replace self-closed <br /> with \n

        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    def _get_create_meta(self):
        resp = self.client.get(
            path=f'/rest/api/3/issue/createmeta/{self.project.id}/issuetypes')
        resp.raise_for_status()
        return resp.json()['issueTypes']

    def _get_create_meta_field_metadata(self):
        meta = {}
        for issue_type in self.issue_types:
            resp = self.client.get(
                path=f'/rest/api/3/issue/createmeta/{self.project.id}/issuetypes/{issue_type['id']}?maxResults=200')
            resp.raise_for_status()
            meta[issue_type['id']] = resp.json()['fields']
        return meta

    def get_allowed_value_id(self, allowed_values, my_value):
        for allowed_value in allowed_values:
            if allowed_value['value'] == my_value:
                return allowed_value['id']
            if str(my_value).upper() == 'YES' and allowed_value['value'] == 'true':
                return allowed_value['id']
            if str(my_value).upper() == 'NO' and allowed_value['value'] == 'false':
                return allowed_value['id']
        return None


    def format_textarea_resp(self, value):
        value = self.strip_html_and_format(value)
        resp = {
                "content": [],
                "type": "doc",
                "version": 1
                }
        for val in value.split('\n'):
            resp['content'].append({
                "content": [
                    {
                        "text": val,
                        "type": "text"
                    }
                ],
                "type": "paragraph"
            })

        return resp

    def format_field_data(self, issue_type, field_name, value):
        field = self.get_field(issue_type, field_name)
        if field is None:
            return None, None

        field_scheme = field.get('schema').get('type')
        custom = field.get('schema').get('custom')
        if field_scheme == 'string':
            if custom.endswith('textfield'):
                return field.get('key'), value
            elif custom.endswith('textarea'):
                return field.get('key'), self.format_textarea_resp(value)
            else:
                return field.get('key'), value
        elif field_scheme == 'array':
            array_values = []
            if isinstance(value, dict):
                for key in value:
                    val_id = self.get_allowed_value_id(field.get('allowedValues'), value[key])
                    if val_id:
                        array_values.append({"id": val_id})
            else:
                for val in value:
                    if isinstance(val, str):
                        val_id = self.get_allowed_value_id(field.get('allowedValues'), val)
                    elif isinstance(val, dict):
                        for key in val:
                            val_id = self.get_allowed_value_id(field.get('allowedValues'), val[key])
                    else:
                        val_id = None
                        logging.error(f'When processing ARRAY values.  The instance type was not fond for {str(val)}')

                    if val_id:
                        array_values.append({"id": val_id})

            return field.get('key'), array_values
        elif field_scheme == 'option':
            val_id = self.get_allowed_value_id(field.get('allowedValues'), value)
            if val_id:
                return field.get('key'), {"id": val_id}
            else:
                logging.error(f'Could not find value id for "{value}"')
                return None, None
        else:
            logging.error(f'Could not find translation for "{field_scheme}/{custom}"')
            return None, None

    def get_field(self, issue_type, field_name):
        for field in self.issue_type_field_metadata[issue_type['id']]:
            if field['name'] == field_name:
                return field
        return None

    def get_issues_updated_last_days(self, issue_type, days):
        relevant_issue_type = None
        for it in self.issue_types:
            if it['name'].endswith(issue_type):
                relevant_issue_type = it

        if relevant_issue_type is None:
            logging.error(f'Could not find issue type "{issue_type}"')
            return []

        jql = f'project="{self.project.key}" AND issuetype="{relevant_issue_type['name']}" AND updated >= "-{days}d"'
        resp = self.client.get(path=f'/rest/api/3/search?jql={jql}')
        resp.raise_for_status()
        results = []
        for issue in resp.json()['issues']:
            results.append(Issue(issue, self.client, relevant_issue_type, self.get_field))
        return results

    def create_issue(self, issue_type, summary, description='', fields={}, parent_issue: Issue=None):
        payload = {
            "fields": {
                "project": {
                    "id": self.project.id
                },
                "summary": summary,
                "description": self.format_textarea_resp(description),
                "issuetype": {
                    "id": issue_type['id']
                }
            }
        }

        if parent_issue:
            payload['fields']['parent'] = {'key': parent_issue.key}

        for field in fields:
            try:
                if fields[field]:
                    field_key, val = self.format_field_data(issue_type, field, fields[field])
                    if field_key:
                        payload['fields'][field_key] = val
                    else:
                        logging.error(f'Could not find field key for "{field}"')
            except Exception as e:
                logging.exception(f'Field {field}: {e}')
                continue

        resp = self.client.post(path=f'/rest/api/3/issue', data=payload)
        resp.raise_for_status()
        resp = self.client.get(path=f'/rest/api/3/issue/{resp.json()['key']}')
        resp.raise_for_status()
        return Issue(resp.json(), self.client, issue_type, self.get_field)