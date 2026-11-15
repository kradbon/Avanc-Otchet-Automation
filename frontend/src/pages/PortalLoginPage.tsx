import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Role } from "../lib/types";
import { useAuth } from "../features/auth/AuthContext";

type PortalLoginPageProps = {
  role: Role;
};

const loginContent = {
  staff: {
    title: "Вход для сотрудников",
    subtitle: "Персональный кабинет для ежедневной производственной отчетности.",
    login: "staff1",
    password: "staff1"
  },
  admin: {
    title: "Вход для администраторов",
    subtitle: "Контроль сводных данных, отчетов и авансовых документов.",
    login: "admin",
    password: "admin"
  }
} satisfies Record<Role, { title: string; subtitle: string; login: string; password: string }>;

export default function PortalLoginPage({ role }: PortalLoginPageProps) {
  const content = loginContent[role];
  const navigate = useNavigate();
  const { login, user } = useAuth();
  const [loginValue, setLoginValue] = useState(content.login);
  const [password, setPassword] = useState(content.password);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.role === role) {
      navigate(`/${role}/dashboard`, { replace: true });
    }
  }, [navigate, role, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login({ login: loginValue, password, expectedRole: role });
      navigate(`/${role}/dashboard`, { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Не удалось выполнить вход.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`login-page login-page--${role}`}>
      <section className="login-card">
        <div className="login-card__intro">
          <span className="eyebrow">{role === "staff" ? "Staff portal" : "Admin portal"}</span>
          <h1>{content.title}</h1>
          <p>{content.subtitle}</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            <span>Логин</span>
            <input
              autoComplete="username"
              type="text"
              value={loginValue}
              onChange={(event) => setLoginValue(event.target.value)}
            />
          </label>
          <label>
            <span>Пароль</span>
            <input
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Выполняем вход…" : "Открыть кабинет"}
          </button>
        </form>

        <div className="login-card__footer">
          <span>Демо-доступ уже подставлен в форму.</span>
          <Link to={role === "staff" ? "/admin/login" : "/staff/login"}>
            {role === "staff" ? "Перейти к админам" : "Перейти к сотрудникам"}
          </Link>
        </div>
      </section>
    </div>
  );
}
