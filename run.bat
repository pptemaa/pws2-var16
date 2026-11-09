@echo off
setlocal
if "%~1"=="test" (
    python -m pytest -q tests
) else if "%~1"=="coverage" (
    python -m coverage run --branch --source=src.app -m pytest -q tests/test_mbt.py
    python -m coverage report -m
) else if "%~1"=="demo" (
    python -m examples.demo
) else (
    python -m src.app
)
