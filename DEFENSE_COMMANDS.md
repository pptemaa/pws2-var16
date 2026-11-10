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

## 2. Пять примеров преобразования MP3 в WAV

```powershell
.\.venv\Scripts\python.exe -m examples.demo
```

Ожидается пять строк: номер примера, частота, длительность, размеры MP3 и WAV,
число каналов, частота дискретизации и число сэмплов.

## 3. Тесты, ветвевое покрытие и стиль

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m coverage run --branch --source=src.app -m pytest -q tests/test_mbt.py
.\.venv\Scripts\python.exe -m coverage report -m
.\.venv\Scripts\python.exe -m flake8 src tests examples --max-line-length=79 --max-complexity=10
```

Ожидается два пройденных теста. Последняя команда при отсутствии замечаний
ничего не печатает.

## 4. Работающий HTTP API, если попросят показать

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
