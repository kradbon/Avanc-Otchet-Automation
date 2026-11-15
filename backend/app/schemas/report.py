from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import ExpenseStatus, PaymentStatus


AdvanceRequestCurrency = Literal["TJS", "USD", "CNY"]


class ExpenseAdvanceRequestCreate(BaseModel):
    amount_requested: float = Field(gt=0, le=50_000_000)
    purpose: str = Field(min_length=8, max_length=400)
    period_label: str | None = Field(default=None, max_length=80)
    currency: AdvanceRequestCurrency


class ProductionReportCreate(BaseModel):
    department: str = Field(min_length=3, max_length=120)
    production_line: str = Field(min_length=2, max_length=120)
    report_date: date
    shift: str = Field(min_length=1, max_length=30)
    quantity_kg: float = Field(gt=0)
    sausage_units: int = Field(ge=0, le=1_000_000)
    waste_kg: float = Field(ge=0)
    downtime_minutes: int = Field(ge=0)
    quality_score: float = Field(ge=0, le=100)
    issues: str | None = Field(default=None, max_length=400)


class ProductionReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: str
    department: str
    production_line: str
    report_date: date
    shift: str
    quantity_kg: float
    sausage_units: int
    waste_kg: float
    downtime_minutes: int
    quality_score: float
    issues: str | None
    created_at: datetime


class ExpenseReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: str
    reference_number: str
    period_label: str
    purpose: str
    amount_requested: float
    amount_approved: float
    status: ExpenseStatus
    generated_at: datetime
    admin_read: bool
    currency: str


class ExpenseCurrencyBucket(BaseModel):
    currency: str
    total: float


class StaffMetrics(BaseModel):
    total_volume_kg: float
    average_quality: float
    reports_count: int
    latest_expense_status: str
    current_salary_due_tjs: float
    current_salary_status: str


class SalaryApprovalUpdate(BaseModel):
    base_salary_tjs: float = Field(ge=0, le=50_000_000)
    premium_tjs: float = Field(ge=0, le=50_000_000)
    status: PaymentStatus
    admin_comment: str | None = Field(default=None, max_length=400)


class SalaryReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: str
    period_year: int
    period_month: int
    period_label: str
    base_salary_tjs: float
    sausage_units: int
    sausage_rate_tjs: float
    production_bonus_tjs: float
    premium_tjs: float
    total_due_tjs: float
    status: PaymentStatus
    admin_comment: str | None
    approved_at: datetime | None
    updated_at: datetime


class StaffDashboardResponse(BaseModel):
    metrics: StaffMetrics
    recent_reports: list[ProductionReportRead]
    expense_reports: list[ExpenseReportSummary]
    salary_reports: list[SalaryReportSummary]


class DepartmentSummary(BaseModel):
    department: str
    total_volume_kg: float
    average_quality: float
    reports_count: int


class AdminStats(BaseModel):
    active_staff: int
    reports_total: int
    total_output_kg: float
    approved_expense_buckets: list[ExpenseCurrencyBucket]
    average_quality: float
    unread_expense_count: int
    pending_salary_count: int
    payroll_due_tjs: float


class AdminOverviewResponse(BaseModel):
    stats: AdminStats
    department_breakdown: list[DepartmentSummary]
    recent_reports: list[ProductionReportRead]
    expense_reports: list[ExpenseReportSummary]
    salary_reports: list[SalaryReportSummary]
