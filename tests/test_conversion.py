"""Интеграционная проверка реального фонового преобразования."""

import base64
import tempfile
import time
import wave
from io import BytesIO
from pathlib import Path

from src.app import create_app
from src.client import ApiClient
from src.convert import SAMPLE_RATE
from examples.demo import make_mp3


def test_real_mp3_to_wav():
    """Проверить цепочку PUT Task -> subprocess -> Feedback -> WAV."""
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        database = Path(directory) / "real.db"
        app = create_app(overrides={
            "database_url": "sqlite:///" + database.as_posix(),
            "test_mode": False,
        })
        api = ApiClient("http://localhost", "student", "change-me",
                        transport=app.test_client())
        api.submit_agent(1, "pytest")
        api.submit_task(1, 1, make_mp3(440, 0.2))
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            feedback = api.explore_feedback(1)
            if feedback:
                break
            time.sleep(0.05)
        assert feedback[0]["status"] == "completed"
        data = base64.b64decode(feedback[0]["result"])
        with wave.open(BytesIO(data), "rb") as wav:
            assert wav.getnchannels() == 1
            assert wav.getframerate() == SAMPLE_RATE
            assert wav.getnframes() > 0
        app.config["ENGINE"].dispose()
