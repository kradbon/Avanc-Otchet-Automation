from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

from app.core.security import get_password_hash
from app.models import ExpenseReportRecord, ExpenseStatus, UserRecord, UserRole
from app.services.pdf import generate_expense_report_pdf


def seed_database(db: sqlite3.Connection) -> None:
    users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if users_count and users_count > 0:
        _synchronize_demo_credentials(db)
        return

    now = datetime.utcnow().replace(microsecond=0)
    users = [
        (
            "admin",
            "Ирина Волкова",
            "admin@avancfactory.com",
            get_password_hash("admin"),
            UserRole.ADMIN.value,
            "Руководитель административного контроля",
            "Администрация",
        ),
        (
            "staff1",
            "Алексей Панов",
            "staff1@avancfactory.com",
            get_password_hash("staff1"),
            UserRole.STAFF.value,
            "Старший мастер смены",
            "Колбасный цех",
        ),
        (
            "staff2",
            "Марина Белова",
            "staff2@avancfactory.com",
            get_password_hash("staff2"),
            UserRole.STAFF.value,
            "Технолог линии упаковки",
            "Упаковочный участок",
        ),
    ]

    user_records: dict[str, UserRecord] = {}
    for username, full_name, email, hashed_password, role, position, department in users:
        cursor = db.execute(
            """
            INSERT INTO users (
                username, full_name, email, hashed_password, role, position, department, is_active, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (username, full_name, email, hashed_password, role, position, department, now.isoformat()),
        )
        user_records[email] = UserRecord(
            id=int(cursor.lastrowid),
            username=username,
            full_name=full_name,
            email=email,
            hashed_password=hashed_password,
            role=UserRole(role),
            position=position,
            department=department,
            is_active=True,
            created_at=now,
        )

    today = date.today()
    report_rows = [
        (
            user_records["staff1@avancfactory.com"].id,
            "Колбасный цех",
            "Линия А",
            (today - timedelta(days=1)).isoformat(),
            "Дневная",
            1820.5,
            28.3,
            14,
            96.4,
            "Кратковременная перенастройка дозатора.",
            (now - timedelta(days=1)).isoformat(),
        ),
        (
            user_records["staff1@avancfactory.com"].id,
            "Колбасный цех",
            "Линия B",
            (today - timedelta(days=3)).isoformat(),
            "Ночная",
            1654.0,
            35.1,
            22,
            94.8,
            "Останов линии на санитарную обработку.",
            (now - timedelta(days=3)).isoformat(),
        ),
        (
            user_records["staff2@avancfactory.com"].id,
            "Упаковочный участок",
            "Упаковка 1",
            (today - timedelta(days=1)).isoformat(),
            "Дневная",
            1210.0,
            14.0,
            8,
            97.2,
            "Без замечаний.",
            (now - timedelta(days=1)).isoformat(),
        ),
        (
            user_records["staff2@avancfactory.com"].id,
            "Упаковочный участок",
            "Упаковка 2",
            (today - timedelta(days=4)).isoformat(),
            "Вечерняя",
            1148.4,
            18.7,
            17,
            95.5,
            "Замена термоленты, регламентно.",
            (now - timedelta(days=4)).isoformat(),
        ),
    ]
    production_rows = [row[:6] + (int(round(row[5])),) + row[6:] for row in report_rows]
    db.executemany(
        """
        INSERT INTO production_reports (
            employee_id, department, production_line, report_date, shift, quantity_kg,
            sausage_units, waste_kg, downtime_minutes, quality_score, issues, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        production_rows,
    )

    expense_inputs = [
        (
            user_records["staff1@avancfactory.com"],
            "AO-2026-041",
            "Май 2026",
            "Закупка расходных материалов и транспортные расходы по служебным выездам в рамках контроля колбасного цеха.",
            18450.0,
            17600.0,
            ExpenseStatus.APPROVED,
            now - timedelta(days=2),
        ),
        (
            user_records["staff2@avancfactory.com"],
            "AO-2026-042",
            "Май 2026",
            "Командировочные и хозяйственные расходы, связанные с аудитом линии упаковки и внутренним нормоконтролем.",
            13200.0,
            13200.0,
            ExpenseStatus.PAID,
            now - timedelta(days=1),
        ),
    ]

    created_expense_reports: list[tuple[ExpenseReportRecord, UserRecord]] = []
    for employee, reference_number, period_label, purpose, amount_requested, amount_approved, status, generated_at in expense_inputs:
        cursor = db.execute(
            """
            INSERT INTO expense_reports (
                employee_id, reference_number, period_label, purpose,
                amount_requested, amount_approved, status, generated_at, pdf_path, admin_read, currency
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 1, ?)
            """,
            (
                employee.id,
                reference_number,
                period_label,
                purpose,
                amount_requested,
                amount_approved,
                status.value,
                generated_at.replace(microsecond=0).isoformat(),
                "RUB",
            ),
        )
        created_expense_reports.append(
            (
                ExpenseReportRecord(
                    id=int(cursor.lastrowid),
                    employee_id=employee.id,
                    employee_name=employee.full_name,
                    reference_number=reference_number,
                    period_label=period_label,
                    purpose=purpose,
                    amount_requested=amount_requested,
                    amount_approved=amount_approved,
                    status=status,
                    generated_at=generated_at.replace(microsecond=0),
                    pdf_path=None,
                    admin_read=True,
                    currency="RUB",
                ),
                employee,
            )
        )

    db.commit()

    for expense_report, employee in created_expense_reports:
        pdf_path = generate_expense_report_pdf(expense_report, employee)
        db.execute(
            "UPDATE expense_reports SET pdf_path = ? WHERE id = ?",
            (str(pdf_path), expense_report.id),
        )
    db.commit()


def _synchronize_demo_credentials(db: sqlite3.Connection) -> None:
    credentials = [
        ("admin", "admin", "admin@avancfactory.com", UserRole.ADMIN.value),
        ("staff1", "staff1", "staff1@avancfactory.com", UserRole.STAFF.value),
        ("staff2", "staff2", "staff2@avancfactory.com", UserRole.STAFF.value),
    ]
    for username, password, email, role in credentials:
        db.execute(
            """
            UPDATE users
            SET username = ?, email = ?, hashed_password = ?
            WHERE role = ?
              AND (username = ? OR email = ? OR (role = 'admin' AND full_name LIKE 'Ирина%'))
            """,
            (username, email, get_password_hash(password), role, username, email),
        )
    db.commit()
