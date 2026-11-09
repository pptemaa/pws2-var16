"""Клиент HTTP API с методами в формате действие_таблица."""

import base64
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from src.app import PREFIX


class ApiClient:
    """Клиент варианта 16, пригодный для HTTP и Flask test_client."""

    def __init__(self, base_url, username, password, transport=None):
        """Сохранить адрес, учётные данные и необязательный transport."""
        self.base_url = base_url.rstrip("/")
        credentials = f"{username}:{password}".encode("utf-8")
        token = base64.b64encode(credentials).decode("ascii")
        self.headers = {"Authorization": f"Basic {token}"}
        self.transport = transport

    def _request(self, method, path, **params):
        """Выполнить запрос и разобрать XML ответ."""
        query = urlencode(params)
        url = f"{self.base_url}{PREFIX}{path}"
        if query:
            url = f"{url}?{query}"
        if self.transport is not None:
            response = self.transport.open(url, method=method,
                                           headers=self.headers)
            data = response.data
        else:
            request = Request(url, method=method, headers=self.headers)
            with urlopen(request) as response:
                data = response.read()
        root = ET.fromstring(data)
        return [{child.tag: child.text or "" for child in item}
                for item in root.findall("item")]

    def submit_agent(self, key, platform, time=None):
        """Создать агента."""
        params = {"platform": platform}
        if time is not None:
            params["time"] = time
        return self._request("PUT", f"/agent/submit/{key}", **params)

    def explore_agent(self, **filters):
        """Найти агентов."""
        return self._request("POST", "/agent/explore", **filters)

    def view_agent(self, **filters):
        """Прочитать агентов."""
        return self._request("GET", "/agent/view", **filters)

    def submit_task(self, key, agent, mp3, description="", tags=""):
        """Создать задачу асинхронного преобразования."""
        argument = base64.b64encode(mp3).decode("ascii")
        return self._request("PUT", f"/task/submit/{key}", agent=agent,
                             argument=argument, description=description,
                             tags=tags)

    def explore_task(self, agent, **filters):
        """Найти задачи агента."""
        return self._request("POST", f"/task/explore/{agent}", **filters)

    def view_task(self, **filters):
        """Прочитать задачи."""
        return self._request("GET", "/task/view", **filters)

    def explore_feedback(self, task, **filters):
        """Найти результаты задачи."""
        return self._request("POST", f"/feedback/explore/{task}", **filters)

    def view_feedback(self, **filters):
        """Прочитать результаты."""
        return self._request("GET", "/feedback/view", **filters)

    def explore_report(self):
        """Вычислить отчёт по формуле (16)."""
        return self._request("POST", "/report/explore")
