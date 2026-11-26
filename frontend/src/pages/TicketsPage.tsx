import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import api, { type Categoria, type EstadoTicket, type Prioridad, type Ticket } from '../api';
import { BadgeEstado, BadgePrioridad, BadgeEtiqueta } from '../components/Badge';
import Modal from '../components/Modal';
import Spinner from '../components/Spinner';

interface ListaTickets {
  items: Ticket[];
  total: number;
}

const ESTADOS: EstadoTicket[] = [
  'nuevo',
  'en_triage',
  'abierto',
  'en_resolucion',
  'resuelto',
  'cerrado',
];
const CATEGORIAS: Categoria[] = ['hardware', 'software', 'red', 'accesos', 'otro'];
const PRIORIDADES: Prioridad[] = ['baja', 'media', 'alta', 'critica'];

const TEXTO_ESTADO: Record<EstadoTicket, string> = {
  nuevo: 'Nuevo',
  en_triage: 'En triage',
  abierto: 'Abierto',
  en_resolucion: 'En resolución',
  resuelto: 'Resuelto',
  cerrado: 'Cerrado',
};
const TEXTO_CATEGORIA: Record<Categoria, string> = {
  hardware: 'Hardware',
  software: 'Software',
  red: 'Red',
  accesos: 'Accesos',
  otro: 'Otro',
};
const TEXTO_PRIORIDAD: Record<Prioridad, string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
  critica: 'Crítica',
};

/** Página de listado de tickets con filtros y creación. */
export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [fEstado, setFEstado] = useState<string>('');
  const [fCategoria, setFCategoria] = useState<string>('');
  const [fPrioridad, setFPrioridad] = useState<string>('');

  // Modal de nuevo ticket
  const [modalAbierto, setModalAbierto] = useState(false);
  const [nTitulo, setNTitulo] = useState('');
  const [nDescripcion, setNDescripcion] = useState('');
  const [nServicio, setNServicio] = useState('');
  const [creando, setCreando] = useState(false);
  const [errorModal, setErrorModal] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (fEstado) params.estado = fEstado;
      if (fCategoria) params.categoria = fCategoria;
      if (fPrioridad) params.prioridad = fPrioridad;
      const resp = await api.get<ListaTickets>('/tickets', { params });
      setTickets(resp.data.items);
      setTotal(resp.data.total);
    } catch {
      setError('No se pudieron cargar los tickets. Intenta de nuevo.');
    } finally {
      setCargando(false);
    }
  }, [fEstado, fCategoria, fPrioridad]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const crearTicket = async (e: FormEvent) => {
    e.preventDefault();
    setCreando(true);
    setErrorModal(null);
    try {
      await api.post<Ticket>('/tickets', {
        titulo: nTitulo,
        descripcion: nDescripcion,
        ...(nServicio ? { servicio_afectado: nServicio } : {}),
      });
      setModalAbierto(false);
      setNTitulo('');
      setNDescripcion('');
      setNServicio('');
      await cargar();
    } catch {
      setErrorModal('No se pudo crear el ticket. Intenta de nuevo.');
    } finally {
      setCreando(false);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-xl font-bold text-slate-800">Tickets</h1>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setModalAbierto(true)}
        >
          Nuevo ticket
        </button>
      </div>

      {/* Filtros */}
      <div className="card p-4 mb-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="label" htmlFor="f-estado">Estado</label>
          <select
            id="f-estado"
            className="input"
            value={fEstado}
            onChange={(e) => setFEstado(e.target.value)}
          >
            <option value="">Todos</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>{TEXTO_ESTADO[e]}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="f-categoria">Categoría</label>
          <select
            id="f-categoria"
            className="input"
            value={fCategoria}
            onChange={(e) => setFCategoria(e.target.value)}
          >
            <option value="">Todas</option>
            {CATEGORIAS.map((c) => (
              <option key={c} value={c}>{TEXTO_CATEGORIA[c]}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="f-prioridad">Prioridad</label>
          <select
            id="f-prioridad"
            className="input"
            value={fPrioridad}
            onChange={(e) => setFPrioridad(e.target.value)}
          >
            <option value="">Todas</option>
            {PRIORIDADES.map((p) => (
              <option key={p} value={p}>{TEXTO_PRIORIDAD[p]}</option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
          {error}
        </div>
      )}

      {cargando ? (
        <Spinner className="py-16" tamano={28} />
      ) : tickets.length === 0 ? (
        <div className="card p-8 text-center text-slate-500">
          No hay tickets con los filtros seleccionados.
        </div>
      ) : (
        <p className="text-sm text-slate-500 mb-2">{total} ticket(s)</p>
      )}

      {/* Tarjetas de tickets (mobile-first) */}
      {!cargando && tickets.length > 0 && (
        <ul className="space-y-3">
          {tickets.map((t) => (
            <li key={t.id}>
              <Link
                to={`/tickets/${t.id}`}
                className="card p-4 block hover:border-emerald-400 transition-colors"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h2 className="font-semibold text-slate-800 truncate">{t.titulo}</h2>
                    <p className="text-sm text-slate-500 mt-0.5">
                      {TEXTO_CATEGORIA[t.categoria]}
                      {t.servicio_afectado ? ` · ${t.servicio_afectado}` : ''}
                    </p>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <BadgeEstado estado={t.estado} />
                    <BadgePrioridad prioridad={t.prioridad} />
                  </div>
                </div>
                {t.etiquetas.length > 0 && (
                  <div className="mt-2 flex gap-1.5 flex-wrap">
                    {t.etiquetas.map((et) => (
                      <BadgeEtiqueta key={et} texto={et} />
                    ))}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}

      {/* Modal de creación */}
      <Modal
        abierto={modalAbierto}
        titulo="Nuevo ticket"
        onClose={() => setModalAbierto(false)}
      >
        {errorModal && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
            {errorModal}
          </div>
        )}
        <form onSubmit={crearTicket} className="space-y-4">
          <div>
            <label className="label" htmlFor="t-titulo">Título</label>
            <input
              id="t-titulo"
              className="input"
              value={nTitulo}
              onChange={(e) => setNTitulo(e.target.value)}
              required
              placeholder="Resumen breve del problema"
            />
          </div>
          <div>
            <label className="label" htmlFor="t-desc">Descripción</label>
            <textarea
              id="t-desc"
              className="input min-h-[120px]"
              value={nDescripcion}
              onChange={(e) => setNDescripcion(e.target.value)}
              required
              placeholder="Describe el problema con detalle"
            />
          </div>
          <div>
            <label className="label" htmlFor="t-servicio">Servicio afectado (opcional)</label>
            <input
              id="t-servicio"
              className="input"
              value={nServicio}
              onChange={(e) => setNServicio(e.target.value)}
              placeholder="Ej.: correo, VPN, impresora"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setModalAbierto(false)}
            >
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={creando}>
              {creando ? <Spinner tamano={18} /> : 'Crear ticket'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
