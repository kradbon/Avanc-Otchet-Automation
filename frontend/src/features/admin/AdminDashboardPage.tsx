import { useDeferredValue, useEffect, useState } from "react";
import { api } from "../../api/client";
import ApiUnavailableState from "../../components/ApiUnavailableState";
import DepartmentChart from "../../components/charts/DepartmentChart";
import MetricCard from "../../components/MetricCard";
import PdfPreviewPanel, { PdfPreviewDocument } from "../../components/PdfPreviewPanel";
import StatusBadge from "../../components/StatusBadge";
import {
  formatDate,
  formatDateTime,
  formatMoneyAmount,
  formatNumber
} from "../../lib/formatters";
import { AdminOverview, ExpenseReport, PaymentStatus, ProductionReport, SalaryReport } from "../../lib/types";
import { useAuth } from "../auth/AuthContext";

export default function AdminDashboardPage() {
  const { token } = useAuth();
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [reports, setReports] = useState<ProductionReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query.trim().toLowerCase());
  const [pdfDocument, setPdfDocument] = useState<PdfPreviewDocument | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [salaryEdits, setSalaryEdits] = useState<
    Record<number, { base_salary_tjs: string; premium_tjs: string; status: PaymentStatus; admin_comment: string }>
  >({});
  const [salarySavingId, setSalarySavingId] = useState<number | null>(null);

  const loadData = async () => {
    if (!token) {
      return;
    }

    const [overviewData, reportsData] = await Promise.all([
      api.get<AdminOverview>("/admin/overview", token),
      api.get<ProductionReport[]>("/admin/reports", token)
    ]);
    setOverview(overviewData);
    setReports(reportsData);
  };

  useEffect(() => {
    if (!token) {
      return;
    }

    void (async () => {
      try {
        await loadData();
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить админ-панель.");
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  useEffect(() => {
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [pdfUrl]);

  useEffect(() => {
    if (!overview) {
      return;
    }

    setSalaryEdits((current) => {
      const next = { ...current };
      for (const salary of overview.salary_reports) {
        if (!next[salary.id]) {
          next[salary.id] = {
            base_salary_tjs: String(salary.base_salary_tjs),
            premium_tjs: String(salary.premium_tjs),
            status: salary.status,
            admin_comment: salary.admin_comment ?? ""
          };
        }
      }
      return next;
    });
  }, [overview]);

  const filteredReports = !deferredQuery
    ? reports
    : reports.filter((report) =>
        [
          report.employee_name,
          report.department,
          report.production_line,
          report.shift,
          report.issues ?? ""
        ]
          .join(" ")
          .toLowerCase()
          .includes(deferredQuery)
      );

  const filteredExpenseReports = !(overview?.expense_reports && deferredQuery)
    ? overview?.expense_reports ?? []
    : overview.expense_reports.filter((report) =>
        [report.reference_number, report.employee_name, report.period_label, report.purpose, report.currency]
          .join(" ")
          .toLowerCase()
          .includes(deferredQuery)
      );

  const filteredSalaryReports = !(overview?.salary_reports && deferredQuery)
    ? overview?.salary_reports ?? []
    : overview.salary_reports.filter((report) =>
        [report.employee_name, report.period_label, report.status, report.admin_comment ?? ""]
          .join(" ")
          .toLowerCase()
          .includes(deferredQuery)
      );

  const closePreview = () => {
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
    }
    setPdfUrl(null);
    setPdfDocument(null);
    setPdfLoading(false);
  };

  const openExpensePreview = async (report: ExpenseReport) => {
    if (!token) {
      return;
    }

    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }

    setPdfDocument({ kind: "expense", report });
    setPdfLoading(true);

    try {
      const blob = await api.pdf(`/admin/expense-reports/${report.id}/pdf`, token);
      setPdfUrl(URL.createObjectURL(blob));
      await loadData();
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : "Не удалось открыть PDF.");
    } finally {
      setPdfLoading(false);
    }
  };

  const openProductionPreview = async (report: ProductionReport) => {
    if (!token) {
      return;
    }

    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }

    setPdfDocument({ kind: "production", report });
    setPdfLoading(true);

    try {
      const blob = await api.pdf(`/admin/reports/${report.id}/pdf`, token);
      setPdfUrl(URL.createObjectURL(blob));
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : "Не удалось открыть PDF.");
    } finally {
      setPdfLoading(false);
    }
  };

  const updateSalaryEdit = (
    report: SalaryReport,
    field: "base_salary_tjs" | "premium_tjs" | "status" | "admin_comment",
    value: string
  ) => {
    setSalaryEdits((current) => ({
      ...current,
      [report.id]: {
        base_salary_tjs: current[report.id]?.base_salary_tjs ?? String(report.base_salary_tjs),
        premium_tjs: current[report.id]?.premium_tjs ?? String(report.premium_tjs),
        status: current[report.id]?.status ?? report.status,
        admin_comment: current[report.id]?.admin_comment ?? report.admin_comment ?? "",
        [field]: field === "status" ? (value as PaymentStatus) : value
      }
    }));
  };

  const saveSalaryApproval = async (report: SalaryReport) => {
    if (!token) {
      return;
    }

    const edit = salaryEdits[report.id];
    if (!edit) {
      return;
    }

    setSalarySavingId(report.id);
    try {
      await api.post<SalaryReport>(
        `/admin/salary-reports/${report.id}/approval`,
        {
          base_salary_tjs: Number(edit.base_salary_tjs),
          premium_tjs: Number(edit.premium_tjs),
          status: edit.status,
          admin_comment: edit.admin_comment.trim() || null
        },
        token
      );
      await loadData();
    } catch (salaryError) {
      setError(salaryError instanceof Error ? salaryError.message : "Не удалось сохранить зарплату.");
    } finally {
      setSalarySavingId(null);
    }
  };

  const downloadSelectedPdf = async () => {
    if (!token || !pdfDocument) {
      return;
    }

    try {
      if (pdfDocument.kind === "expense") {
        const blob = await api.pdf(
          `/admin/expense-reports/${pdfDocument.report.id}/pdf?download=true`,
          token
        );
        const objectUrl = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = objectUrl;
        anchor.download = `${pdfDocument.report.reference_number}.pdf`;
        anchor.click();
        URL.revokeObjectURL(objectUrl);
      } else {
        const blob = await api.pdf(`/admin/reports/${pdfDocument.report.id}/pdf?download=true`, token);
        const objectUrl = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = objectUrl;
        anchor.download = `production-report-${pdfDocument.report.id}.pdf`;
        anchor.click();
        URL.revokeObjectURL(objectUrl);
      }
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : "Не удалось скачать PDF.");
      return;
    }
    await loadData();
  };

  if (loading) {
    return <div className="empty-state">Загружаем административную панель…</div>;
  }

  if (error || !overview) {
    return <ApiUnavailableState message={error || "Сводные данные недоступны."} />;
  }

  return (
    <>
      <div className="dashboard-grid">
        <section className="hero-panel hero-panel--admin">
          <div>
            <span className="eyebrow">Сводный контур</span>
            <h3>Контроль отчетности и авансовых документов</h3>
            <p>
              Единая витрина для всех подразделений: производственные данные, контроль качества
              и авансовые формы в PDF.
            </p>
          </div>
          <label className="search-field">
            <span>Поиск по данным</span>
            <input
              placeholder="Сотрудник, цех, линия, номер документа"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
        </section>

        <section className="metrics-grid">
          <MetricCard
            label="Активные сотрудники"
            value={String(overview.stats.active_staff)}
            hint="Пользователи с доступом к staff-порталу"
          />
          <MetricCard
            label="Новые авансовые запросы"
            value={String(overview.stats.unread_expense_count)}
            hint="Еще не открыты в PDF администратором"
            tone="gold"
          />
          <MetricCard
            label="Зарплаты на согласовании"
            value={String(overview.stats.pending_salary_count)}
            hint="Месячные выплаты, ожидающие решения администратора"
            tone="gold"
          />
          <MetricCard
            label="К выплате персоналу"
            value={formatMoneyAmount(overview.stats.payroll_due_tjs, "TJS")}
            hint="Зарплата и премии со статусом pending/approved"
            tone="green"
          />
          <MetricCard
            label="Всего отчетов"
            value={String(overview.stats.reports_total)}
            hint="Включая все подразделения"
          />
          <MetricCard
            label="Выпуск продукции"
            value={`${formatNumber(overview.stats.total_output_kg)} кг`}
            hint="Суммарный объем"
            tone="green"
          />
          <MetricCard
            label="Подтвержденные авансы"
            value={
              overview.stats.approved_expense_buckets.length === 0
                ? "—"
                : overview.stats.approved_expense_buckets
                    .map((b) => formatMoneyAmount(b.total, b.currency))
                    .join(" · ")
            }
            hint="Суммы по валютам (подтверждено и оплачено)"
            tone="navy"
          />
        </section>

        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Подразделения</span>
              <h3>Распределение выпуска</h3>
            </div>
          </div>
          <DepartmentChart items={overview.department_breakdown} />
        </section>

        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Финансы</span>
              <h3>Авансовые отчеты</h3>
            </div>
          </div>
          <div className="expense-grid">
            {filteredExpenseReports.map((report) => (
              <article
                className={`expense-card${report.admin_read ? "" : " expense-card--unread"}`}
                key={report.id}
              >
                <div className="expense-card__header">
                  <div className="expense-card__title">
                    <strong>{report.reference_number}</strong>
                    {!report.admin_read ? <span className="unread-pill">Новый</span> : null}
                  </div>
                  <StatusBadge status={report.status} />
                </div>
                <p>{report.employee_name}</p>
                <span>{report.purpose}</span>
                <div className="expense-card__footer">
                  <div>
                    <strong>
                      {report.status === "pending" && report.amount_approved === 0
                        ? "—"
                        : formatMoneyAmount(report.amount_approved, report.currency)}
                    </strong>
                    <small>
                      Запрошено {formatMoneyAmount(report.amount_requested, report.currency)} ·{" "}
                      {formatDateTime(report.generated_at)}
                    </small>
                  </div>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => void openExpensePreview(report)}
                  >
                    Превью PDF
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="panel-card panel-card--wide">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Оплата персонала</span>
              <h3>Зарплаты, колбасный бонус и премии</h3>
              <p className="panel-card__lede">
                Администратор задает базовую зарплату, премию лучшему сотруднику месяца и финальный статус выплаты.
              </p>
            </div>
          </div>

          <div className="expense-grid">
            {filteredSalaryReports.map((salary) => {
              const edit = salaryEdits[salary.id] ?? {
                base_salary_tjs: String(salary.base_salary_tjs),
                premium_tjs: String(salary.premium_tjs),
                status: salary.status,
                admin_comment: salary.admin_comment ?? ""
              };
              const calculatedTotal =
                Number(edit.base_salary_tjs || 0) +
                salary.production_bonus_tjs +
                Number(edit.premium_tjs || 0);

              return (
                <article className="expense-card" key={salary.id}>
                  <div className="expense-card__header">
                    <div className="expense-card__title">
                      <strong>{salary.employee_name}</strong>
                      <span className="unread-pill">{salary.period_label}</span>
                    </div>
                    <StatusBadge status={edit.status} />
                  </div>
                  <p>{formatMoneyAmount(calculatedTotal, "TJS")}</p>
                  <span>
                    {formatNumber(salary.sausage_units)} шт. x {formatMoneyAmount(salary.sausage_rate_tjs, "TJS")} ={" "}
                    {formatMoneyAmount(salary.production_bonus_tjs, "TJS")}
                  </span>

                  <div className="salary-edit-grid">
                    <label>
                      <span>Базовая зарплата, TJS</span>
                      <input
                        type="number"
                        min={0}
                        step="0.01"
                        value={edit.base_salary_tjs}
                        onChange={(event) => updateSalaryEdit(salary, "base_salary_tjs", event.target.value)}
                      />
                    </label>
                    <label>
                      <span>Премия, TJS</span>
                      <input
                        type="number"
                        min={0}
                        step="0.01"
                        value={edit.premium_tjs}
                        onChange={(event) => updateSalaryEdit(salary, "premium_tjs", event.target.value)}
                      />
                    </label>
                    <label>
                      <span>Статус</span>
                      <select
                        value={edit.status}
                        onChange={(event) => updateSalaryEdit(salary, "status", event.target.value)}
                      >
                        <option value="pending">На согласовании</option>
                        <option value="approved">Подтвержден</option>
                        <option value="paid">Оплачен</option>
                      </select>
                    </label>
                    <label>
                      <span>Комментарий администратора</span>
                      <input
                        value={edit.admin_comment}
                        onChange={(event) => updateSalaryEdit(salary, "admin_comment", event.target.value)}
                      />
                    </label>
                  </div>

                  <div className="expense-card__footer">
                    <small>Обновлено {formatDateTime(salary.updated_at)}</small>
                    <button
                      className="secondary-button"
                      type="button"
                      disabled={salarySavingId === salary.id}
                      onClick={() => void saveSalaryApproval(salary)}
                    >
                      {salarySavingId === salary.id ? "Сохраняем..." : "Подтвердить"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="panel-card panel-card--wide">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Журнал отчетов</span>
              <h3>Все производственные отчеты</h3>
            </div>
            <button
              type="button"
              className="secondary-button"
              disabled={filteredReports.length === 0}
              title="Открывает превью первого отчета в списке (с учетом поиска). Для любой строки используйте кнопку в таблице."
              onClick={() => {
                const first = filteredReports[0];
                if (first) {
                  void openProductionPreview(first);
                }
              }}
            >
              Превью PDF
            </button>
          </div>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Сотрудник</th>
                  <th>Подразделение</th>
                  <th>Линия</th>
                  <th>Дата</th>
                  <th>Смена</th>
                  <th>Выпуск</th>
                  <th>Качество</th>
                  <th className="data-table__narrow">Превью</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((report) => (
                  <tr key={report.id}>
                    <td>{report.employee_name}</td>
                    <td>{report.department}</td>
                    <td>{report.production_line}</td>
                    <td>{formatDate(report.report_date)}</td>
                    <td>{report.shift}</td>
                    <td>{formatNumber(report.quantity_kg)} кг</td>
                    <td>{formatNumber(report.quality_score)}%</td>
                    <td className="data-table__narrow">
                      <button
                        type="button"
                        className="secondary-button secondary-button--compact"
                        onClick={() => void openProductionPreview(report)}
                      >
                        Превью PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <PdfPreviewPanel
        document={pdfDocument}
        pdfUrl={pdfUrl}
        loading={pdfLoading}
        onClose={closePreview}
        onDownload={() => void downloadSelectedPdf()}
      />
    </>
  );
}
