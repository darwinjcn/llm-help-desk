import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import api, {
  type Rol,
  type User,
  clearToken,
  getToken,
  setToken,
} from '../api';

interface RegisterData {
  nombre: string;
  email: string;
  password: string;
  rol: Exclude<Rol, 'admin'>;
}

interface AuthContextShape {
  user: User | null;
  cargando: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: RegisterData) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextShape | null>(null);

interface AuthResponse {
  access_token: string;
  user: User;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [cargando, setCargando] = useState<boolean>(true);

  // Al montar, si hay token, recupera el perfil desde /auth/me
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setCargando(false);
      return;
    }
    api
      .get<User>('/auth/me')
      .then((resp) => setUser(resp.data))
      .catch(() => clearToken())
      .finally(() => setCargando(false));
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<User> => {
    const resp = await api.post<AuthResponse>('/auth/login', { email, password });
    setToken(resp.data.access_token);
    setUser(resp.data.user);
    return resp.data.user;
  }, []);

  const register = useCallback(async (data: RegisterData): Promise<User> => {
    const resp = await api.post<AuthResponse>('/auth/register', data);
    setToken(resp.data.access_token);
    setUser(resp.data.user);
    return resp.data.user;
  }, []);

  const logout = useCallback((): void => {
    clearToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, cargando, login, register, logout }),
    [user, cargando, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextShape {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return ctx;
}
