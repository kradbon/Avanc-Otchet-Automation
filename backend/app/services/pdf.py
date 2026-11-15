from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.models import ExpenseReportRecord, ProductionReportRecord, UserRecord


PAGE_WIDTH = 1240
PAGE_HEIGHT = 1754
MARGIN_X = 86


def generate_expense_report_pdf(report: ExpenseReportRecord, employee: UserRecord) -> Path:
    settings.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
    path = settings.pdf_storage_dir / f"{report.reference_number}.pdf"

    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), color="#f8f7f2")
    draw = ImageDraw.Draw(image)

    title_font = _load_font(58, bold=True)
    section_font = _load_font(28, bold=True)
    body_font = _load_font(24)
    body_bold_font = _load_font(24, bold=True)
    small_font = _load_font(20)

    draw.rounded_rectangle((MARGIN_X, 70, PAGE_WIDTH - MARGIN_X, 206), radius=28, fill="#15304a")
    draw.text((MARGIN_X + 36, 98), "Авансовый отчет", font=title_font, fill="#ffffff")
    draw.text(
        (MARGIN_X + 36, 160),
        "Формализованный документ для административной проверки",
        font=small_font,
        fill="#dbe6f0",
    )

    y = 270
    draw.text((MARGIN_X, y), "Реквизиты", font=section_font, fill="#15304a")
    y += 58

    info_rows = [
        ("Номер документа", report.reference_number),
        ("Сотрудник", employee.full_name),
        ("Должность", employee.position),
        ("Подразделение", employee.department),
        ("Отчетный период", report.period_label),
        ("Валюта", report.currency),
        ("Дата формирования", report.generated_at.strftime("%d.%m.%Y %H:%M")),
    ]

    for label, value in info_rows:
        draw.text((MARGIN_X + 6, y), label, font=body_font, fill="#4f6579")
        draw.text((MARGIN_X + 370, y), value, font=body_bold_font, fill="#172737")
        y += 54

    y += 14
    draw.text((MARGIN_X, y), "Финансовая часть", font=section_font, fill="#15304a")
    y += 60

    table_left = MARGIN_X
    table_right = PAGE_WIDTH - MARGIN_X
    row_height = 74
    rows = [
        ("Запрошено к возмещению", _format_money(report.amount_requested, report.currency)),
        ("Подтверждено администрацией", _format_money(report.amount_approved, report.currency)),
        ("Статус", _status_label(report.status.value)),
    ]

    draw.rounded_rectangle((table_left, y, table_right, y + row_height), radius=20, fill="#e7eef4")
    draw.text((table_left + 28, y + 20), "Показатель", font=body_bold_font, fill="#15304a")
    draw.text((table_right - 300, y + 20), "Значение", font=body_bold_font, fill="#15304a")
    y += row_height + 8

    for index, (label, value) in enumerate(rows):
        fill = "#ffffff" if index % 2 == 0 else "#f3f6f9"
        draw.rounded_rectangle((table_left, y, table_right, y + row_height), radius=18, fill=fill)
        draw.text((table_left + 28, y + 20), label, font=body_font, fill="#172737")
        draw.text((table_right - 280, y + 20), value, font=body_bold_font, fill="#172737")
        y += row_height + 8

    y += 24
    draw.text((MARGIN_X, y), "Назначение", font=section_font, fill="#15304a")
    y += 56

    purpose_box = (MARGIN_X, y, PAGE_WIDTH - MARGIN_X, y + 220)
    draw.rounded_rectangle(purpose_box, radius=24, fill="#eef3f7")
    purpose_lines = _wrap_text(draw, report.purpose, body_font, PAGE_WIDTH - (MARGIN_X * 2) - 56)
    line_y = y + 28
    for line in purpose_lines[:5]:
        draw.text((MARGIN_X + 28, line_y), line, font=body_font, fill="#172737")
        line_y += 40

    sign_y = PAGE_HEIGHT - 220
    draw.line((MARGIN_X + 18, sign_y, MARGIN_X + 290, sign_y), fill="#9eb1c2", width=2)
    draw.line((PAGE_WIDTH - MARGIN_X - 290, sign_y, PAGE_WIDTH - MARGIN_X - 18, sign_y), fill="#9eb1c2", width=2)
    draw.text((MARGIN_X + 72, sign_y + 16), "Подпись сотрудника", font=small_font, fill="#4f6579")
    draw.text((PAGE_WIDTH - MARGIN_X - 248, sign_y + 16), "Подпись администратора", font=small_font, fill="#4f6579")

    image.save(path, "PDF", resolution=150.0)
    return path


def generate_production_report_pdf(report: ProductionReportRecord) -> Path:
    settings.production_pdf_storage_dir.mkdir(parents=True, exist_ok=True)
    path = settings.production_pdf_storage_dir / f"production-{report.id}.pdf"

    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), color="#f8f7f2")
    draw = ImageDraw.Draw(image)

    title_font = _load_font(58, bold=True)
    section_font = _load_font(28, bold=True)
    body_font = _load_font(24)
    body_bold_font = _load_font(24, bold=True)
    small_font = _load_font(20)

    draw.rounded_rectangle((MARGIN_X, 70, PAGE_WIDTH - MARGIN_X, 206), radius=28, fill="#1a4d3a")
    draw.text((MARGIN_X + 36, 98), "Производственный отчет", font=title_font, fill="#ffffff")
    draw.text(
        (MARGIN_X + 36, 160),
        "Сменные показатели выпуска, качества и простоев",
        font=small_font,
        fill="#d4ebe3",
    )

    y = 270
    draw.text((MARGIN_X, y), "Смена и участок", font=section_font, fill="#1a4d3a")
    y += 58

    report_date_str = report.report_date.strftime("%d.%m.%Y")
    info_rows = [
        ("Сотрудник", report.employee_name),
        ("Подразделение", report.department),
        ("Производственная линия", report.production_line),
        ("Дата отчета", report_date_str),
        ("Смена", report.shift),
        ("Выпуск", _format_kg(report.quantity_kg)),
        ("Отходы", _format_kg(report.waste_kg)),
        ("Простой", f"{report.downtime_minutes} мин"),
        ("Качество", f"{report.quality_score:.1f} %".replace(".", ",")),
    ]

    for label, value in info_rows:
        draw.text((MARGIN_X + 6, y), label, font=body_font, fill="#4f6579")
        draw.text((MARGIN_X + 420, y), value, font=body_bold_font, fill="#172737")
        y += 54

    y += 14
    draw.text((MARGIN_X, y), "Замечания и инциденты", font=section_font, fill="#1a4d3a")
    y += 56

    issues_text = (report.issues or "").strip() or "Нет замечаний."
    purpose_box = (MARGIN_X, y, PAGE_WIDTH - MARGIN_X, y + 200)
    draw.rounded_rectangle(purpose_box, radius=24, fill="#eef3f7")
    issue_lines = _wrap_text(draw, issues_text, body_font, PAGE_WIDTH - (MARGIN_X * 2) - 56)
    line_y = y + 28
    for line in issue_lines[:6]:
        draw.text((MARGIN_X + 28, line_y), line, font=body_font, fill="#172737")
        line_y += 40

    meta_y = PAGE_HEIGHT - 140
    draw.text(
        (MARGIN_X, meta_y),
        f"Документ № {report.id} · сформировано {report.created_at.strftime('%d.%m.%Y %H:%M')}",
        font=small_font,
        fill="#4f6579",
    )

    sign_y = PAGE_HEIGHT - 220
    draw.line((MARGIN_X + 18, sign_y, MARGIN_X + 290, sign_y), fill="#9eb1c2", width=2)
    draw.line((PAGE_WIDTH - MARGIN_X - 290, sign_y, PAGE_WIDTH - MARGIN_X - 18, sign_y), fill="#9eb1c2", width=2)
    draw.text((MARGIN_X + 72, sign_y + 16), "Подпись мастера смены", font=small_font, fill="#4f6579")
    draw.text((PAGE_WIDTH - MARGIN_X - 248, sign_y + 16), "Подпись технолога", font=small_font, fill="#4f6579")

    image.save(path, "PDF", resolution=150.0)
    return path


def _format_kg(value: float) -> str:
    text = f"{value:,.1f}".replace(",", " ")
    return f"{text.replace('.', ',')} кг"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = value.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        candidate_width = draw.textbbox((0, 0), candidate, font=font)[2]
        if candidate_width <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines


def _format_money(value: float, currency: str = "RUB") -> str:
    text = f"{value:,.2f}".replace(",", " ")
    return f"{text.replace('.', ',')} {currency}"


def _status_label(status: str) -> str:
    labels = {
        "pending": "На согласовании",
        "approved": "Подтвержден",
        "paid": "Оплачен",
    }
    return labels.get(status, status)
