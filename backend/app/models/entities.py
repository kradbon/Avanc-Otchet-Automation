from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"


class ExpenseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"


@dataclass
class UserRecord:
    id: int
    username: str
    full_name: str
    email: str
    hashed_password: str
    role: UserRole
    position: str
    department: str
    is_active: bool
    created_at: datetime


@dataclass
class ProductionReportRecord:
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


@dataclass
class ExpenseReportRecord:
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
    pdf_path: str | None
    admin_read: bool
    currency: str


@dataclass
class SalaryReportRecord:
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
