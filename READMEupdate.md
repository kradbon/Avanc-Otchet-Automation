# README Update - Staff Payment System

This file describes the new staff payment functionality added to the Avanc Otchet Automation system. It can be used later in a project report or technical documentation.

## 1. Feature Summary

The system now includes a monthly staff payment module. Each staff member can see how much salary they can receive at the end of the month, and every payment must be reviewed and approved by the admin.

Main additions:

- monthly salary records for every staff member;
- production bonus for each produced колбаса;
- premium/премия for the best staff member of the month;
- admin approval before salary is confirmed;
- payment status tracking: `pending`, `approved`, `paid`;
- staff salary history in the staff dashboard;
- salary approval cards in the admin dashboard.

## 2. Payment Calculation

The production bonus is calculated in TJS.

```text
production_bonus = sausage_units * 2 TJS
total_salary = base_salary + production_bonus + premium
```

Example:

```text
base_salary = 2500 TJS
sausage_units = 1500
premium = 500 TJS

production_bonus = 1500 * 2 TJS = 3000 TJS
total_salary = 2500 TJS + 3000 TJS + 500 TJS = 6000 TJS
```

## 3. Staff Workflow

Staff create production reports as before, but the form now also includes колбаса quantity.

Example production report payload:

```json
{
  "department": "Колбасный цех",
  "production_line": "Линия А",
  "report_date": "2026-05-29",
  "shift": "Дневная",
  "quantity_kg": 1500,
  "sausage_units": 1500,
  "waste_kg": 12,
  "downtime_minutes": 10,
  "quality_score": 96,
  "issues": null
}
```

When the report is saved, the salary record for that staff member and month is synchronized automatically.

Staff can see:

- current monthly salary total;
- salary approval status;
- base salary;
- колбаса production bonus;
- premium/премия;
- admin comment;
- previous monthly salary records.

## 4. Admin Workflow

Admin can review salary records in the admin dashboard. For each staff member and month, admin can set:

- base salary in TJS;
- premium/премия in TJS;
- status: `pending`, `approved`, or `paid`;
- admin comment.

Example admin approval payload:

```json
{
  "base_salary_tjs": 2500,
  "premium_tjs": 500,
  "status": "approved",
  "admin_comment": "Best staff of the month premium approved."
}
```

## 5. New API Endpoints

Staff endpoints:

```text
GET /api/staff/salary-reports
```

Returns the logged-in staff member's salary history.

Admin endpoints:

```text
GET /api/admin/salary-reports
POST /api/admin/salary-reports/{salary_report_id}/approval
```

The `POST` endpoint updates base salary, premium, status, and admin comment.

## 6. Backend Code Example

Salary synchronization uses the monthly production reports and applies the 2 TJS per колбаса rule.

```python
SAUSAGE_RATE_TJS = 2.0

production_bonus = round(sausage_units * SAUSAGE_RATE_TJS, 2)
total_due = round(base_salary + production_bonus + premium, 2)
```

The synchronization runs when:

- staff opens their dashboard;
- admin opens the overview;
- staff creates a new production report.

## 7. Database Additions

Production reports now store колбаса units:

```sql
ALTER TABLE production_reports
ADD COLUMN sausage_units INTEGER NOT NULL DEFAULT 0;
```

New salary table, simplified for documentation:

```sql
CREATE TABLE salary_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,
    base_salary_tjs REAL NOT NULL DEFAULT 0,
    sausage_units INTEGER NOT NULL DEFAULT 0,
    sausage_rate_tjs REAL NOT NULL DEFAULT 2,
    production_bonus_tjs REAL NOT NULL DEFAULT 0,
    premium_tjs REAL NOT NULL DEFAULT 0,
    total_due_tjs REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    admin_comment TEXT,
    approved_by INTEGER,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(employee_id, period_year, period_month)
);
```

## 8. Frontend Changes

Staff dashboard:

- added "Зарплата за месяц" metric;
- added salary history cards;
- added колбаса unit input in the production report form;
- added колбаса units column in the report table.

Admin dashboard:

- added "Зарплаты на согласовании" metric;
- added "К выплате персоналу" metric in TJS;
- added salary approval section;
- added editable base salary, premium, status, and comment fields.

## 9. Status Meaning

```text
pending  - waiting for admin review
approved - admin approved the salary amount
paid     - salary was paid to the staff member
```

## 10. Short Report Text

The system was extended with a staff payment module. The module calculates monthly salary based on base salary, production bonus, and premium. For every produced колбаса, the staff member receives 2 TJS. At the end of the month, staff can see the full amount they can receive. The admin reviews every salary report, can add a premium for the best staff member of the month, and must approve or mark the salary as paid.
