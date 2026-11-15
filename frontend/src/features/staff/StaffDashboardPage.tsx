import { FormEvent, useEffect, useState, useTransition } from "react";
import { api } from "../../api/client";
import ApiUnavailableState from "../../components/ApiUnavailableState";
import MetricCard from "../../components/MetricCard";
import StatusBadge from "../../components/StatusBadge";
import { formatDate, formatMoneyAmount, formatNumber } from "../../lib/formatters";
import { AdvanceCurrency, ExpenseReport, ProductionReport, StaffDashboard } from "../../lib/types";
import { useAuth } from "../auth/AuthContext";

type ReportFormState = {
  department: string;
  production_line: string;
  report_date: string;
  shift: string;
  quantity_kg: string;
  sausage_units: string;
  waste_kg: string;
  downtime_minutes: string;
  quality_score: string;
  issues: string;
};

const today = new Date().toISOString().slice(0, 10);

export default function StaffDashboardPage() {
  const { token, user } = useAuth();
  const [dashboard, setDashboard] = useState<StaffDashboard | null>(null);
  const [reports, setReports] = useState<ProductionReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, startTransition] = useTransition();
  const [advanceCurrency, setAdvanceCurrency] = useState<AdvanceCurrency>("TJS");
  const [advanceAmount, setAdvanceAmount] = useState("5000");
  const [advancePurpose, setAdvancePurpose] = useState(
    "Запрос аванса на закупку расходных материалов и сопутствующие расходы по производственной необходимости."
  );
  const [advancePeriod, setAdvancePeriod] = useState("");
  const [advanceError, setAdvanceError] = useState("");
  const [advanceSubmitting, setAdvanceSubmitting] = useState(false);
  const [form, setForm] = useState<ReportFormState>({
    department: user?.department ?? "Колбасный цех",
    production_line: "Линия А",
    report_date: today,
    shift: "Дневная",
    quantity_kg: "1500",
    sausage_units: "1500",
    waste_kg: "12",
    downtime_minutes: "10",
    quality_score: "96",
    issues: ""
  });

  const loadData = async () => {
    if (!token) {
      return;
    }

    setError("");
    const [dashboardData, reportsData] = await Promise.all([
      api.get<StaffDashboard>("/staff/dashboard", token),
      api.get<ProductionReport[]>("/staff/reports", token)
    ]);
    setDashboard(dashboardData);
    setReports(reportsData);
  };

  useEffect(() => {
    if (!token || !user) {
      return;
    }

    setForm((current) => ({ ...current, department: user.department }));

    void (async () => {
      try {
        await loadData();
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить кабинет.");
      } finally {
        setLoading(false);
      }
    })();
  }, [token, user]);

  const updateField = (field: keyof ReportFormState, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) {
      return;
    }

    setSubmitError("");

    try {
      await api.post<ProductionReport>(
        "/staff/reports",
        {
          department: form.department,
          production_line: form.production_line,
          report_date: form.report_date,
          shift: form.shift,
          quantity_kg: Number(form.quantity_kg),
          sausage_units: Number(form.sausage_units),
          waste_kg: Number(form.waste_kg),
          downtime_minutes: Number(form.downtime_minutes),
          quality_score: Number(form.quality_score),
          issues: form.issues || null
        },
        token
      );

      setForm((current) => ({
        ...current,
        report_date: today,
        quantity_kg: "1500",
        sausage_units: "1500",
        waste_kg: "12",
        downtime_minutes: "10",
        quality_score: "96",
        issues: ""
      }));

      startTransition(() => {
        void loadData();
      });
    } catch (createError) {
      setSubmitError(createError instanceof Error ? createError.message : "Не удалось сохранить отчет.");
    }
  };

  const handleAdvanceSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) {
      return;
    }

    setAdvanceError("");
    const amount = Number(advanceAmount.replace(",", "."));
    if (!Number.isFinite(amount) || amount <= 0) {
      setAdvanceError("Укажите корректную сумму.");
      return;
    }
    if (advancePurpose.trim().length < 8) {
      setAdvanceError("Опишите назначение запроса (не менее 8 символов).");
      return;
    }

    setAdvanceSubmitting(true);
    try {
      await api.post<ExpenseReport>(
        "/staff/expense-reports",
        {
          amount_requested: amount,
          purpose: advancePurpose.trim(),
          period_label: advancePeriod.trim() || null,
          currency: advanceCurrency
        },
        token
      );
      startTransition(() => {
        void loadData();
      });
    } catch (advanceErr) {
      setAdvanceError(advanceErr instanceof Error ? advanceErr.message : "Не удалось отправить запрос.");
    } finally {
      setAdvanceSubmitting(false);
    }
  };

  if (loading) {
    return <div className="empty-state">Загружаем персональный кабинет…</div>;
  }

  if (error || !dashboard) {
    return <ApiUnavailableState message={error || "Данные недоступны."} />;
  }

  return (
    <div className="dashboard-grid">
      <section className="hero-panel hero-panel--staff">
        <div>
          <span className="eyebrow">Личный кабинет</span>
          <h3>{user?.full_name}</h3>
          <p>
            Ведите сменные отчеты по цеху, отслеживайте ключевые показатели и контролируйте
            финансовые документы без бумажной рутины.
          </p>
        </div>
        <div className="hero-panel__meta">
          <span>{user?.position}</span>
          <span>{user?.department}</span>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard
          label="Выпуск за месяц"
          value={`${formatNumber(dashboard.metrics.total_volume_kg)} кг`}
          hint="Суммарный объем по текущему месяцу"
          tone="gold"
        />
        <MetricCard
          label="Среднее качество"
          value={`${formatNumber(dashboard.metrics.average_quality)}%`}
          hint="Индикатор по вашим последним отчетам"
          tone="green"
        />
        <MetricCard
          label="Сдано отчетов"
          value={String(dashboard.metrics.reports_count)}
          hint="Количество подтвержденных записей"
        />
        <MetricCard
          label="Зарплата за месяц"
          value={formatMoneyAmount(dashboard.metrics.current_salary_due_tjs, "TJS")}
          hint={`Статус: ${dashboard.metrics.current_salary_status}`}
          tone="green"
        />
        <MetricCard
          label="Статус аванса"
          value={dashboard.metrics.latest_expense_status}
          hint="Последний финансовый документ"
          tone="navy"
        />
      </section>

      <section className="panel-card panel-card--wide">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Форма отчета</span>
            <h3>Новый производственный отчет</h3>
          </div>
        </div>

        <form className="report-form" onSubmit={handleSubmit}>
          <label>
            <span>Подразделение</span>
            <input
              value={form.department}
              onChange={(event) => updateField("department", event.target.value)}
            />
          </label>
          <label>
            <span>Линия</span>
            <input
              value={form.production_line}
              onChange={(event) => updateField("production_line", event.target.value)}
            />
          </label>
          <label>
            <span>Дата</span>
            <input
              type="date"
              value={form.report_date}
              onChange={(event) => updateField("report_date", event.target.value)}
            />
          </label>
          <label>
            <span>Смена</span>
            <select value={form.shift} onChange={(event) => updateField("shift", event.target.value)}>
              <option>Дневная</option>
              <option>Вечерняя</option>
              <option>Ночная</option>
            </select>
          </label>
          <label>
            <span>Выпуск, кг</span>
            <input
              type="number"
              step="0.1"
              value={form.quantity_kg}
              onChange={(event) => updateField("quantity_kg", event.target.value)}
            />
          </label>
          <label>
            <span>Колбаса, шт.</span>
            <input
              type="number"
              min={0}
              step={1}
              value={form.sausage_units}
              onChange={(event) => updateField("sausage_units", event.target.value)}
            />
          </label>
          <label>
            <span>Потери, кг</span>
            <input
              type="number"
              step="0.1"
              value={form.waste_kg}
              onChange={(event) => updateField("waste_kg", event.target.value)}
            />
          </label>
          <label>
            <span>Простой, мин</span>
            <input
              type="number"
              value={form.downtime_minutes}
              onChange={(event) => updateField("downtime_minutes", event.target.value)}
            />
          </label>
          <label>
            <span>Качество, %</span>
            <input
              type="number"
              step="0.1"
              value={form.quality_score}
              onChange={(event) => updateField("quality_score", event.target.value)}
            />
          </label>
          <label className="report-form__full">
            <span>Замечания</span>
            <textarea
              rows={4}
              value={form.issues}
              onChange={(event) => updateField("issues", event.target.value)}
            />
          </label>
          {submitError && <div className="form-error report-form__full">{submitError}</div>}
          <div className="report-form__actions report-form__full">
            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Сохраняем…" : "Сохранить отчет"}
            </button>
          </div>
        </form>
      </section>

      <section className="panel-card panel-card--wide">
        <div className="section-heading">
          <div>
            <span className="eyebrow">История</span>
            <h3>Мои отчеты</h3>
          </div>
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Линия</th>
                <th>Смена</th>
                <th>Выпуск</th>
                <th>Колбаса</th>
                <th>Потери</th>
                <th>Качество</th>
                <th>Замечания</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>{formatDate(report.report_date)}</td>
                  <td>{report.production_line}</td>
                  <td>{report.shift}</td>
                  <td>{formatNumber(report.quantity_kg)} кг</td>
                  <td>{formatNumber(report.sausage_units)} шт.</td>
                  <td>{formatNumber(report.waste_kg)} кг</td>
                  <td>{formatNumber(report.quality_score)}%</td>
                  <td>{report.issues || "Без замечаний"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel-card panel-card--wide">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Оплата персонала</span>
            <h3>Моя зарплата и премии</h3>
            <p className="panel-card__lede">
              Сумма рассчитывается за месяц: базовая зарплата, 2 TJS за каждую колбасу и премия после подтверждения администратором.
            </p>
          </div>
        </div>

        <div className="expense-grid">
          {dashboard.salary_reports.map((salary) => (
            <article className="expense-card" key={salary.id}>
              <div className="expense-card__header">
                <strong>{salary.period_label}</strong>
                <StatusBadge status={salary.status} />
              </div>
              <p>{formatMoneyAmount(salary.total_due_tjs, "TJS")}</p>
              <span>
                {formatNumber(salary.sausage_units)} шт. x {formatMoneyAmount(salary.sausage_rate_tjs, "TJS")} ={" "}
                {formatMoneyAmount(salary.production_bonus_tjs, "TJS")}
              </span>
              <div className="expense-card__footer">
                <div>
                  <strong>Премия: {formatMoneyAmount(salary.premium_tjs, "TJS")}</strong>
                  <small>База: {formatMoneyAmount(salary.base_salary_tjs, "TJS")}</small>
                </div>
              </div>
              {salary.admin_comment ? <small>{salary.admin_comment}</small> : null}
            </article>
          ))}
        </div>
      </section>

      <section className="panel-card panel-card--wide">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Финансовый блок</span>
            <h3>Запрос аванса</h3>
            <p className="panel-card__lede">
              Отправьте сумму и обоснование: заявка появится у администратора как новая, пока он не откроет PDF.
            </p>
          </div>
        </div>

        <form className="report-form" onSubmit={handleAdvanceSubmit}>
          <label>
            <span>Сумма</span>
            <input
              type="number"
              min={1}
              step="0.01"
              value={advanceAmount}
              onChange={(event) => setAdvanceAmount(event.target.value)}
            />
          </label>
          <label>
            <span>Валюта</span>
            <select value={advanceCurrency} onChange={(event) => setAdvanceCurrency(event.target.value as AdvanceCurrency)}>
              <option value="TJS">TJS — таджикский сомони</option>
              <option value="USD">USD — доллар США</option>
              <option value="CNY">CNY — китайский юань</option>
            </select>
          </label>
          <label>
            <span>Отчетный период (необязательно)</span>
            <input
              placeholder="Например: Май 2026"
              value={advancePeriod}
              onChange={(event) => setAdvancePeriod(event.target.value)}
            />
          </label>
          <label className="report-form__full">
            <span>Назначение и комментарий</span>
            <textarea
              rows={4}
              value={advancePurpose}
              onChange={(event) => setAdvancePurpose(event.target.value)}
            />
          </label>
          {advanceError && <div className="form-error report-form__full">{advanceError}</div>}
          <div className="report-form__actions report-form__full">
            <button className="primary-button" type="submit" disabled={advanceSubmitting}>
              {advanceSubmitting ? "Отправляем…" : "Отправить запрос администратору"}
            </button>
          </div>
        </form>
      </section>

      <section className="panel-card panel-card--wide">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Финансовый блок</span>
            <h3>Мои авансовые отчеты</h3>
          </div>
        </div>

        <div className="expense-grid">
          {dashboard.expense_reports.map((report) => (
            <article className="expense-card" key={report.id}>
              <div className="expense-card__header">
                <strong>{report.reference_number}</strong>
                <StatusBadge status={report.status} />
              </div>
              <p>{report.period_label}</p>
              <span>{report.purpose}</span>
              <div className="expense-card__footer">
                <div>
                  <strong>
                    {report.status === "pending" && report.amount_approved === 0
                      ? "—"
                      : formatMoneyAmount(report.amount_approved, report.currency)}
                  </strong>
                  <small>Запрошено {formatMoneyAmount(report.amount_requested, report.currency)}</small>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
