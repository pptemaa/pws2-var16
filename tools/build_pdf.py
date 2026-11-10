"""Построить PDF копию README без бинарных файлов в репозитории."""

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT.parent / "Практическая_работа_2_вариант_16_README.pdf"


def styles():
    """Подготовить шрифты с поддержкой кириллицы."""
    font_dir = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("Arial", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("ArialBold", str(font_dir / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Consolas", str(font_dir / "consola.ttf")))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="ArialBold")
    return {
        "body": ParagraphStyle("body", fontName="Arial", fontSize=8.5,
                               leading=11.5, spaceAfter=4),
        "title": ParagraphStyle("title", fontName="ArialBold", fontSize=17,
                                leading=20, spaceAfter=10),
        "section": ParagraphStyle("section", fontName="ArialBold",
                                  fontSize=11.5, leading=15, spaceBefore=9,
                                  spaceAfter=6),
        "cell": ParagraphStyle("cell", fontName="Arial", fontSize=6.7,
                               leading=8, alignment=TA_CENTER),
        "code": ParagraphStyle("code", fontName="Consolas", fontSize=7,
                               leading=9, leftIndent=6, spaceAfter=6),
    }


def inline(text):
    """Подготовить простой Markdown текст для Paragraph."""
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='Consolas'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def add_table(rows, story, style, width):
    """Добавить таблицу Markdown с шириной по странице."""
    count = len(rows[0])
    widths = [width / count] * count
    cells = [[Paragraph(inline(cell), style) for cell in row]
             for row in rows]
    table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eff5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend((table, Spacer(1, 6)))


def line_kind(line, in_code):
    """Определить вид строки Markdown."""
    if line.startswith("```"):
        return "fence"
    if in_code:
        return "code"
    if not line.strip():
        return "blank"
    if line.startswith("# ") or line.startswith("## "):
        return "heading"
    if line.startswith("|"):
        return "table"
    return "paragraph"


def iter_blocks(source):
    """Сгруппировать строки README по видам блоков."""
    current, lines, in_code = None, [], False
    for line in source.splitlines() + [""]:
        kind = line_kind(line, in_code)
        if kind in ("fence", "blank"):
            if lines:
                yield current, lines
                lines = []
            if kind == "fence":
                in_code = not in_code
            current = None
            continue
        if kind != current and lines:
            yield current, lines
            lines = []
        current = kind
        lines.append(line)


def parse_table(lines):
    """Извлечь ячейки таблицы, пропуская строку разделителей."""
    rows = []
    for line in lines:
        cells = [part.strip() for part in line.strip("|").split("|")]
        if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            rows.append(cells)
    return rows


def build_story(source, sheet, width):
    """Преобразовать блоки README в элементы ReportLab."""
    story = []
    for kind, lines in iter_blocks(source):
        if kind == "heading":
            for line in lines:
                key = "title" if line.startswith("# ") else "section"
                story.append(Paragraph(inline(line.lstrip("# ")),
                                       sheet[key]))
        elif kind == "table":
            add_table(parse_table(lines), story, sheet["cell"], width)
        elif kind == "code":
            story.append(Preformatted("\n".join(lines), sheet["code"],
                                      maxLineLength=88))
        else:
            story.append(Paragraph(inline(" ".join(lines)), sheet["body"]))
    return story


def main():
    """Создать PDF в родительском каталоге проекта."""
    document = SimpleDocTemplate(str(OUTPUT), pagesize=A4,
                                 leftMargin=15 * mm, rightMargin=15 * mm,
                                 topMargin=14 * mm, bottomMargin=14 * mm)
    source = (ROOT / "README.md").read_text(encoding="utf-8")
    story = build_story(source, styles(), document.width)
    document.build(story)


if __name__ == "__main__":
    main()
