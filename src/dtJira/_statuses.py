
class Status:

    def __init__(self, detail, client):
        self.detail = detail
        self.client = client

    @property
    def id(self):
        return self.detail['id']

    @property
    def description(self):
        return self.detail['description']

    @property
    def name(self):
        return self.detail['name']

    @property
    def scope(self):
        return self.detail['scope']

    @property
    def status_category(self):
        return self.detail['statusCategory']

    @property
    def usages(self):
        return self.detail['usages']

    @property
    def workflow_usages(self):
        return self.detail['workflowUsages']

class Statuses:

    def __init__(self, client):
        self.client = client

    def get_all(self):
        resp = self.client.get(path='/rest/api/3/statuses/search?expand=usages,workflowUsages')
        resp.raise_for_status()

        return [Status(status_data, self.client) for status_data in resp.json()['values']]

    def delete(self, status: Status):
        resp = self.client.delete(path=f'/rest/api/3/statuses?id={status.id}')
        resp.raise_for_status()

    def create(self, name, status_category, description=''):
        payload = {
            "scope": {
                "type": "GLOBAL"
            },
            "statuses": [
                {
                    "description": description,
                    "name": name,
                    "statusCategory": status_category
                }
            ]

        }
        resp = self.client.post(path='/rest/api/3/statuses', data=payload)
        resp.raise_for_status()
        return Status(resp.json()[0], self.client)