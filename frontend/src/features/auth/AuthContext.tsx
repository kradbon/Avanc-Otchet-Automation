import {
  createContext,
  PropsWithChildren,
  useContext,
  useEffect,
  useState
} from "react";
import { api } from "../../api/client";
import { AuthResponse, Role, UserProfile } from "../../lib/types";

type LoginPayload = {
  login: string;
  password: string;
  expectedRole: Role;
};

type AuthState = {
  token: string | null;
  user: UserProfile | null;
};

type AuthContextValue = AuthState & {
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
};

const STORAGE_KEY = "avanc-session";

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredState(): AuthState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { token: null, user: null };
  }

  try {
    const state = JSON.parse(raw) as AuthState;
    if (state.user && typeof state.user.username !== "string") {
      return { token: null, user: null };
    }
    return state;
  } catch {
    return { token: null, user: null };
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<AuthState>(() => readStoredState());

  useEffect(() => {
    if (state.token && state.user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      return;
    }

    localStorage.removeItem(STORAGE_KEY);
  }, [state]);

  const login = async ({ login, password, expectedRole }: LoginPayload) => {
    const response = await api.post<AuthResponse>("/auth/login", { login, password });
    if (response.user.role !== expectedRole) {
      throw new Error("Учетная запись относится к другому порталу.");
    }

    setState({ token: response.access_token, user: response.user });
  };

  const logout = () => {
    setState({ token: null, user: null });
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        isAuthenticated: Boolean(state.token && state.user)
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
