import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Role } from "../../lib/types";
import { useAuth } from "./AuthContext";

type RequireAuthProps = {
  role: Role;
};

export default function RequireAuth({ role }: RequireAuthProps) {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated || !user) {
    return <Navigate to={`/${role}/login`} replace state={{ from: location }} />;
  }

  if (user.role !== role) {
    return <Navigate to={`/${user.role}/dashboard`} replace />;
  }

  return <Outlet />;
}
