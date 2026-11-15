export type Role = "admin" | "staff";
export type ExpenseStatus = "pending" | "approved" | "paid";
export type PaymentStatus = "pending" | "approved" | "paid";
export type AdvanceCurrency = "TJS" | "USD" | "CNY";

export interface UserProfile {
  id: number;
  username: string;
  full_name: string;
  email: string;
  role: Role;
  position: string;
  department: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface ProductionReport {
  id: number;
  employee_id: number;
  employee_name: string;
  department: string;
  production_line: string;
  report_date: string;
  shift: string;
  quantity_kg: number;
  sausage_units: number;
  waste_kg: number;
  downtime_minutes: number;
  quality_score: number;
  issues: string | null;
  created_at: string;
}

export interface ExpenseReport {
  id: number;
  employee_id: number;
  employee_name: string;
  reference_number: string;
  period_label: string;
  purpose: string;
  amount_requested: number;
  amount_approved: number;
  status: ExpenseStatus;
  generated_at: string;
  admin_read: boolean;
  currency: string;
}

export interface StaffDashboard {
  metrics: {
    total_volume_kg: number;
    average_quality: number;
    reports_count: number;
    latest_expense_status: string;
    current_salary_due_tjs: number;
    current_salary_status: string;
  };
  recent_reports: ProductionReport[];
  expense_reports: ExpenseReport[];
  salary_reports: SalaryReport[];
}

export interface DepartmentSummary {
  department: string;
  total_volume_kg: number;
  average_quality: number;
  reports_count: number;
}

export interface ExpenseCurrencyBucket {
  currency: string;
  total: number;
}

export interface AdminOverview {
  stats: {
    active_staff: number;
    reports_total: number;
    total_output_kg: number;
    approved_expense_buckets: ExpenseCurrencyBucket[];
    average_quality: number;
    unread_expense_count: number;
    pending_salary_count: number;
    payroll_due_tjs: number;
  };
  department_breakdown: DepartmentSummary[];
  recent_reports: ProductionReport[];
  expense_reports: ExpenseReport[];
  salary_reports: SalaryReport[];
}

export interface SalaryReport {
  id: number;
  employee_id: number;
  employee_name: string;
  period_year: number;
  period_month: number;
  period_label: string;
  base_salary_tjs: number;
  sausage_units: number;
  sausage_rate_tjs: number;
  production_bonus_tjs: number;
  premium_tjs: number;
  total_due_tjs: number;
  status: PaymentStatus;
  admin_comment: string | null;
  approved_at: string | null;
  updated_at: string;
}
