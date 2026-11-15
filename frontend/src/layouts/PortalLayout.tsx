import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Role } from "../lib/types";
import { useAuth } from "../features/auth/AuthContext";

type PortalLayoutProps = {
  role: Role;
};

const portalConfig = {
  staff: {
    title: "Кабинет сотрудника",
    subtitle: "Производственные отчеты и персональный контроль по сменам."
  },
  admin: {
    title: "Админ",
    subtitle: "Сводные показатели, контроль отчетности и авансовые документы."
  }
} satisfies Record<Role, { title: string; subtitle: string }>;

export default function PortalLayout({ role }: PortalLayoutProps) {
  const { user, logout } = useAuth();
  const portal = portalConfig[role];
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate(`/${role}/login`, { replace: true });
  };

  const handleSwitchAccount = () => {
    logout();
    navigate("/", { replace: true });
  };

  return (
    <div className={`portal-shell portal-shell--${role}`}>
      <aside className="portal-sidebar">
        <div className="portal-sidebar__top">
          <span className="eyebrow">Avanc Automation</span>
          <h1>{portal.title}</h1>
          <p>{portal.subtitle}</p>
        </div>

        <div className="portal-sidebar__stack">
          <nav className="portal-nav">
            <NavLink to={`/${role}/dashboard`}>Главная панель</NavLink>
          </nav>

          <div className="portal-account-card">
            <span className="eyebrow">Аккаунт</span>
            <strong>{user?.full_name}</strong>
            <span>{user?.position}</span>
            <span>{user?.department}</span>
            <small>@{user?.username}</small>
            <button
              className="secondary-button portal-account-card__button"
              type="button"
              onClick={handleSwitchAccount}
            >
              Сменить аккаунт
            </button>
          </div>
        </div>
      </aside>

      <div className="portal-main">
        <header className="portal-header">
          <div>
            <span className="eyebrow">{role === "staff" ? "Staff portal" : "Admin portal"}</span>
            <h2>{portal.title}</h2>
          </div>
          <div className="portal-header__actions">
            <button className="secondary-button" type="button" onClick={handleSwitchAccount}>
              Сменить аккаунт
            </button>
            <button className="ghost-button" type="button" onClick={handleLogout}>
              Выйти
            </button>
          </div>
        </header>
        <main className="portal-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
