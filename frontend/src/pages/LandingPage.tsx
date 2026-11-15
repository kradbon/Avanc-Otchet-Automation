import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <section className="hero">
        <div className="hero__copy">
          <span className="eyebrow">Классический нормоконтроль</span>
          <h1>Единая система отчетности для производственных и авансовых процессов</h1>
          <p>
            Платформа объединяет сотрудников цехов и административный контур в одном
            аккуратном рабочем пространстве: от сменных отчетов до PDF-документов для
            финансового контроля.
          </p>

          <div className="hero__stats">
            <div className="hero-stat">
              <strong>2 портала</strong>
              <span>раздельный доступ для сотрудников и администраторов</span>
            </div>
            <div className="hero-stat">
              <strong>PDF-контур</strong>
              <span>превью и скачивание авансовых отчетов прямо из браузера</span>
            </div>
          </div>
        </div>

        <div className="hero__summary">
          <div className="hero__summary-top">
            <span className="eyebrow">Рабочий контур</span>
            <div className="hero__summary-grid">
              <div className="hero__summary-item">
                <strong>Staff</strong>
                <span>Сменные отчеты, личный кабинет, персональные документы.</span>
              </div>
              <div className="hero__summary-item">
                <strong>Admin</strong>
                <span>Сводка по подразделениям, контроль данных и PDF-превью.</span>
              </div>
            </div>
          </div>

          <div className="hero__summary-bottom">
            <h2>Выберите портал для входа</h2>
            <p>
              Каждый сценарий оформлен отдельно: сотрудники работают со своими сменами,
              администраторы контролируют всю картину целиком.
            </p>
          </div>
        </div>
      </section>

      <section className="portal-entry-grid">
        <article className="entry-card entry-card--staff">
          <span className="entry-card__code">Portal 01</span>
          <h3>Вход сотрудника</h3>
          <p>
            Личный кабинет для мастеров, технологов и сотрудников производственных
            участков.
          </p>
          <ul className="entry-card__list">
            <li>Создание сменных отчетов</li>
            <li>История собственных записей</li>
            <li>Персональные авансовые документы</li>
          </ul>
          <Link className="primary-button" to="/staff/login">
            Войти сотруднику
          </Link>
        </article>

        <article className="entry-card entry-card--admin">
          <span className="entry-card__code">Portal 02</span>
          <h3>Вход администратора</h3>
          <p>
            Административная витрина для контроля отчетности, подразделений и PDF-форм.
          </p>
          <ul className="entry-card__list">
            <li>Сводка по всем подразделениям</li>
            <li>Контроль качества и производственных данных</li>
            <li>Превью и выгрузка авансовых PDF</li>
          </ul>
          <Link className="secondary-button" to="/admin/login">
            Войти администратору
          </Link>
        </article>
      </section>

      <section className="feature-grid">
        <article className="feature-card">
          <h3>Личный кабинет сотрудника</h3>
          <p>Ввод производственных отчетов, история смен и контроль персональных показателей.</p>
        </article>
        <article className="feature-card">
          <h3>Панель администратора</h3>
          <p>Все отчеты в одной витрине, разрезы по подразделениям и финансовый контроль.</p>
        </article>
        <article className="feature-card">
          <h3>PDF-пакет документов</h3>
          <p>Готовые авансовые формы с превью прямо в браузере и скачиванием одним действием.</p>
        </article>
      </section>
    </div>
  );
}
