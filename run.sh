#!/bin/sh
set -eu
case "${1:-server}" in
  test) python -m pytest -q tests ;;
  coverage)
    python -m coverage run --branch --source=src.app -m pytest -q tests/test_mbt.py
    python -m coverage report -m
    ;;
  demo) python -m examples.demo ;;
  server) python -m src.app ;;
  *) echo "Usage: $0 [server|test|coverage|demo]" >&2; exit 2 ;;
esac
