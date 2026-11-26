import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Spinner from '../components/Spinner';

type Tab = 'login' | 'register';

/** Página de autenticación: tabs de inicio de sesión y registro. */
export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [tab, setTab] = useState<Tab>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nombre, setNombre] = useState('');
  const [rol, setRol] = useState<'cliente' | 'agente'>('cliente');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      if (tab === 'login') {
        await login(email, password);
      } else {
        await register({ nombre, email, password, rol });
      }
      navigate('/tickets');
    } catch {
      setError(
        tab === 'login'
          ? 'No se pudo iniciar sesión. Verifica tus credenciales.'
          : 'No se pudo completar el registro. El email puede estar en uso.',
      );
    } finally {
      setEnviando(false);
    }
  };

  const tabClass = (activo: boolean) =>
    `flex-1 py-3 text-sm font-medium rounded-lg transition-colors ${
      activo ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'
    }`;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-slate-50">
      <div className="card w-full max-w-md p-6 sm:p-8">
        <h1 className="text-xl font-bold text-slate-800 text-center mb-1">
          LLM Help Desk
        </h1>
        <p className="text-sm text-slate-500 text-center mb-6">IA 100% local</p>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 p-1 rounded-lg mb-6">
          <button
            type="button"
            className={tabClass(tab === 'login')}
            onClick={() => setTab('login')}
          >
            Iniciar sesión
          </button>
          <button
            type="button"
            className={tabClass(tab === 'register')}
            onClick={() => setTab('register')}
          >
            Registrarse
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
            {error}
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          {tab === 'register' && (
            <div>
              <label className="label" htmlFor="nombre">
                Nombre
              </label>
              <input
                id="nombre"
                className="input"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                required
                placeholder="Tu nombre completo"
              />
            </div>
          )}
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="tu@correo.com"
            />
          </div>
          <div>
            <label className="label" htmlFor="password">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              placeholder="Mínimo 6 caracteres"
            />
          </div>
          {tab === 'register' && (
            <div>
              <label className="label" htmlFor="rol">
                Rol
              </label>
              <select
                id="rol"
                className="input"
                value={rol}
                onChange={(e) => setRol(e.target.value as 'cliente' | 'agente')}
              >
                <option value="cliente">Cliente</option>
                <option value="agente">Agente</option>
              </select>
            </div>
          )}
          <button type="submit" className="btn-primary w-full" disabled={enviando}>
            {enviando ? (
              <Spinner tamano={18} />
            ) : tab === 'login' ? (
              'Iniciar sesión'
            ) : (
              'Crear cuenta'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
