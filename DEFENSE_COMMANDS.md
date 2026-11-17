# Команды для защиты практической работы № 2

Команды ниже рассчитаны на **Windows PowerShell** на вашем ноутбуке.
Сначала откройте терминал в папке `pws2-var16`. Каждый блок можно копировать
целиком.

## 1. Проверка окружения

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import flask, sqlalchemy, imageio_ffmpeg, hypothesis; print('Зависимости установлены')"
if (-not (Test-Path config.json)) { Copy-Item config.example.json config.json }
```

Виртуальное окружение `.venv` уже создано на вашем ноутбуке.

## 2. Прямой запуск консольной утилиты

Файл `my_song.mp3` уже лежит рядом с `README.md`. Передать его утилите через
стандартный ввод и сохранить стандартный вывод как WAV:

```powershell
cmd.exe /c ".venv\Scripts\python.exe -m src.convert < my_song.mp3 > my_song.wav"
.\.venv\Scripts\python.exe -c "import wave; w = wave.open('my_song.wav', 'rb'); print(w.getparams()); w.close()"
```

После первой команды в папке появится `my_song.wav`. Вторая команда печатает
его параметры. Для перенаправления бинарных потоков используется `cmd.exe`:
PowerShell не поддерживает оператор `<` для ввода файла. Файлы MP3 и WAV
исключены из Git и остаются локально на вашем ноутбуке.

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
.\.venv\Scripts\python.exe -m sqlite3 practice2.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
.\.venv\Scripts\python.exe -m sqlite3 practice2.db "SELECT key, agent, description, processed FROM task ORDER BY key DESC LIMIT 1;"
.\.venv\Scripts\python.exe -m sqlite3 practice2.db "SELECT task, status, duration FROM feedback ORDER BY key DESC LIMIT 1;"
```

Ожидаются таблицы `agent`, `task`, `feedback` и строка `feedback` со статусом
`completed`. На вашем Python 3.14 доступен CLI SQLite как `python -m sqlite3`.

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
