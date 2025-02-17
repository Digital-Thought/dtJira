from jira.client import JIRA
import requests
from requests.auth import HTTPBasicAuth

import json

from ._fields import Fields
from ._projects import Projects
from ._issue_types import IssueTypes
from ._screens import Screens
from ._statuses import Statuses
from ._workflows import Workflows
from ._groups import Groups

class JiraClient:

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.jira = JIRA(server=self.url, basic_auth=(self.username, self.password))
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.session.headers.update({"Content-Type": "application/json"})

    def close(self):
        self.jira.close()
        self.session.close()

    def fields(self) -> Fields:
        return Fields(self)

    def projects(self) -> Projects:
        return Projects(self)

    def issue_types(self) -> IssueTypes:
        return IssueTypes(self)

    def screens(self) -> Screens:
        return Screens(self)

    def statuses(self) -> Statuses:
        return Statuses(self)

    def workflows(self) -> Workflows:
        return Workflows(self)

    def groups(self) -> Groups:
        return Groups(self)

    def get_me(self):
        resp = self.get("/rest/api/2/myself")
        resp.raise_for_status()
        return resp.json()

    def post(self, path, data):
        url = f"{self.url}{path}"
        return self.session.post(url, data=json.dumps(data))

    def delete(self, path):
        url = f"{self.url}{path}"
        return self.session.delete(url)

    def get(self, path):
        url = f"{self.url}{path}"
        return self.session.get(url)

    def put(self, path, data):
        url = f"{self.url}{path}"
        return self.session.put(url, data=json.dumps(data))