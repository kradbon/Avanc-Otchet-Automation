import { ExpenseReport, ProductionReport } from "../lib/types";
import { formatDate, formatDateTime, formatMoneyAmount, formatNumber } from "../lib/formatters";
import StatusBadge from "./StatusBadge";

export type PdfPreviewDocument =
  | { kind: "expense"; report: ExpenseReport }
  | { kind: "production"; report: ProductionReport };

type PdfPreviewPanelProps = {
  document: PdfPreviewDocument | null;
  pdfUrl: string | null;
  loading: boolean;
  onClose: () => void;
  onDownload: () => void;
};

export default function PdfPreviewPanel({
  document,
  pdfUrl,
  loading,
  onClose,
  onDownload
}: PdfPreviewPanelProps) {
  if (!document) {
    return null;
  }

  const iframeTitle =
    document.kind === "expense"
      ? document.report.reference_number
      : `production-${document.report.id}`;

  return (
    <div className="pdf-panel-backdrop" onClick={onClose}>
      <aside className="pdf-panel" onClick={(event) => event.stopPropagation()}>
        <section className="pdf-panel__sidebar">
          <div className="pdf-panel__header">
            <div>
              <span className="eyebrow">PDF-превью</span>
              {document.kind === "expense" ? (
                <>
                  <h3>{document.report.reference_number}</h3>
                  <p>{document.report.employee_name}</p>
                </>
              ) : (
                <>
                  <h3>Производственный отчет №{document.report.id}</h3>
                  <p>{document.report.employee_name}</p>
                </>
              )}
            </div>
            <button className="ghost-button" type="button" onClick={onClose}>
              Закрыть
            </button>
          </div>

          {document.kind === "expense" ? (
            <>
              <div className="pdf-panel__summary">
                <div>
                  <span>Период</span>
                  <strong>{document.report.period_label}</strong>
                </div>
                <div>
                  <span>Валюта</span>
                  <strong>{document.report.currency}</strong>
                </div>
                <div>
                  <span>Запрошено</span>
                  <strong>
                    {formatMoneyAmount(document.report.amount_requested, document.report.currency)}
                  </strong>
                </div>
                <div>
                  <span>Статус</span>
                  <StatusBadge status={document.report.status} />
                </div>
                <div>
                  <span>Подтверждено</span>
                  <strong>{formatMoneyAmount(document.report.amount_approved, document.report.currency)}</strong>
                </div>
                <div>
                  <span>Сформирован</span>
                  <strong>{formatDateTime(document.report.generated_at)}</strong>
                </div>
              </div>
              <p className="pdf-panel__purpose">{document.report.purpose}</p>
            </>
          ) : (
            <>
              <div className="pdf-panel__summary">
                <div>
                  <span>Подразделение</span>
                  <strong>{document.report.department}</strong>
                </div>
                <div>
                  <span>Линия</span>
                  <strong>{document.report.production_line}</strong>
                </div>
                <div>
                  <span>Дата</span>
                  <strong>{formatDate(document.report.report_date)}</strong>
                </div>
                <div>
                  <span>Смена</span>
                  <strong>{document.report.shift}</strong>
                </div>
                <div>
                  <span>Выпуск</span>
                  <strong>{formatNumber(document.report.quantity_kg)} кг</strong>
                </div>
                <div>
                  <span>Качество</span>
                  <strong>{formatNumber(document.report.quality_score)}%</strong>
                </div>
                <div>
                  <span>Отходы</span>
                  <strong>{formatNumber(document.report.waste_kg)} кг</strong>
                </div>
                <div>
                  <span>Простой</span>
                  <strong>{document.report.downtime_minutes} мин</strong>
                </div>
              </div>
              {document.report.issues ? (
                <p className="pdf-panel__purpose">{document.report.issues}</p>
              ) : null}
            </>
          )}

          <div className="pdf-panel__actions">
            <button className="primary-button" type="button" onClick={onDownload}>
              Скачать PDF
            </button>
            {pdfUrl && (
              <a className="secondary-button" href={pdfUrl} target="_blank" rel="noreferrer">
                Открыть отдельно
              </a>
            )}
          </div>
        </section>

        <section className="pdf-panel__viewer">
          {loading && <div className="empty-state">Подготавливаем превью документа…</div>}
          {!loading && pdfUrl && (
            <div className="pdf-panel__frame">
              <iframe src={pdfUrl} title={iframeTitle} />
            </div>
          )}
        </section>
      </aside>
    </div>
  );
}
