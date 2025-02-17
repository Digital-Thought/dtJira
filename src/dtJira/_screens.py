
class Screen:

    def __init__(self, screen_detail, client):
        self.screen_detail = screen_detail
        self.client = client

    @property
    def id(self):
        return self.screen_detail['id']

    @property
    def name(self):
        return self.screen_detail['name']

    @property
    def description(self):
        return self.screen_detail['description']

    def get_tabs(self, project):
        resp = self.client.get(path=f'/rest/api/3/screens/{self.id}/tabs?projectKey={project.id}')
        resp.raise_for_status()
        return resp.json()

    def create_tab(self, name, fields):
        payload = {
            'name': name,
        }
        resp = self.client.post(path=f'/rest/api/3/screens/{self.id}/tabs', data=payload)
        resp.raise_for_status()
        tab_detail = resp.json()
        for field in fields:
            payload = {
                'fieldId': field,
            }
            resp = self.client.post(path=f'/rest/api/3/screens/{self.id}/tabs/{tab_detail["id"]}/fields', data=payload)
            resp.raise_for_status()

        return tab_detail

class ScreenScheme:

    def __init__(self, detail, client):
        self.detail = detail
        self.client = client

    @property
    def id(self):
        return self.detail['id']

    @property
    def name(self):
        return self.detail['name']

    @property
    def description(self):
        return self.detail['description']

    def get_screen_ids(self):
        _l = []
        for screen in self.detail['screens']:
            if self.detail['screens'][screen] not in _l:
                _l.append(self.detail['screens'][screen])
        return _l


class Screens:

    def __init__(self, client):
        self.client = client

    def create(self, name, description):
        payload = {
            "name": name,
            "description": description
        }
        resp = self.client.post("/rest/api/2/screens", data=payload)
        resp.raise_for_status()
        return Screen(resp.json(), self.client)

    def create_screen_scheme(self, name, description, default, edit, view) -> ScreenScheme:
        payload = {
            "name": name,
            "description": description,
            'screens': {
                'edit': edit,
                'view': view,
                'default': default
            }
        }
        resp = self.client.post("/rest/api/3/screenscheme", data=payload)
        resp.raise_for_status()
        return self.get_screen_scheme(resp.json()['id'])

    def get_screen_scheme(self, screen_scheme_id) -> ScreenScheme:
        resp = self.client.get(f"/rest/api/3/screenscheme?id={screen_scheme_id}")
        resp.raise_for_status()
        return ScreenScheme(resp.json()['values'][0], self.client)

    def delete_screen_scheme(self, screen_scheme: ScreenScheme):
        resp = self.client.delete(f"/rest/api/3/screenscheme/{screen_scheme.id}")
        resp.raise_for_status()

    def get_all_screen_schemes(self) -> list:
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/screenscheme?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(ScreenScheme(val, self.client))
        return _l

    def get_screen(self, _id) -> Screen:
        resp = self.client.get(f"/rest/api/3/screens?id={_id}")
        resp.raise_for_status()
        return Screen(resp.json()['values'][0], self.client)

    def get_all_screens(self) -> list:
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/screens?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(Screen(val, self.client))
        return _l

    def delete_screen(self, screen: Screen):
        resp = self.client.delete(f"/rest/api/3/screens//{screen.id}")
        resp.raise_for_status()

