
class Group:

    def __init__(self, detail, client):
        self.detail = detail
        self.client = client

    @property
    def name(self):
        return self.detail['name']

    @property
    def id(self):
        return self.detail['groupId']

class Groups:

    def __init__(self, client):
        self.client = client

    def get_groups(self):
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/group/bulk?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(Group(val, self.client))
        return _l

    def create_group(self, name):
        payload = {
            "name": name
        }
        resp = self.client.post("/rest/api/3/group", data=payload)
        resp.raise_for_status()
        return Group(resp.json(), self.client)

    def create_groups(self, group_names: list):
        _l = []
        for name in group_names:
            found = False
            for group in self.get_groups():
                if name == group.name:
                    found = True
                    break
            if not found:
                _l.append(self.create_group(name))

        return _l