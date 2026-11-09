# Практическая работа № 2, вариант 16

Группа ИКБО-71-24. Тема курсовой работы: веб-приложение с HTTP API для
асинхронного преобразования файлов MP3 в WAV.

## Общее описание

Работа реализует три этапа варианта 16. Консольная утилита читает байты MP3
из стандартного ввода и пишет байты WAV в стандартный вывод. Flask API
принимает задачи, запускает утилиту в отдельном процессе посредством
`subprocess`, сохраняет результат в таблице `Feedback`. Основной поток HTTP
запроса не ожидает завершения обработки. Слой данных использует SQLite и
ORM SQLAlchemy. Ответы API имеют формат XML. Все маршруты требуют HTTP Basic
авторизацию по RFC 7617.

Таблицы соответствуют рисунку 16 методички: `Agent(key, time, platform)`,
`Task(key, time, argument, agent, description, tags, processed, launched)` и
`Feedback(key, time, result, status, failure, task, cache_hit, duration)`.
`Task.agent` ссылается на `Agent.key`, `Feedback.task` — на `Task.key`.
Время хранится как Unix timestamp в секундах, длительность — в миллисекундах.
`argument` содержит MP3 в Base64, `result` содержит WAV в Base64.

## Установка и настройки

Нужен Python 3.10 или новее. Из каталога проекта:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Скопировать `config.example.json` в `config.json` и задать свой пароль.
Настройки: `username`, `password` — учётные данные Basic Auth;
`database_url` — URL SQLAlchemy для SQLite, по умолчанию
`sqlite:///practice2.db`; `test_mode` — режим без запуска реального
преобразования. При `test_mode=true` задача получает Feedback со статусом
`skipped`. Файл `config.json` содержит пароль и исключён из git.

```bash
python -m src.app
# либо run.bat / run.sh
```

Сервер по умолчанию слушает `http://127.0.0.1:5000`. Все методы используют
префикс `/service/api/v2.1`. Ошибка авторизации возвращает код 401,
заголовок `WWW-Authenticate` и XML. Ошибочные параметры возвращают 400 и XML.
Корректные запросы возвращают 200 и XML.

## Функции и методы API

| Метод | Маршрут | Назначение |
|---|---|---|
| PUT | `/agent/submit/:key` | Создать Agent; параметры `platform`, `time` |
| POST | `/agent/explore` | Поиск Agent по полям |
| GET | `/agent/view` | Чтение Agent по полям |
| PUT | `/task/submit/:key` | Создать и запустить Task; `agent`, `argument`, `description`, `tags`, `time` |
| POST | `/task/explore/:agent` | Поиск Task агента по полям |
| GET | `/task/view` | Чтение Task по полям |
| POST | `/feedback/explore/:task` | Поиск Feedback задачи по полям |
| GET | `/feedback/view` | Чтение Feedback по полям |
| POST | `/report/explore` | Отчёт по формуле (16) |

Поля таблиц можно передать как параметры строки запроса для поиска.
`key` в PUT берётся из пути. В `task/submit` передаётся Base64 кодировка
байтов MP3. Это соответствует указанным в таблице 16 параметрам пути и
строки запроса. Для крупных файлов длина URL может ограничиваться сервером
или прокси; учебный интерфейс рассчитан на короткие записи.

`report/explore` выбирает уникальные сочетания
`(Agent.platform, Task.argument, Task.description)` для агентов с
`Agent.time > now - 7 минут`, соединяя таблицы по `Agent.key = Task.agent`.

Класс `src.client.ApiClient` реализует девять методов в требуемой форме
`действие_таблица`: `submit_agent`, `explore_agent`, `view_agent`,
`submit_task`, `explore_task`, `view_task`, `explore_feedback`,
`view_feedback`, `explore_report`. Он декодирует XML в список словарей.

Утилита `src.convert.convert_mp3(data)` возвращает WAV PCM 16 бит, моно,
44100 Гц. `src.convert.main()` читает MP3 через `stdin.buffer`, пишет WAV
через `stdout.buffer`, сообщения об ошибке направляет в stderr и возвращает
ненулевой код. Декодирование выполняется локальным FFmpeg из пакета
`imageio-ffmpeg`; для формирования WAV с точным заголовком используется
стандартный модуль `wave`.

## Примеры использования

Консольная утилита:

```bash
python -m src.convert < input.mp3 > output.wav
```

Пять воспроизводимых примеров генерируются без хранения бинарных файлов в
репозитории командой `python -m examples.demo` или `run.bat demo`.
Тестовые MP3 содержат синусоидальный сигнал с указанной частотой и
длительностью. Результат запуска:

| № | Частота, Гц | Длительность, с | MP3, байт | WAV, байт | Каналы | Частота WAV, Гц | Сэмплы |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 440 | 0.2 | 1924 | 20780 | 1 | 44100 | 10368 |
| 2 | 523 | 0.3 | 2760 | 29996 | 1 | 44100 | 14976 |
| 3 | 659 | 0.4 | 3596 | 39212 | 1 | 44100 | 19584 |
| 4 | 784 | 0.5 | 4432 | 48428 | 1 | 44100 | 24192 |
| 5 | 880 | 0.6 | 5059 | 55340 | 1 | 44100 | 27648 |

Пример клиента после запуска сервера:

```python
from pathlib import Path
from src.client import ApiClient

api = ApiClient("http://127.0.0.1:5000", "student", "your-password")
api.submit_agent(1, "Windows")
api.submit_task(1, 1, Path("input.mp3").read_bytes(),
                description="Демонстрация")
feedback = api.explore_feedback(1)
# Повторять запрос, пока список пуст; результат приходит асинхронно.
```

После получения Feedback со статусом `completed` поле `result` можно
декодировать: `base64.b64decode(feedback[0]["result"])`, затем сохранить
полученные байты в WAV файл. Статус `failed` сопровождается полем `failure`.

## Тесты и покрытие

```bash
run.bat test
run.bat coverage
python -m flake8 src tests examples --max-line-length=79
```

Для Linux/macOS используются `./run.sh test`, `./run.sh coverage` и та же
команда flake8. `tests/test_mbt.py` применяет
`hypothesis.stateful.RuleBasedStateMachine`: модель хранит ожидаемые Agent и
Task, генерирует последовательности вызовов через `ApiClient` и проверяет
все девять обработчиков. В режиме покрытия запускается только этот файл
тестов. Ветвевой отчёт находится в `coverage-report.txt`.
`tests/test_conversion.py` отдельно проверяет настоящее преобразование
через Flask API, фоновый `subprocess`, сохранённый Feedback и параметры WAV.

Команда покрытия:

```bash
python -m coverage run --branch --source=src.app -m pytest -q tests/test_mbt.py
python -m coverage report -m
```

Исходный код и тесты оформлены по PEP 8. В репозиторий не добавляются
бинарные файлы, база данных, служебные файлы Python и конфигурация редактора.
