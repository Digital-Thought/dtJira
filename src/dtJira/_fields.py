
class Field:

    def __init__(self, field_detail, client):
        self.field_detail = field_detail
        self.client = client

    def __str__(self):
        return f"{self.name} / {self.id}"

    @property
    def id(self):
        return self.field_detail.get('id')

    @property
    def key(self):
        return self.field_detail.get('key')

    @property
    def name(self):
        return self.field_detail.get('name')

    @property
    def description(self):
        return self.field_detail.get('description')

    @property
    def navigable(self):
        return self.field_detail.get('navigable')

    @property
    def orderable(self):
        return self.field_detail.get('orderable')

    @property
    def schema(self):
        return self.field_detail.get('schema')

    @property
    def searchable(self):
        return self.field_detail.get('searchable')

    @property
    def untranslated_name(self):
        return self.field_detail.get('untranslatedName')

    @property
    def is_locked(self):
        return 'isLocked' in self.field_detail and self.field_detail['isLocked']

    @property
    def is_custom(self):
        return self.schema and 'custom' in self.schema

    def get_contexts(self):
        resp = self.client.get(f"/rest/api/3/field/{self.id}/context")
        resp.raise_for_status()
        return resp.json().get('values')

    def add_option(self, context, option, parent_option_id=None):
        if 'sub_items' in option:
            option.pop('sub_items')

        payload = {
            "options": [
                option
            ]
        }
        if parent_option_id:
            payload['options'][0]["optionId"] = parent_option_id

        resp = self.client.post(f"/rest/api/3/field/{self.id}/context/{context.get("id")}/option", data=payload)
        resp.raise_for_status()
        return resp.json()

    def add_options(self, context, options):
        for option in options:
            sub_items = option.get('sub_items')
            option_resp = self.add_option(context, option)
            if sub_items:
                parent_id = option_resp['options'][0]['id']
                for sub_item in sub_items:
                    self.add_option(context, sub_item, parent_id)

class Fields:

    def __init__(self, client):
        self.client = client

    @staticmethod
    def get_searcher_type(field_type):
        mapping = {
            "cascadingselect": "cascadingselectsearcher",
            "datepicker": "daterange",
            "datetime": "datetimerange",
            "float": "exactnumber or numberrange",
            "grouppicker": "grouppickersearcher",
            "importid": "exactnumber or numberrange",
            "labels": "labelsearcher",
            "multicheckboxes": "multiselectsearcher",
            "multigrouppicker": "multiselectsearcher",
            "multiselect": "multiselectsearcher",
            "multiuserpicker": "userpickergroupsearcher",
            "multiversion": "versionsearcher",
            "project": "projectsearcher",
            "radiobuttons": "multiselectsearcher",
            "readonlyfield": "textsearcher",
            "select": "multiselectsearcher",
            "textarea": "textsearcher",
            "textfield": "textsearcher",
            "url": "exacttextsearcher",
            "userpicker": "userpickergroupsearcher",
            "version": "versionsearcher",
        }

        return mapping.get(field_type, None)

    def create_field(self, field_type, field_name, description, options = None) -> Field:
        payload = {
            "name": field_name,
            "description": description,
            "type": f"com.atlassian.jira.plugin.system.customfieldtypes:{field_type}",
            "searcherKey": f"com.atlassian.jira.plugin.system.customfieldtypes:{self.get_searcher_type(field_type)}"
        }

        response = self.client.post("/rest/api/3/field", data=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to create custom field: {response.text}")

        field = Field(response.json(), self.client)
        if options:
            context = field.get_contexts()[0]
            field.add_options(context, options)

        return field

    def create_datepicker_field(self, field_name, description):
        return self.create_field("datepicker", field_name, description)

    def create_datetime_field(self, field_name, description):
        return self.create_field("datetime", field_name, description)

    def create_float_field(self, field_name, description):
        return self.create_field("float", field_name, description)

    def create_grouppicker_field(self, field_name, description):
        return self.create_field("grouppicker", field_name, description)

    def create_multiuserpicker_field(self, field_name, description):
        return self.create_field("multiuserpicker", field_name, description)

    def create_multigrouppicker_field(self, field_name, description):
        return self.create_field("multigrouppicker", field_name, description)

    def create_labels_field(self, field_name, description):
        return self.create_field("labels", field_name, description)

    def create_textarea_field(self, field_name, description):
        return self.create_field("textarea", field_name, description)

    def create_textfield_field(self, field_name, description):
        return self.create_field("textfield", field_name, description)

    def create_url_field(self, field_name, description):
        return self.create_field("url", field_name, description)

    def create_userpicker_field(self, field_name, description):
        return self.create_field("userpicker", field_name, description)

    def _create_multi_field(self, field_type, field_name, description):
        return self.create_field(field_type, field_name, description)

    def create_selects_field(self, field_name, description, options):
        return self._create_multi_field("select", field_name, description)

    def create_radiobuttons_field(self, field_name, description, options):
        return self._create_multi_field("radiobuttons", field_name, description)

    def create_multiselect_field(self, field_name, description, options):
        return self._create_multi_field("multiselect", field_name, description)

    def create_multi_checkboxes_field(self, field_name, description, options):
        return self._create_multi_field("multicheckboxes", field_name, description)

    def create_cascading_select_field(self, field_name, description, options):
        return self.create_field('cascadingselect', field_name, description)

    def delete_field(self, field: Field):
        resp = self.client.delete(f"/rest/api/3/field/{field.id}")
        resp.raise_for_status()

    def get_custom_field(self, name, description, field_type):
        for field in self.get_custom_fields():
            if field.name == name and field.description == description and field.schema['custom'].endswith(field_type):
                return field
        return None

    def get_non_custom_fields(self):
        _l = []
        for field in self.get_all():
            if not field.is_custom:
                _l.append(field)
        return _l

    def get_all(self):
        start_at = 0
        max_results = 50
        _l = []
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/field/search?startAt={start_at}&maxResults={max_results}&expand=isLocked")
            resp.raise_for_status()
            results = resp.json()
            is_last = results['isLast']
            start_at += max_results
            for value in results['values']:
                _l.append(Field(value, self.client))

        return _l

    def get_custom_fields(self):
        _l = []
        for field in self.get_all():
            if field.is_custom:
                _l.append(field)
        return _l
