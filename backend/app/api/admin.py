from __future__ import annotations

from datetime import date
from datetime import datetime as dt
from pathlib import Path
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.security import require_role
from app.db.database import (
    get_db,
    row_to_expense_report,
    row_to_production_report,
    row_to_salary_report,
    row_to_user,
    sync_salary_reports,
)
from app.models import ExpenseStatus, UserRecord, UserRole
from app.schemas.report import (
    AdminOverviewResponse,
    AdminStats,
    DepartmentSummary,
    ExpenseCurrencyBucket,
    ExpenseReportSummary,
    ProductionReportRead,
    SalaryApprovalUpdate,
    SalaryReportSummary,
)
from app.services.pdf import generate_expense_report_pdf, generate_production_report_pdf


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
def get_overview(
    _: UserRecord = Depends(require_role(UserRole.ADMIN)),
    db: sqlite3.Connection = Depends(get_db),
) -> AdminOverviewResponse:
    today = date.today()
    sync_salary_reports(db, today.year, today.month)
    staff_count = db.execute(
        "SELECT COUNT(*) FROM users WHERE role = ? AND is_active = 1",
        (UserRole.STAFF.value,),
    ).fetchone()[0]
    reports_total = db.execute("SELECT COUNT(*) FROM production_reports").fetchone()[0]
    total_output = db.execute("SELECT COALESCE(SUM(quantity_kg), 0) FROM production_reports").fetchone()[0]
    average_quality = db.execute("SELECT COALESCE(AVG(quality_score), 0) FROM production_reports").fetchone()[0]
    bucket_rows = db.execute(
        """
        SELECT currency, COALESCE(SUM(amount_approved), 0)
        FROM expense_reports
        WHERE status IN (?, ?)
        GROUP BY currency
        ORDER BY currency
        """,
        (ExpenseStatus.APPROVED.value, ExpenseStatus.PAID.value),
    ).fetchall()
    approved_expense_buckets = [
        ExpenseCurrencyBucket(currency=str(row[0]), total=round(float(row[1]), 2)) for row in bucket_rows
    ]
    unread_expense_count = int(
        db.execute("SELECT COUNT(*) FROM expense_reports WHERE admin_read = 0").fetchone()[0]
    )
    pending_salary_count = int(
        db.execute("SELECT COUNT(*) FROM salary_reports WHERE status = 'pending'").fetchone()[0]
    )
    payroll_due_tjs = float(
        db.execute(
            "SELECT COALESCE(SUM(total_due_dirams), 0) FROM salary_reports WHERE status IN ('pending', 'approved')"
        ).fetchone()[0]
    )

    department_rows = db.execute(
        """
        SELECT department,
               COALESCE(SUM(quantity_kg), 0),
               COALESCE(AVG(quality_score), 0),
               COUNT(id)
        FROM production_reports
        GROUP BY department
        ORDER BY SUM(quantity_kg) DESC
        """
    ).fetchall()

    report_rows = db.execute(
        """
        SELECT pr.*, u.full_name AS employee_name
        FROM production_reports pr
        JOIN users u ON u.id = pr.employee_id
        ORDER BY pr.report_date DESC, pr.created_at DESC
        """
    ).fetchall()
    reports = [row_to_production_report(row) for row in report_rows]

    expense_rows = db.execute(
        """
        SELECT er.*, u.full_name AS employee_name
        FROM expense_reports er
        JOIN users u ON u.id = er.employee_id
        ORDER BY er.admin_read ASC, er.generated_at DESC
        """
    ).fetchall()
    expense_reports = [row_to_expense_report(row) for row in expense_rows]
    salary_rows = db.execute(
        """
        SELECT sr.*, u.full_name AS employee_name
        FROM salary_reports sr
        JOIN users u ON u.id = sr.employee_id
        ORDER BY sr.period_year DESC, sr.period_month DESC, u.full_name
        """
    ).fetchall()
    salary_reports = [row_to_salary_report(row) for row in salary_rows]

    return AdminOverviewResponse(
        stats=AdminStats(
            active_staff=staff_count,
            reports_total=reports_total,
            total_output_kg=round(total_output, 1),
            approved_expense_buckets=approved_expense_buckets,
            average_quality=round(average_quality, 1),
            unread_expense_count=unread_expense_count,
            pending_salary_count=pending_salary_count,
            payroll_due_tjs=round(payroll_due_tjs, 2),
        ),
        department_breakdown=[
            DepartmentSummary(
                department=department,
                total_volume_kg=round(total_volume, 1),
                average_quality=round(avg_quality, 1),
                reports_count=reports_count,
            )
            for department, total_volume, avg_quality, reports_count in department_rows
        ],
        recent_reports=[ProductionReportRead.model_validate(report) for report in reports[:10]],
        expense_reports=[ExpenseReportSummary.model_validate(report) for report in expense_reports],
        salary_reports=[SalaryReportSummary.model_validate(report) for report in salary_reports],
    )


@router.get("/reports", response_model=list[ProductionReportRead])
def list_reports(
    _: UserRecord = Depends(require_role(UserRole.ADMIN)),
    db: sqlite3.Connection = Depends(get_db),
) -> list[ProductionReportRead]:
    rows = db.execute(
        """
        SELECT pr.*, u.full_name AS employee_name
        FROM production_reports pr
        JOIN users u ON u.id = pr.employee_id
        ORDER BY pr.report_date DESC, pr.created_at DESC
        """
    ).fetchall()
    return [ProductionReportRead.model_validate(row_to_production_report(row)) for row in rows]


@router.get("/salary-reports", response_model=list[SalaryReportSummary])
def list_salary_reports(
    _: UserRecord = Depends(require_role(UserRole.ADMIN)),
    db: sqlite3.Connection = Depends(get_db),
) -> list[SalaryReportSummary]:
    today = date.today()
    sync_salary_reports(db, today.year, today.month)
    rows = db.execute(
        """
        SELECT sr.*, u.full_name AS employee_name
        FROM salary_reports sr
        JOIN users u ON u.id = sr.employee_id
        ORDER BY sr.period_year DESC, sr.period_month DESC, u.full_name
        """
    ).fetchall()
    return [SalaryReportSummary.model_validate(row_to_salary_report(row)) for row in rows]


@router.post("/salary-reports/{salary_report_id}/approval", response_model=SalaryReportSummary)
def update_salary_approval(
    salary_report_id: int,
    payload: SalaryApprovalUpdate,
    current_user: UserRecord = Depends(require_role(UserRole.ADMIN)),
    db: sqlite3.Connection = Depends(get_db),
) -> SalaryReportSummary:
    salary_row = db.execute(
        "SELECT * FROM salary_reports WHERE id = ?",
        (salary_report_id,),
    ).fetchone()
    if salary_row is None:
        raise HTTPException(status_code=404, detail="Salary report not found.")

    production_bonus = float(salary_row["production_bonus_dirams"])
    total_due = round(payload.base_salary_tjs + production_bonus + payload.premium_tjs, 2)
    approved_at = (
        dt.utcnow().replace(microsecond=0).isoformat()
        if payload.status.value in {"approved", "paid"}
        else None
    )
    approved_by = current_user.id if approved_at else None
    db.execute(
        """
        UPDATE salary_reports
        SET base_salary_dirams = ?,
            premium_dirams = ?,
            total_due_dirams = ?,
            status = ?,
            admin_comment = ?,
            approved_by = ?,
            approved_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            payload.base_salary_tjs,
            payload.premium_tjs,
            total_due,
            payload.status.value,
            payload.admin_comment.strip() if payload.admin_comment else None,
            approved_by,
            approved_at,
            dt.utcnow().replace(microsecond=0).isoformat(),
            salary_report_id,
        ),
    )
    db.commit()
    row = db.execute(
        """
        SELECT sr.*, u.full_name AS employee_name
        FROM salary_reports sr
        JOIN users u ON u.id = sr.employee_id
        WHERE sr.id = ?
        """,
        (salary_report_id,),
    ).fetchone()
    return SalaryReportSummary.model_validate(row_to_salary_report(row))


@router.get("/reports/{report_id}/pdf")
def get_production_report_pdf(
    report_id: int,
    download: bool = Query(default=False),
    _: UserRecord = Depends(require_role(UserRole.ADMIN)),
    db: sqlite3.Connection = Depends(get_db),
) -> FileResponse:
    row = db.execute(
        """
        SELECT pr.*, u.full_name AS employee_name
        FROM production_reports pr
        JOIN users u ON u.id = pr.employee_id
        WHERE pr.id = ?
        """,
        (report_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Производственный отчет не найден.")

    report = row_to_production_report(row)
    pdf_path = generate_production_report_pdf(report)
    filename = f"production-report-{report.id}.pdf"
    disposition = "attachment" if download else "inline"
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@router.get("/expense-reports", response_model=list[ExpenseReportSummary])
def list_expense_reports(
    _: UserRecord = Depends(require_role(UserRole.ADMIN)),
    db: sqlite3.Connection = Depends(get_db),
) -> list[ExpenseReportSummary]:
    rows = db.execute(
        """
        SELECT er.*, u.full_name AS employee_name
        FROM expense_reports er
        JOIN users u ON u.id = er.employee_id
        ORDER BY er.admin_read ASC, er.generated_at DESC
        """
    ).fetchall()
    return [ExpenseReportSummary.model_validate(row_to_expense_report(row)) for row in rows]


@router.get("/expense-reports/{report_id}/pdf")
def get_expense_pdf(
    report_id: int,
    download: bool = Query(default=False),
    _: UserRecord = Depends(require_role(UserRole.ADMIN)),
    db: sqlite3.Connection = Depends(get_db),
) -> FileResponse:
    expense_row = db.execute(
        """
        SELECT er.*, u.full_name AS employee_name
        FROM expense_reports er
        JOIN users u ON u.id = er.employee_id
        WHERE er.id = ?
        """,
        (report_id,),
    ).fetchone()
    if expense_row is None:
        raise HTTPException(status_code=404, detail="Авансовый отчет не найден.")

    db.execute("UPDATE expense_reports SET admin_read = 1 WHERE id = ?", (report_id,))
    db.commit()

    user_row = db.execute("SELECT * FROM users WHERE id = ?", (expense_row["employee_id"],)).fetchone()
    report = row_to_expense_report(expense_row)
    employee = row_to_user(user_row)
    pdf_path = Path(report.pdf_path) if report.pdf_path else None
    if pdf_path is None or not pdf_path.exists():
        pdf_path = generate_expense_report_pdf(report, employee)
        db.execute(
            "UPDATE expense_reports SET pdf_path = ? WHERE id = ?",
            (str(pdf_path), report.id),
        )
        db.commit()

    disposition = "attachment" if download else "inline"
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{report.reference_number}.pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{report.reference_number}.pdf"'},
    )
