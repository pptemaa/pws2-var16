# Команды для защиты практической работы № 2

Команды ниже рассчитаны на **Windows PowerShell**. Сначала откройте терминал
внутри клонированной папки `pws2-var16`. Каждый блок можно копировать целиком.

## 1. Подготовка на компьютере преподавателя

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.json config.json
```

Нужен Python 3.10 или новее и доступ к интернету для установки пакетов.
Эту подготовку достаточно выполнить один раз после клонирования.

## 2. Прямой запуск консольной утилиты

Создать небольшой MP3, передать его утилите через стандартный ввод и
сохранить стандартный вывод как WAV:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from examples.demo import make_mp3; Path('sample.mp3').write_bytes(make_mp3(440, 1.0))"
cmd.exe /c ".venv\Scripts\python.exe -m src.convert < sample.mp3 > sample.wav"
.\.venv\Scripts\python.exe -c "import wave; w = wave.open('sample.wav', 'rb'); print(w.getparams()); w.close()"
```

После второй команды в папке появится `sample.wav`. Третья команда печатает
его параметры. Если есть свой MP3, замените `sample.mp3` его именем и
пропустите первую команду. Для перенаправления бинарных потоков используется
`cmd.exe`: PowerShell не поддерживает оператор `<` для ввода файла.

## 3. Пять примеров преобразования MP3 в WAV

```powershell
.\.venv\Scripts\python.exe -m examples.demo
```

Ожидается пять строк: номер примера, частота, длительность, размеры MP3 и WAV,
число каналов, частота дискретизации и число сэмплов.

## 4. Где показать обработчики 4.1 и 2.1

В `src/app.py` найти `register_routes`. Для 4.1 показать регистрацию
`POST /service/api/v2.1/report/explore` и функцию `explore_report` ниже:
она соединяет `Agent` и `Task`, оставляет агентов за последние 7 минут и
возвращает уникальные тройки `platform`, `argument`, `description`.

Для 2.1 показать регистрацию `PUT /service/api/v2.1/task/submit/:key` и
функцию `submit_task`: она сохраняет `Task`, запускает фоновый поток и через
`run_task` вызывает консольную утилиту посредством `subprocess`.

## 5. MBT, внесённая ошибка и контрпример

На основной ветке показать `tests/test_mbt.py`: класс `ApiMachine` наследует
`RuleBasedStateMachine`, правила вызывают API через `ApiClient`, а инвариант
`read_all` сравнивает данные сервера с моделью.

Для демонстрации ошибки переключиться на отдельную ветку. В ней изменена
**одна строка** в `src/client.py`, метод `submit_task`: клиент искажает поле
`description` при PUT-запросе к обработчику 2.1. Вариант 16 не содержит
отдельной ручки `update`, поэтому для опыта используется его метод PUT 2.1.

```powershell
git switch demo/mbt-client-fault
.\.venv\Scripts\python.exe -m pytest -q tests/test_mbt.py
git switch main
.\.venv\Scripts\python.exe -m pytest -q tests/test_mbt.py
```

На демонстрационной ветке тест **должен завершиться ошибкой** и вывести
`Failing test case`. Hypothesis сокращает сценарий до `create_agent`,
`create_task`, `read_all`: модель ожидает `job-1`, а сервер после ошибочного
запроса клиента хранит `job-1-fault`.
После возврата на `main` тот же тест должен пройти.

## 6. Файл SQLite на диске

На основной ветке создать реальную задачу через Flask API и показать базу:

```powershell
.\.venv\Scripts\python.exe -m examples.defense_api
Get-Item practice2.db
sqlite3.exe practice2.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
sqlite3.exe practice2.db "SELECT key, agent, description, processed FROM task ORDER BY key DESC LIMIT 1;"
sqlite3.exe practice2.db "SELECT task, status, duration FROM feedback ORDER BY key DESC LIMIT 1;"
```

Ожидаются таблицы `agent`, `task`, `feedback` и строка `feedback` со статусом
`completed`. Если на компьютере нет `sqlite3.exe`, можно открыть тот же
файл через CLI модуля Python, подставив вместо `sqlite3.exe` команду
`.\.venv\Scripts\python.exe -m sqlite3`. Если этот CLI недоступен, используйте
встроенный модуль Python:

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; db = sqlite3.connect('practice2.db'); print(db.execute('SELECT name FROM sqlite_master').fetchall()); print(db.execute('SELECT task, status FROM feedback').fetchall())"
```

## 7. Тесты, ветвевое покрытие и стиль

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m coverage run --branch --source=src.app -m pytest -q tests/test_mbt.py
.\.venv\Scripts\python.exe -m coverage report -m
.\.venv\Scripts\python.exe -m flake8 src tests examples --max-line-length=79 --max-complexity=10
```

Ожидается два пройденных теста. Последняя команда при отсутствии замечаний
ничего не печатает.

## 8. Работающий HTTP API, если попросят показать

В **первом PowerShell** из папки проекта запустить сервер и оставить окно
открытым:

```powershell
.\.venv\Scripts\python.exe -m src.app
```

Во **втором PowerShell** из папки проекта проверить авторизацию:

```powershell
curl.exe -i http://127.0.0.1:5000/service/api/v2.1/agent/view
curl.exe -i -u student:change-me http://127.0.0.1:5000/service/api/v2.1/agent/view
```

Первый запрос возвращает `401 Unauthorized`, второй — `200 OK` и XML.
Имя пользователя и пароль взяты из `config.json`, созданного на шаге 1.
Сервер можно остановить сочетанием `Ctrl+C` в первом окне.

## Что показать в GitHub

Репозиторий: https://github.com/pptemaa/pws2-var16

Показать `README.md`, папки `src` и `tests`, историю коммитов и файл
`coverage-report.txt`. Консольную утилиту объяснить по `src/convert.py`,
HTTP API — по `src/app.py`, SQLite-модель — по `src/models.py`, модельное
тестирование — по `tests/test_mbt.py`.
