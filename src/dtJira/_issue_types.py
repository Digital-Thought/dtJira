
class IssueType:

    def __init__(self, type_detail, client):
        self.type_detail = type_detail
        self.client = client

    @property
    def id(self):
        return self.type_detail['id']

    @property
    def name(self):
        return self.type_detail['name']

    @property
    def description(self):
        return self.type_detail['description']

    @property
    def subtask(self):
        return self.type_detail['subtask']

    @property
    def icon_url(self):
        return self.type_detail['iconUrl']

    @property
    def avatar_id(self):
        return self.type_detail['avatarId']

    @property
    def hierarchy_level(self):
        return self.type_detail['hierarchyLevel']

class IssueTypeScheme:

    def __init__(self, scheme_detail, client):
        self.scheme_detail = scheme_detail
        self.client = client

    @property
    def id(self):
        return self.scheme_detail.get('issueTypeScheme', self.scheme_detail.get('id', self.scheme_detail.get('issueTypeSchemeId')))

    @property
    def is_default(self):
        return self.scheme_detail.get('isDefault')

    def add_issue_type(self, issue_type):
        id_ = []
        for i in issue_type:
            id_.append(i.id)
        payload = {
            "issueTypeIds": id_
        }

        resp = self.client.put(f"/rest/api/3/issuetypescheme/{self.id}/issuetype", data=payload)
        resp.raise_for_status()

class IssueTypeScreenScheme:

    def __init__(self, detail, client):
        self.detail = detail
        self.client = client

    @property
    def id(self):
        return self.detail.get('issueTypeScreenScheme', self.detail)['id']

    def add_mapping(self, issue_type, screen_scheme):
        payload = {
            "issueTypeMappings": [
                {
                    "issueTypeId": issue_type.id,
                    "screenSchemeId": screen_scheme.id
                }
            ]
        }
        resp = self.client.put(f"/rest/api/3/issuetypescreenscheme/{self.id}/mapping", data=payload)
        resp.raise_for_status()

class IssueTypes:

    def __init__(self, client):
        self.client = client

    def create(self, name, description, subtask) -> IssueType:
        hierarchy = -1 if subtask else 0
        payload = {
            "name": name,
            "description": description,
            "hierarchyLevel": hierarchy
        }

        resp = self.client.post("/rest/api/2/issuetype", data=payload)
        resp.raise_for_status()
        return IssueType(resp.json(), self.client)

    def delete(self, issue_type: IssueType):
        resp = self.client.delete(f"/rest/api/2/issuetype/{issue_type.id}")
        resp.raise_for_status()

    def get_all(self, project_id):
        resp = self.client.get(f"/rest/api/3/issuetype/project?projectId={project_id}")
        resp.raise_for_status()
        _l = []
        for _p in resp.json():
            _l.append(IssueType(_p, self.client))
        return _l

    def get_all_user_issue_types(self):
        resp = self.client.get(f"/rest/api/3/issuetype")
        resp.raise_for_status()
        _l = []
        for _p in resp.json():
            _l.append(IssueType(_p, self.client))
        return _l

    def create_issue_type_scheme(self, name, description, issue_types) -> IssueTypeScheme:
        payload = {
            "name": name,
            "description": description,
            "issueTypeIds": issue_types
        }

        resp = self.client.post(f"/rest/api/3/issuetypescheme", data=payload)
        resp.raise_for_status()
        return IssueTypeScheme(resp.json(), self.client)

    def create_issue_type_screen_scheme(self, name, description, mapping) -> IssueTypeScreenScheme:
        payload = {
            "name": name,
            "description": description,
            "issueTypeMappings": mapping
        }
        resp = self.client.post(f"/rest/api/3/issuetypescreenscheme", data=payload)
        resp.raise_for_status()
        return IssueTypeScreenScheme(resp.json(), self.client)

    def delete_issue_type_screen_scheme(self, issue_type_screen_scheme: IssueTypeScreenScheme):
        resp = self.client.delete(f"/rest/api/3/issuetypescreenscheme/{issue_type_screen_scheme.id}")
        resp.raise_for_status()

    def get_issue_type_screen_schemes(self, project) -> list:
        _l = []

        resp = self.client.get(f"/rest/api/3/issuetypescreenscheme/project?projectId={project.id}")
        resp.raise_for_status()
        for val in resp.json().get('values', []):
            _l.append(IssueTypeScreenScheme(val, self.client))

        return _l

    def delete_issue_screen_scheme(self, issue_type_screen_scheme: IssueTypeScreenScheme):
        resp = self.client.delete(f"/rest/api/3/issuetypescreenscheme/{issue_type_screen_scheme.id}")
        resp.raise_for_status()

    def get_all_issue_type_screen_schemes(self) -> list:
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/issuetypescreenscheme?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(IssueTypeScreenScheme(val, self.client))
        return _l

    def get_all_issue_type_schemes(self) -> list:
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/issuetypescheme?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(IssueTypeScheme(val, self.client))
        return _l

    def get_all_issue_type_schemes_for_project(self, project) -> list:
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/issuetypescheme?startAt={start_at}&maxResults={max_results}&projectId={project.id}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(IssueTypeScheme(val, self.client))
        return _l

    def delete_issue_type_scheme(self, issue_type_scheme: IssueTypeScheme):
        resp = self.client.delete(f"/rest/api/3/issuetypescheme/{issue_type_scheme.id}")
        resp.raise_for_status()
