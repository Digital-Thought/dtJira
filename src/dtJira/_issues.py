import logging
import re

class Issue:
    def __init__(self, detail, client):
        self.detail = detail
        self.client = client

    @property
    def status(self):
        return self.detail['fields']['status']['name']

    @property
    def key(self):
        return self.detail['key']

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

    def create_issue(self, issue_type, summary, description='', fields={}):
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

        for field in fields:
            if fields[field]:
                field_key, val = self.format_field_data(issue_type, field, fields[field])
                if field_key:
                    payload['fields'][field_key] = val
                else:
                    logging.error(f'Could not find field key for "{field}"')

        resp = self.client.post(path=f'/rest/api/3/issue', data=payload)
        resp.raise_for_status()
        resp = self.client.get(path=f'/rest/api/3/issue/{resp.json()['key']}')
        resp.raise_for_status()
        return Issue(resp.json(), self.client)