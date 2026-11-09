"""Создать HTML для печати README через браузер."""

from pathlib import Path

import markdown


def main():
    """Преобразовать Markdown с таблицами и блоками кода в HTML."""
    source = Path("README.md").read_text(encoding="utf-8")
    body = markdown.markdown(source, extensions=["tables", "fenced_code"])
    css = """
    @page { size: A4; margin: 17mm; }
    body { font: 11pt Arial, sans-serif; line-height: 1.35; color: #222; }
    h1 { font-size: 20pt; }
    h2 { font-size: 15pt; margin-top: 20pt; }
    pre { background: #f5f5f5; padding: 8pt; white-space: pre-wrap; }
    code { font-family: Consolas, monospace; font-size: 9pt; }
    table { border-collapse: collapse; font-size: 8pt; width: 100%; }
    th, td { border: 1px solid #aaa; padding: 4pt; }
    tr { page-break-inside: avoid; }
    """
    html = f'<html><meta charset="utf-8"><style>{css}</style>{body}</html>'
    Path("readme-print.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
