import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="not-found">
      <span className="eyebrow">404</span>
      <h1>Страница не найдена</h1>
      <p>Проверьте адрес или вернитесь в один из рабочих порталов системы.</p>
      <Link className="primary-button" to="/">
        На главную
      </Link>
    </div>
  );
}
