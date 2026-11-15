type MetricCardProps = {
  label: string;
  value: string;
  hint: string;
  tone?: "navy" | "gold" | "green";
};

export default function MetricCard({
  label,
  value,
  hint,
  tone = "navy"
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <span className="metric-card__label">{label}</span>
      <strong className="metric-card__value">{value}</strong>
      <span className="metric-card__hint">{hint}</span>
    </article>
  );
}
