import {
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useNavigate,
} from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from './context/AuthContext';
import Spinner from './components/Spinner';
import LoginPage from './pages/LoginPage';
import TicketsPage from './pages/TicketsPage';
import TicketDetailPage from './pages/TicketDetailPage';
import KbPage from './pages/KbPage';
import DashboardPage from './pages/DashboardPage';
import type { Rol } from './api';

/** Redirige a /login si no hay sesión. */
function RutaProtegida() {
  const { user, cargando } = useAuth();
  if (cargando) {
    return <Spinner className="min-h-screen" tamano={32} />;
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

/** Solo permite acceso a roles con permiso (para vistas de agente/admin). */
function RequiereRol({ roles, children }: { roles: Rol[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.rol)) return <Navigate to="/tickets" replace />;
  return <>{children}</>;
}

interface NavbarProps {
  onLogout: () => void;
}

/** Barra superior con logo, links según rol y usuario. */
function Navbar({ onLogout }: NavbarProps) {
  const { user } = useAuth();
  if (!user) return null;

  const puedeVerAgente = user.rol === 'agente' || user.rol === 'admin';

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-lg text-sm font-medium min-h-[44px] inline-flex items-center ${
      isActive ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'
    }`;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 flex items-center gap-2 sm:gap-4 h-16 overflow-x-auto">
        <NavLink to="/tickets" className="font-bold text-slate-800 whitespace-nowrap">
          LLM Help Desk
        </NavLink>
        <nav className="flex items-center gap-1">
          <NavLink to="/tickets" className={linkClass}>
            Tickets
          </NavLink>
          {puedeVerAgente && (
            <NavLink to="/kb" className={linkClass}>
              Base de Conocimiento
            </NavLink>
          )}
          {puedeVerAgente && (
            <NavLink to="/dashboard" className={linkClass}>
              Dashboard IA
            </NavLink>
          )}
        </nav>
        <div className="ml-auto flex items-center gap-2 whitespace-nowrap">
          <span className="text-sm text-slate-600 hidden sm:inline">
            {user.nombre} <span className="text-slate-400">({user.rol})</span>
          </span>
          <button type="button" onClick={onLogout} className="btn-secondary !min-h-[44px]">
            Salir
          </button>
        </div>
      </div>
    </header>
  );
}

/** Layout principal con navbar y footer fijo. */
function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar onLogout={handleLogout} />
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
      <footer className="bg-white border-t border-slate-200 py-3 text-center text-sm text-slate-500">
        LLM Help Desk — IA 100% local
      </footer>
    </div>
  );
}

/** Router con rutas públicas y protegidas. */
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RutaProtegida />}>
        <Route element={<Layout />}>
          <Route path="/tickets" element={<TicketsPage />} />
          <Route path="/tickets/:id" element={<TicketDetailPage />} />
          <Route
            path="/kb"
            element={
              <RequiereRol roles={['agente', 'admin']}>
                <KbPage />
              </RequiereRol>
            }
          />
          <Route
            path="/dashboard"
            element={
              <RequiereRol roles={['agente', 'admin']}>
                <DashboardPage />
              </RequiereRol>
            }
          />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/tickets" replace />} />
    </Routes>
  );
}
