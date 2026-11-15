from __future__ import annotations

import sqlite3
from datetime import date
from datetime import datetime as dt

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_role
from app.db.database import (
    get_db,
    row_to_expense_report,
    row_to_production_report,
    row_to_salary_report,
    sync_salary_reports,
)
from app.models import ExpenseStatus, UserRecord, UserRole
from app.schemas.report import (
    ExpenseAdvanceRequestCreate,
    ExpenseReportSummary,
    ProductionReportCreate,
    ProductionReportRead,
    SalaryReportSummary,
    StaffDashboardResponse,
    StaffMetrics,
)


router = APIRouter(prefix="/staff", tags=["staff"])

_MONTH_NAMES = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _default_period_label() -> str:
    today = date.today()
    return f"{_MONTH_NAMES[today.month]} {today.year}"


@router.get("/dashboard", response_model=StaffDashboardResponse)
def get_dashboard(
    current_user: UserRecord = Depends(require_role(UserRole.STAFF)),
    db: sqlite3.Connection = Depends(get_db),
) -> StaffDashboardResponse:
    today = date.today()
    sync_salary_reports(db, today.year, today.month, current_user.id)
    monthly_rows = db.execute(
        """
        SELECT pr.*, u.full_name AS employee_name
        FROM production_reports pr
        JOIN users u ON u.id = pr.employee_id
        WHERE pr.employee_id = ?
          AND strftime('%Y', pr.report_date) = ?
          AND strftime('%m', pr.report_date) = ?
        ORDER BY pr.report_date DESC, pr.created_at DESC
        """,
        (current_user.id, str(today.year), f"{today.month:02d}"),
    ).fetchall()
    monthly_reports = [row_to_production_report(row) for row in monthly_rows]
    recent_reports = monthly_reports[:5]

    total_volume = sum(report.quantity_kg for report in monthly_reports)
    reports_count = len(monthly_reports)
    average_quality = (
        sum(report.quality_score for report in monthly_reports) / reports_count if reports_count else 0.0
    )

    expense_rows = db.execute(
        """
        SELECT er.*, u.full_name AS employee_name
        FROM expense_reports er
        JOIN users u ON u.id = er.employee_id
        WHERE er.employee_id = ?
        ORDER BY er.generated_at DESC
        """,
        (current_user.id,),
    ).fetchall()
    expense_reports = [row_to_expense_report(row) for row in expense_rows]
    latest_expense_status = expense_reports[0].status.value if expense_reports else "no data"

    salary_rows = db.execute(
        """
        SELECT sr.*, u.full_name AS employee_name
        FROM salary_reports sr
        JOIN users u ON u.id = sr.employee_id
        WHERE sr.employee_id = ?
        ORDER BY sr.period_year DESC, sr.period_month DESC
        """,
        (current_user.id,),
    ).fetchall()
    salary_reports = [row_to_salary_report(row) for row in salary_rows]
    current_salary = salary_reports[0] if salary_reports else None

    return StaffDashboardResponse(
        metrics=StaffMetrics(
            total_volume_kg=round(total_volume, 1),
            average_quality=round(average_quality, 1),
            reports_count=reports_count,
            latest_expense_status=latest_expense_status,
            current_salary_due_tjs=round(current_salary.total_due_tjs, 2) if current_salary else 0,
            current_salary_status=current_salary.status.value if current_salary else "pending",
        ),
        recent_reports=[ProductionReportRead.model_validate(report) for report in recent_reports],
        expense_reports=[ExpenseReportSummary.model_validate(report) for report in expense_reports],
        salary_reports=[SalaryReportSummary.model_validate(report) for report in salary_reports],
    )


@router.get("/reports", response_model=list[ProductionReportRead])
def list_reports(
    current_user: UserRecord = Depends(require_role(UserRole.STAFF)),
    db: sqlite3.Connection = Depends(get_db),
) -> list[ProductionReportRead]:
    rows = db.execute(
        """
        SELECT pr.*, u.full_name AS employee_name
        FROM production_reports pr
        JOIN users u ON u.id = pr.employee_id
        WHERE pr.employee_id = ?
        ORDER BY pr.report_date DESC, pr.created_at DESC
        """,
        (current_user.id,),
    ).fetchall()
    return [ProductionReportRead.model_validate(row_to_production_report(row)) for row in rows]


@router.post("/reports", response_model=ProductionReportRead, status_code=201)
def create_report(
    payload: ProductionReportCreate,
    current_user: UserRecord = Depends(require_role(UserRole.STAFF)),
    db: sqlite3.Connection = Depends(get_db),
) -> ProductionReportRead:
    cursor = db.execute(
        """
        INSERT INTO production_reports (
            employee_id, department, production_line, report_date, shift, quantity_kg,
            sausage_units, waste_kg, downtime_minutes, quality_score, issues, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_user.id,
            payload.department,
            payload.production_line,
            payload.report_date.isoformat(),
            payload.shift,
            payload.quantity_kg,
            payload.sausage_units,
            payload.waste_kg,
            payload.downtime_minutes,
            payload.quality_score,
            payload.issues,
            dt.utcnow().replace(microsecond=0).isoformat(),
        ),
    )
    db.commit()
    sync_salary_reports(db, payload.report_date.year, payload.report_date.month, current_user.id)
    row = db.execute(
        """
        SELECT pr.*, u.full_name AS employee_name
        FROM production_reports pr
        JOIN users u ON u.id = pr.employee_id
        WHERE pr.id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return ProductionReportRead.model_validate(row_to_production_report(row))


@router.get("/expense-reports", response_model=list[ExpenseReportSummary])
def list_expense_reports(
    current_user: UserRecord = Depends(require_role(UserRole.STAFF)),
    db: sqlite3.Connection = Depends(get_db),
) -> list[ExpenseReportSummary]:
    rows = db.execute(
        """
        SELECT er.*, u.full_name AS employee_name
        FROM expense_reports er
        JOIN users u ON u.id = er.employee_id
        WHERE er.employee_id = ?
        ORDER BY er.generated_at DESC
        """,
        (current_user.id,),
    ).fetchall()
    return [ExpenseReportSummary.model_validate(row_to_expense_report(row)) for row in rows]


@router.get("/salary-reports", response_model=list[SalaryReportSummary])
def list_salary_reports(
    current_user: UserRecord = Depends(require_role(UserRole.STAFF)),
    db: sqlite3.Connection = Depends(get_db),
) -> list[SalaryReportSummary]:
    today = date.today()
    sync_salary_reports(db, today.year, today.month, current_user.id)
    rows = db.execute(
        """
        SELECT sr.*, u.full_name AS employee_name
        FROM salary_reports sr
        JOIN users u ON u.id = sr.employee_id
        WHERE sr.employee_id = ?
        ORDER BY sr.period_year DESC, sr.period_month DESC
        """,
        (current_user.id,),
    ).fetchall()
    return [SalaryReportSummary.model_validate(row_to_salary_report(row)) for row in rows]


@router.post("/expense-reports", response_model=ExpenseReportSummary, status_code=201)
def create_expense_request(
    payload: ExpenseAdvanceRequestCreate,
    current_user: UserRecord = Depends(require_role(UserRole.STAFF)),
    db: sqlite3.Connection = Depends(get_db),
) -> ExpenseReportSummary:
    generated_at = dt.utcnow().replace(microsecond=0)
    reference_number = f"AO-REQ-{generated_at.strftime('%Y%m%d%H%M%S')}-{current_user.id}"
    period_label = (payload.period_label.strip() if payload.period_label else "") or _default_period_label()

    cursor = db.execute(
        """
        INSERT INTO expense_reports (
            employee_id, reference_number, period_label, purpose,
            amount_requested, amount_approved, status, generated_at, pdf_path, admin_read, currency
        )
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, NULL, 0, ?)
        """,
        (
            current_user.id,
            reference_number,
            period_label,
            payload.purpose.strip(),
            payload.amount_requested,
            ExpenseStatus.PENDING.value,
            generated_at.isoformat(),
            payload.currency,
        ),
    )
    db.commit()

    row = db.execute(
        """
        SELECT er.*, u.full_name AS employee_name
        FROM expense_reports er
        JOIN users u ON u.id = er.employee_id
        WHERE er.id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Could not create advance request.")
    return ExpenseReportSummary.model_validate(row_to_expense_report(row))
