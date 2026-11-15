import { Navigate, Route, Routes } from "react-router-dom";
import PortalLayout from "./layouts/PortalLayout";
import PortalLoginPage from "./pages/PortalLoginPage";
import LandingPage from "./pages/LandingPage";
import NotFoundPage from "./pages/NotFoundPage";
import RequireAuth from "./features/auth/RequireAuth";
import StaffDashboardPage from "./features/staff/StaffDashboardPage";
import AdminDashboardPage from "./features/admin/AdminDashboardPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/staff/login" element={<PortalLoginPage role="staff" />} />
      <Route path="/admin/login" element={<PortalLoginPage role="admin" />} />

      <Route element={<RequireAuth role="staff" />}>
        <Route path="/staff" element={<PortalLayout role="staff" />}>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<StaffDashboardPage />} />
        </Route>
      </Route>

      <Route element={<RequireAuth role="admin" />}>
        <Route path="/admin" element={<PortalLayout role="admin" />}>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboardPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
