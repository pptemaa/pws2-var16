"""Model-Based Testing всех девяти обработчиков через API-клиент."""

import tempfile
import time
from http import HTTPStatus
from pathlib import Path

from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from src.app import PREFIX, create_app
from src.client import ApiClient


class ApiMachine(RuleBasedStateMachine):
    """Эталонная модель Agent, Task и Feedback."""

    def __init__(self):
        """Создать отдельную SQLite базу для каждой истории команд."""
        super().__init__()
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        database = Path(self.temp.name) / "test.db"
        url = "sqlite:///" + database.as_posix()
        app = create_app(overrides={"database_url": url, "test_mode": True})
        self.engine = app.config["ENGINE"]
        self.client = ApiClient("http://localhost", "student", "change-me",
                                transport=app.test_client())
        self.agents = {}
        self.tasks = {}

    def teardown(self):
        """Удалить временную базу данных."""
        for task in self.tasks:
            self.wait_for_feedback(task)
        self.engine.dispose()
        self.temp.cleanup()

    @rule()
    def create_agent(self):
        """Создать очередного агента через PUT."""
        key = len(self.agents) + 1
        platform = f"platform-{key}"
        rows = self.client.submit_agent(key, platform)
        assert rows[0]["key"] == str(key)
        self.agents[key] = platform

    @rule()
    def create_task(self):
        """Создать задачу в тестовом режиме через PUT."""
        if not self.agents:
            return
        key = len(self.tasks) + 1
        agent = next(iter(self.agents))
        rows = self.client.submit_task(key, agent, b"test mp3",
                                       description=f"job-{key}")
        assert rows[0]["key"] == str(key)
        self.tasks[key] = agent

    @rule()
    def search_agent(self):
        """Проверить поиск Agent через POST."""
        rows = self.client.explore_agent()
        assert {int(row["key"]) for row in rows} == set(self.agents)

    @rule()
    def search_task(self):
        """Проверить поиск Task через POST."""
        if self.agents:
            agent = next(iter(self.agents))
            rows = self.client.explore_task(agent)
            assert {int(row["key"]) for row in rows} == set(self.tasks)

    @rule()
    def search_feedback(self):
        """Проверить поиск Feedback через POST."""
        if self.tasks:
            task = next(iter(self.tasks))
            self.wait_for_feedback(task)
            rows = self.client.explore_feedback(task)
            assert rows and rows[0]["status"] == "skipped"

    @rule()
    def report(self):
        """Проверить реляционную формулу (16)."""
        rows = self.client.explore_report()
        assert len(rows) == len(self.tasks)

    @rule()
    def reject_missing_credentials(self):
        """Проверить требование 401 для запроса без авторизации."""
        path = f"{PREFIX}/agent/view"
        response = self.client.transport.open(path, method="GET")
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.headers["WWW-Authenticate"].startswith("Basic")

    @invariant()
    def read_all(self):
        """Проверить все GET маршруты и модель состояния."""
        agents = self.client.view_agent()
        tasks = self.client.view_task()
        feedback = self.client.view_feedback()
        assert {int(row["key"]) for row in agents} == set(self.agents)
        assert {int(row["key"]) for row in tasks} == set(self.tasks)
        assert len(feedback) <= len(self.tasks)

    def wait_for_feedback(self, task):
        """Дождаться окончания фонового тестового выполнения."""
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.client.explore_feedback(task):
                return
            time.sleep(0.01)
        raise AssertionError("Фоновая задача не завершилась")


TestApi = ApiMachine.TestCase
TestApi.settings = settings(max_examples=25, stateful_step_count=15,
                            deadline=None)
