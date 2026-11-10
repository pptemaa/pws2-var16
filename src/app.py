"""Flask HTTP API варианта 16 с XML, Basic Auth и SQLite."""

import base64
import binascii
import hmac
import json
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from pathlib import Path
from xml.etree import ElementTree as element_tree

from flask import Flask, Response, current_app, request
from sqlalchemy import Integer, create_engine, select
from sqlalchemy.orm import sessionmaker

from src.models import Agent, Base, Feedback, Task

PREFIX = "/service/api/v2.1"
WINDOW = 7 * 60


def int_route(name):
    """Сформировать параметр пути Flask для целочисленного ключа."""
    return "<int" + ":" + name + ">"


FIELDS = {
    Agent: ("key", "time", "platform"),
    Task: ("key", "time", "argument", "agent", "description", "tags",
           "processed", "launched"),
    Feedback: ("key", "time", "result", "status", "failure", "task",
               "cache_hit", "duration"),
}


def xml_response(name, rows):
    """Сериализовать набор записей в XML."""
    root = element_tree.Element(name)
    for row in rows:
        item = element_tree.SubElement(root, "item")
        if hasattr(row, "_mapping"):
            values = zip(("platform", "argument", "description"), row)
        else:
            values = ((field, getattr(row, field))
                      for field in FIELDS[type(row)])
        for field, value in values:
            element_tree.SubElement(item, field).text = str(value)
    return Response(element_tree.tostring(root, encoding="utf-8"),
                    mimetype="application/xml")


def error_response(message, status):
    """Вернуть ошибку в формате XML."""
    root = element_tree.Element("error")
    element_tree.SubElement(root, "message").text = message
    response = Response(element_tree.tostring(root, encoding="utf-8"),
                        status=status,
                        mimetype="application/xml")
    if status == HTTPStatus.UNAUTHORIZED:
        response.headers["WWW-Authenticate"] = 'Basic realm="Practice 2"'
    return response


def authorized():
    """Проверить учётные данные HTTP Basic (RFC 7617)."""
    auth = request.authorization
    if auth is None or auth.type.lower() != "basic":
        return False
    username = current_app.config["API_USERNAME"]
    password = current_app.config["API_PASSWORD"]
    return (hmac.compare_digest(auth.username or "", username)
            and hmac.compare_digest(auth.password or "", password))


def session():
    """Создать сессию базы данных текущего приложения."""
    return current_app.config["SESSION_FACTORY"]()


def integer(name, default=None):
    """Прочитать обязательный или необязательный целый параметр."""
    value = request.args.get(name)
    if value is None:
        if default is None:
            raise ValueError(f"Отсутствует параметр {name}")
        return default
    return int(value)


def find_rows(model, fixed=None):
    """Найти записи по параметрам запроса и параметрам пути."""
    filters = dict(fixed or {})
    for field in FIELDS[model]:
        if field in request.args:
            value = request.args[field]
            filters[field] = (int(value) if field in numeric_fields(model)
                              else value)
    with session() as db:
        query = select(model).filter_by(**filters).order_by(model.key)
        return xml_response(model.__tablename__, db.scalars(query).all())


def numeric_fields(model):
    """Перечислить целочисленные поля модели."""
    return {column.key for column in model.__table__.columns
            if isinstance(column.type, Integer)}


def run_task(factory, task_key, payload, test_mode):
    """Выполнить задачу в фоновом потоке и сохранить Feedback."""
    start = time.monotonic()
    result, failure, status = "", "", "completed"
    try:
        if test_mode:
            status = "skipped"
        else:
            command = [sys.executable, "-m", "src.convert"]
            root = Path(__file__).resolve().parent.parent
            process = subprocess.run(command, input=payload, cwd=root,
                                     capture_output=True, check=False)
            if process.returncode:
                raise ValueError(process.stderr.decode("utf-8", "replace"))
            result = base64.b64encode(process.stdout).decode("ascii")
    except (OSError, ValueError) as error:
        failure, status = str(error), "failed"
    with factory() as db:
        task = db.get(Task, task_key)
        task.processed = 1
        db.add(Feedback(time=int(time.time()), result=result, status=status,
                        failure=failure, task=task_key, cache_hit=0,
                        duration=int((time.monotonic() - start) * 1000)))
        db.commit()


def create_app(config_path=None, overrides=None):
    """Создать приложение и инициализировать таблицы SQLite."""
    app = Flask(__name__)
    path = Path(config_path or "config.json")
    settings = {}
    if path.exists():
        settings = json.loads(path.read_text(encoding="utf-8"))
    settings.update(overrides or {})
    app.config["API_USERNAME"] = settings.get("username", "student")
    app.config["API_PASSWORD"] = settings.get("password", "change-me")
    app.config["TEST_MODE"] = settings.get("test_mode", False)
    url = settings.get("database_url", "sqlite:///practice2.db")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    app.config["ENGINE"] = engine
    app.config["SESSION_FACTORY"] = sessionmaker(
        engine, expire_on_commit=False)
    register_routes(app)
    return app


def register_routes(app):
    """Подключить обработчики всех девяти маршрутов."""
    app.before_request(check_auth)
    app.add_url_rule(f"{PREFIX}/agent/submit/{int_route('key')}",
                     view_func=submit_agent, methods=["PUT"])
    app.add_url_rule(f"{PREFIX}/agent/explore", view_func=explore_agent,
                     methods=["POST"])
    app.add_url_rule(f"{PREFIX}/agent/view", view_func=view_agent,
                     methods=["GET"])
    app.add_url_rule(f"{PREFIX}/task/submit/{int_route('key')}",
                     view_func=submit_task, methods=["PUT"])
    app.add_url_rule(f"{PREFIX}/task/explore/{int_route('agent')}",
                     view_func=explore_task, methods=["POST"])
    app.add_url_rule(f"{PREFIX}/task/view", view_func=view_task,
                     methods=["GET"])
    app.add_url_rule(f"{PREFIX}/feedback/explore/{int_route('task')}",
                     view_func=explore_feedback, methods=["POST"])
    app.add_url_rule(f"{PREFIX}/feedback/view", view_func=view_feedback,
                     methods=["GET"])
    app.add_url_rule(f"{PREFIX}/report/explore", view_func=explore_report,
                     methods=["POST"])
    app.register_error_handler(ValueError, invalid_value)


def check_auth():
    """Отклонить запрос без правильного HTTP Basic заголовка."""
    if not authorized():
        return error_response("Требуется авторизация", 401)
    return None


def invalid_value(error):
    """Сообщить об ошибочном параметре запроса."""
    return error_response(str(error), 400)


def submit_agent(key):
    """Добавить Agent с ключом из пути."""
    platform = request.args.get("platform")
    if not platform:
        raise ValueError("Отсутствует platform")
    with session() as db:
        if db.get(Agent, key):
            raise ValueError("Agent с таким key уже существует")
        agent = Agent(key=key, time=integer("time", int(time.time())),
                      platform=platform)
        db.add(agent)
        db.commit()
        return xml_response("agent", [agent])


def explore_agent():
    """Найти записи Agent."""
    return find_rows(Agent)


def view_agent():
    """Прочитать записи Agent."""
    return find_rows(Agent)


def submit_task(key):
    """Добавить Task и асинхронно запустить преобразование."""
    agent_key = integer("agent")
    argument = request.args.get("argument")
    if argument is None:
        raise ValueError("Отсутствует argument")
    try:
        payload = base64.b64decode(argument, validate=True)
    except binascii.Error as error:
        raise ValueError("argument должен быть Base64") from error
    with session() as db:
        if db.get(Task, key) or not db.get(Agent, agent_key):
            raise ValueError("Дублирующийся Task или неизвестный Agent")
        task = Task(key=key, time=integer("time", int(time.time())),
                    argument=argument, agent=agent_key,
                    description=request.args.get("description", ""),
                    tags=request.args.get("tags", ""), processed=0, launched=1)
        db.add(task)
        db.commit()
        response = xml_response("task", [task])
    factory = current_app.config["SESSION_FACTORY"]
    mode = current_app.config["TEST_MODE"]
    threading.Thread(target=run_task, args=(factory, key, payload, mode),
                     daemon=True).start()
    return response


def explore_task(agent):
    """Найти задачи указанного Agent."""
    return find_rows(Task, {"agent": agent})


def view_task():
    """Прочитать записи Task."""
    return find_rows(Task)


def explore_feedback(task):
    """Найти Feedback указанной задачи."""
    return find_rows(Feedback, {"task": task})


def view_feedback():
    """Прочитать записи Feedback."""
    return find_rows(Feedback)


def explore_report():
    """Вычислить реляционную формулу (16) из методички."""
    with session() as db:
        query = (select(Agent.platform, Task.argument, Task.description)
                 .join(Task, Agent.key == Task.agent)
                 .where(Agent.time > int(time.time()) - WINDOW)
                 .distinct())
        return xml_response("report", db.execute(query).all())


if __name__ == "__main__":
    create_app().run()
