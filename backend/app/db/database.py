from __future__ import annotations

import sqlite3
from collections.abc import Generator
from datetime import date, datetime

from app.core.config import settings
from app.models import (
    ExpenseReportRecord,
    ExpenseStatus,
    PaymentStatus,
    ProductionReportRecord,
    SalaryReportRecord,
    UserRecord,
    UserRole,
)


SAUSAGE_RATE_TJS = 2.0


def open_connection() -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        settings.database_path,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_db() -> Generator[sqlite3.Connection, None, None]:
    connection = open_connection()
    try:
        yield connection
    finally:
        connection.close()


def init_db() -> None:
    with open_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
                position TEXT NOT NULL,
                department TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS production_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                department TEXT NOT NULL,
                production_line TEXT NOT NULL,
                report_date TEXT NOT NULL,
                shift TEXT NOT NULL,
                quantity_kg REAL NOT NULL,
                sausage_units INTEGER NOT NULL DEFAULT 0,
                waste_kg REAL NOT NULL,
                downtime_minutes INTEGER NOT NULL DEFAULT 0,
                quality_score REAL NOT NULL,
                issues TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS expense_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                reference_number TEXT NOT NULL UNIQUE,
                period_label TEXT NOT NULL,
                purpose TEXT NOT NULL,
                amount_requested REAL NOT NULL,
                amount_approved REAL NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'paid')),
                generated_at TEXT NOT NULL,
                pdf_path TEXT,
                FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS salary_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                period_year INTEGER NOT NULL,
                period_month INTEGER NOT NULL,
                base_salary_dirams REAL NOT NULL DEFAULT 0,
                sausage_units INTEGER NOT NULL DEFAULT 0,
                sausage_rate_dirams REAL NOT NULL DEFAULT 2,
                production_bonus_dirams REAL NOT NULL DEFAULT 0,
                premium_dirams REAL NOT NULL DEFAULT 0,
                total_due_dirams REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'paid')) DEFAULT 'pending',
                admin_comment TEXT,
                approved_by INTEGER,
                approved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(employee_id, period_year, period_month),
                FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )
        production_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(production_reports)").fetchall()
        }
        if "sausage_units" not in production_columns:
            connection.execute(
                "ALTER TABLE production_reports ADD COLUMN sausage_units INTEGER NOT NULL DEFAULT 0"
            )
            connection.execute(
                "UPDATE production_reports SET sausage_units = CAST(ROUND(quantity_kg) AS INTEGER)"
            )

        user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "username" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN username TEXT")

        connection.execute(
            """
            UPDATE users
            SET username = CASE
                WHEN role = 'admin' THEN 'admin'
                WHEN email LIKE 'staff1%' THEN 'staff1'
                WHEN email LIKE 'staff2%' THEN 'staff2'
                WHEN username IS NULL OR username = '' THEN lower(substr(email, 1, instr(email, '@') - 1))
                ELSE username
            END
            WHERE username IS NULL OR username = ''
            """
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )

        expense_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(expense_reports)").fetchall()
        }
        if "admin_read" not in expense_columns:
            connection.execute(
                "ALTER TABLE expense_reports ADD COLUMN admin_read INTEGER NOT NULL DEFAULT 0"
            )
            connection.execute("UPDATE expense_reports SET admin_read = 1")

        if "currency" not in expense_columns:
            connection.execute(
                "ALTER TABLE expense_reports ADD COLUMN currency TEXT NOT NULL DEFAULT 'RUB'"
            )

        connection.commit()


def row_to_user(row: sqlite3.Row) -> UserRecord:
    return UserRecord(
        id=int(row["id"]),
        username=str(row["username"]),
        full_name=str(row["full_name"]),
        email=str(row["email"]),
        hashed_password=str(row["hashed_password"]),
        role=UserRole(str(row["role"])),
        position=str(row["position"]),
        department=str(row["department"]),
        is_active=bool(row["is_active"]),
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )


def row_to_production_report(row: sqlite3.Row) -> ProductionReportRecord:
    return ProductionReportRecord(
        id=int(row["id"]),
        employee_id=int(row["employee_id"]),
        employee_name=str(row["employee_name"]),
        department=str(row["department"]),
        production_line=str(row["production_line"]),
        report_date=date.fromisoformat(str(row["report_date"])),
        shift=str(row["shift"]),
        quantity_kg=float(row["quantity_kg"]),
        sausage_units=int(row["sausage_units"]) if "sausage_units" in row.keys() else 0,
        waste_kg=float(row["waste_kg"]),
        downtime_minutes=int(row["downtime_minutes"]),
        quality_score=float(row["quality_score"]),
        issues=str(row["issues"]) if row["issues"] is not None else None,
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )


def row_to_expense_report(row: sqlite3.Row) -> ExpenseReportRecord:
    return ExpenseReportRecord(
        id=int(row["id"]),
        employee_id=int(row["employee_id"]),
        employee_name=str(row["employee_name"]),
        reference_number=str(row["reference_number"]),
        period_label=str(row["period_label"]),
        purpose=str(row["purpose"]),
        amount_requested=float(row["amount_requested"]),
        amount_approved=float(row["amount_approved"]),
        status=ExpenseStatus(str(row["status"])),
        generated_at=datetime.fromisoformat(str(row["generated_at"])),
        pdf_path=str(row["pdf_path"]) if row["pdf_path"] is not None else None,
        admin_read=bool(int(row["admin_read"])),
        currency=str(row["currency"]) if "currency" in row.keys() else "RUB",
    )


def period_label(year: int, month: int) -> str:
    return date(year, month, 1).strftime("%B %Y")


def sync_salary_reports(
    db: sqlite3.Connection,
    year: int,
    month: int,
    employee_id: int | None = None,
) -> None:
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    period_start = date(year, month, 1).isoformat()
    period_end = date(next_year, next_month, 1).isoformat()
    now = datetime.utcnow().replace(microsecond=0).isoformat()

    if employee_id is None:
        staff_rows = db.execute(
            "SELECT id FROM users WHERE role = ? AND is_active = 1",
            (UserRole.STAFF.value,),
        ).fetchall()
    else:
        staff_rows = db.execute(
            "SELECT id FROM users WHERE id = ? AND role = ? AND is_active = 1",
            (employee_id, UserRole.STAFF.value),
        ).fetchall()

    for staff_row in staff_rows:
        staff_id = int(staff_row["id"])
        sausage_units = int(
            db.execute(
                """
                SELECT COALESCE(SUM(sausage_units), 0)
                FROM production_reports
                WHERE employee_id = ?
                  AND report_date >= ?
                  AND report_date < ?
                """,
                (staff_id, period_start, period_end),
            ).fetchone()[0]
        )
        production_bonus = round(sausage_units * SAUSAGE_RATE_TJS, 2)
        existing = db.execute(
            """
            SELECT *
            FROM salary_reports
            WHERE employee_id = ? AND period_year = ? AND period_month = ?
            """,
            (staff_id, year, month),
        ).fetchone()

        if existing is None:
            db.execute(
                """
                INSERT INTO salary_reports (
                    employee_id, period_year, period_month, base_salary_dirams,
                    sausage_units, sausage_rate_dirams, production_bonus_dirams,
                    premium_dirams, total_due_dirams, status, admin_comment,
                    approved_by, approved_at, created_at, updated_at
                )
                VALUES (?, ?, ?, 0, ?, ?, ?, 0, ?, ?, NULL, NULL, NULL, ?, ?)
                """,
                (
                    staff_id,
                    year,
                    month,
                    sausage_units,
                    SAUSAGE_RATE_TJS,
                    production_bonus,
                    production_bonus,
                    PaymentStatus.PENDING.value,
                    now,
                    now,
                ),
            )
            continue

        base_salary = float(existing["base_salary_dirams"])
        premium = float(existing["premium_dirams"])
        total_due = round(base_salary + production_bonus + premium, 2)
        db.execute(
            """
            UPDATE salary_reports
            SET sausage_units = ?,
                sausage_rate_dirams = ?,
                production_bonus_dirams = ?,
                total_due_dirams = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                sausage_units,
                SAUSAGE_RATE_TJS,
                production_bonus,
                total_due,
                now,
                int(existing["id"]),
            ),
        )

    db.commit()


def row_to_salary_report(row: sqlite3.Row) -> SalaryReportRecord:
    return SalaryReportRecord(
        id=int(row["id"]),
        employee_id=int(row["employee_id"]),
        employee_name=str(row["employee_name"]),
        period_year=int(row["period_year"]),
        period_month=int(row["period_month"]),
        period_label=period_label(int(row["period_year"]), int(row["period_month"])),
        base_salary_tjs=float(row["base_salary_dirams"]),
        sausage_units=int(row["sausage_units"]),
        sausage_rate_tjs=float(row["sausage_rate_dirams"]),
        production_bonus_tjs=float(row["production_bonus_dirams"]),
        premium_tjs=float(row["premium_dirams"]),
        total_due_tjs=float(row["total_due_dirams"]),
        status=PaymentStatus(str(row["status"])),
        admin_comment=str(row["admin_comment"]) if row["admin_comment"] is not None else None,
        approved_at=datetime.fromisoformat(str(row["approved_at"])) if row["approved_at"] else None,
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
    )
