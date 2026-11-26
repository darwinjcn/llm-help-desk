import { useCallback, useEffect, useState, type FormEvent } from 'react';
import api, { type Categoria, type KbArticle } from '../api';
import Spinner from '../components/Spinner';

const CATEGORIAS: Categoria[] = ['hardware', 'software', 'red', 'accesos', 'otro'];

/** Base de conocimiento: listado, creación y reingesta de artículos. */
export default function KbPage() {
  const [articulos, setArticulos] = useState<KbArticle[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  // Formulario de nuevo artículo
  const [aTitulo, setATitulo] = useState('');
  const [aContenido, setAContenido] = useState('');
  const [aCategoria, setACategoria] = useState<Categoria>('software');
  const [aEtiquetas, setAEtiquetas] = useState('');
  const [creando, setCreando] = useState(false);
  const [errorForm, setErrorForm] = useState<string | null>(null);

  const [reingestandoId, setReingestandoId] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const resp = await api.get<{ items: KbArticle[] }>('/kb/articles');
      setArticulos(resp.data.items);
    } catch {
      setError('No se pudieron cargar los artículos.');
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const crearArticulo = async (e: FormEvent) => {
    e.preventDefault();
    setCreando(true);
    setErrorForm(null);
    try {
      const etiquetas = aEtiquetas
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      await api.post<KbArticle>('/kb/articles', {
        titulo: aTitulo,
        contenido: aContenido,
        categoria: aCategoria,
        etiquetas,
      });
      setATitulo('');
      setAContenido('');
      setACategoria('software');
      setAEtiquetas('');
      setMensaje('Artículo creado correctamente.');
      await cargar();
    } catch {
      setErrorForm('No se pudo crear el artículo.');
    } finally {
      setCreando(false);
    }
  };

  const reingestar = async (id: string) => {
    setReingestandoId(id);
    setError(null);
    setMensaje(null);
    try {
      await api.post(`/kb/articles/${id}/reingesta`);
      setMensaje('Reingesta completada: el artículo se indexó nuevamente.');
      await cargar();
    } catch {
      setError('No se pudo completar la reingesta.');
    } finally {
      setReingestandoId(null);
    }
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-800 mb-4">Base de Conocimiento</h1>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
          {error}
        </div>
      )}
      {mensaje && (
        <div className="mb-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm px-3 py-2">
          {mensaje}
        </div>
      )}

      {cargando ? (
        <Spinner className="py-16" tamano={28} />
      ) : articulos.length === 0 ? (
        <div className="card p-8 text-center text-slate-500 mb-6">
          No hay artículos todavía. Crea el primero con el formulario inferior.
        </div>
      ) : (
        <ul className="space-y-3 mb-8">
          {articulos.map((a) => (
            <li key={a.id} className="card p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <h2 className="font-semibold text-slate-800">{a.titulo}</h2>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Categoría: {a.categoria} · Versión: {a.version}
                  </p>
                  {a.etiquetas.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {a.etiquetas.map((et) => (
                        <span key={et} className="badge bg-slate-100 text-slate-600">
                          {et}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`badge ${
                      a.activo
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {a.activo ? 'Activo' : 'Inactivo'}
                  </span>
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={reingestandoId === a.id}
                    onClick={() => void reingestar(a.id)}
                  >
                    {reingestandoId === a.id ? (
                      <Spinner tamano={18} />
                    ) : (
                      'Reingestar'
                    )}
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Formulario de nuevo artículo */}
      <div className="card p-4 sm:p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Nuevo artículo</h2>
        {errorForm && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
            {errorForm}
          </div>
        )}
        <form onSubmit={crearArticulo} className="space-y-4">
          <div>
            <label className="label" htmlFor="k-titulo">Título</label>
            <input
              id="k-titulo"
              className="input"
              value={aTitulo}
              onChange={(e) => setATitulo(e.target.value)}
              required
              placeholder="Título del artículo"
            />
          </div>
          <div>
            <label className="label" htmlFor="k-contenido">Contenido</label>
            <textarea
              id="k-contenido"
              className="input min-h-[140px]"
              value={aContenido}
              onChange={(e) => setAContenido(e.target.value)}
              required
              placeholder="Contenido del artículo (solución, pasos, notas…)"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label" htmlFor="k-categoria">Categoría</label>
              <select
                id="k-categoria"
                className="input"
                value={aCategoria}
                onChange={(e) => setACategoria(e.target.value as Categoria)}
              >
                {CATEGORIAS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="k-etiquetas">Etiquetas (separadas por coma)</label>
              <input
                id="k-etiquetas"
                className="input"
                value={aEtiquetas}
                onChange={(e) => setAEtiquetas(e.target.value)}
                placeholder="vpn, windows, error-401"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" className="btn-primary" disabled={creando}>
              {creando ? <Spinner tamano={18} /> : 'Crear artículo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
