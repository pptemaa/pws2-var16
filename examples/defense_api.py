"""Создать задачу через Flask API для показа файла SQLite."""

import json
import threading
import time
from pathlib import Path

from examples.demo import make_mp3
from src.app import create_app
from src.client import ApiClient

DATABASE = Path("practice2.db")


def main():
    """Отправить MP3 и дождаться сохранения результата в SQLite."""
    config = Path("config.json")
    settings = {}
    if config.exists():
        settings = json.loads(config.read_text(encoding="utf-8"))
    app = create_app()
    client = ApiClient("http://localhost",
                       settings.get("username", "student"),
                       settings.get("password", "change-me"),
                       transport=app.test_client())
    key = time.time_ns() // 1_000_000
    client.submit_agent(key, "defense")
    client.submit_task(key, key, make_mp3(440, 0.2),
                       description="MP3 to WAV")
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        rows = client.explore_feedback(key)
        if rows:
            result = rows[0]
            if result["status"] != "completed":
                raise RuntimeError(result["failure"])
            print("Task key:", key)
            print("Feedback status:", result["status"])
            print("Report rows:", len(client.explore_report()))
            print("SQLite file:", DATABASE.resolve())
            print("File exists:", DATABASE.is_file())
            for worker in threading.enumerate():
                if worker is not threading.current_thread():
                    worker.join(timeout=5)
            app.config["ENGINE"].dispose()
            return
        time.sleep(0.1)
    raise TimeoutError("Feedback не появился за 15 секунд")


if __name__ == "__main__":
    main()
