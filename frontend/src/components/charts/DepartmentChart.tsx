import { DepartmentSummary } from "../../lib/types";
import { formatNumber } from "../../lib/formatters";

type DepartmentChartProps = {
  items: DepartmentSummary[];
};

export default function DepartmentChart({ items }: DepartmentChartProps) {
  const maxVolume = Math.max(...items.map((item) => item.total_volume_kg), 1);

  return (
    <div className="chart-list">
      {items.map((item) => (
        <div className="chart-row" key={item.department}>
          <div className="chart-row__header">
            <strong>{item.department}</strong>
            <span>{formatNumber(item.total_volume_kg)} кг</span>
          </div>
          <div className="chart-row__track">
            <div
              className="chart-row__bar"
              style={{ width: `${(item.total_volume_kg / maxVolume) * 100}%` }}
            />
          </div>
          <div className="chart-row__meta">
            <span>{item.reports_count} отчетов</span>
            <span>Качество {formatNumber(item.average_quality)}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}
