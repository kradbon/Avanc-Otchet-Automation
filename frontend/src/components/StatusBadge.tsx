import { ExpenseStatus } from "../lib/types";

type StatusBadgeProps = {
  status: ExpenseStatus | string;
};

const statusMap: Record<string, string> = {
  pending: "На согласовании",
  approved: "Подтвержден",
  paid: "Оплачен"
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${status}`}>
      {statusMap[status] ?? status}
    </span>
  );
}
