import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import api, {
  type EstadoTicket,
  type Sugerencia,
  type Ticket,
  type TicketEvent,
} from '../api';
import {
  BadgeCategoria,
  BadgeEstado,
  BadgeEtiqueta,
  BadgeIA,
  BadgePrioridad,
} from '../components/Badge';
import Spinner from '../components/Spinner';
import { useAuth } from '../context/AuthContext';

interface DetalleTicket {
  ticket: Ticket;
  eventos: TicketEvent[];
  sugerencia: Sugerencia | null;
}

const TEXTO_ESTADO: Record<EstadoTicket, string> = {
  nuevo: 'Nuevo',
  en_triage: 'En triage',
  abierto: 'Abierto',
  en_resolucion: 'En resolución',
  resuelto: 'Resuelto',
  cerrado: 'Cerrado',
};
const ESTADOS: EstadoTicket[] = [
  'nuevo',
  'en_triage',
  'abierto',
  'en_resolucion',
  'resuelto',
  'cerrado',
];

/** Detalle del ticket: sugerencia IA, timeline y comentarios. */
export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();

  const [detalle, setDetalle] = useState<DetalleTicket | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sugerencia IA
  const [borradorEditado, setBorradorEditado] = useState('');
  const [editandoBorrador, setEditandoBorrador] = useState(false);
  const [decidiendo, setDecidiendo] = useState(false);
  const [reconsultando, setReconsultando] = useState(false);

  // Comentarios y estado
  const [comentario, setComentario] = useState('');
  const [enviandoComentario, setEnviandoComentario] = useState(false);
  const [nuevoEstado, setNuevoEstado] = useState<EstadoTicket | ''>('');
  const [cambiandoEstado, setCambiandoEstado] = useState(false);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const esAgente = user?.rol === 'agente' || user?.rol === 'admin';

  const cargar = useCallback(async () => {
    if (!id) return;
    setCargando(true);
    setError(null);
    try {
      const resp = await api.get<DetalleTicket>(`/tickets/${id}`);
      setDetalle(resp.data);
      if (resp.data.sugerencia) {
        setBorradorEditado(resp.data.sugerencia.salida.respuesta_borrador);
      }
    } catch {
      setError('No se pudo cargar el ticket.');
    } finally {
      setCargando(false);
    }
  }, [id]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  /** Decisión sobre la sugerencia del agente IA. */
  const decidir = async (aceptada: boolean, respuesta_editada?: string) => {
    if (!id) return;
    setDecidiendo(true);
    setErrorAccion(null);
    try {
      await api.post(`/tickets/${id}/sugerencia/decision`, {
        aceptada,
        ...(respuesta_editada !== undefined ? { respuesta_editada } : {}),
      });
      setEditandoBorrador(false);
      await cargar();
    } catch {
      setErrorAccion('No se pudo registrar la decisión.');
    } finally {
      setDecidiendo(false);
    }
  };

  /** Re-ejecuta el agente de resolución con los comentarios del ticket. */
  const reconsultarIA = async () => {
    if (!id) return;
    setReconsultando(true);
    setErrorAccion(null);
    try {
      await api.post(`/tickets/${id}/sugerencia/regenerar`);
      await cargar();
    } catch {
      setErrorAccion(
        'La IA no generó una sugerencia válida en esta reconsulta. El intento quedó registrado en la auditoría.',
      );
    } finally {
      setReconsultando(false);
    }
  };

  const enviarComentario = async (e: FormEvent) => {
    e.preventDefault();
    if (!id || !comentario.trim()) return;
    setEnviandoComentario(true);
    setErrorAccion(null);
    try {
      await api.post(`/tickets/${id}/comentarios`, { contenido: comentario });
      setComentario('');
      await cargar();
    } catch {
      setErrorAccion('No se pudo enviar el comentario.');
    } finally {
      setEnviandoComentario(false);
    }
  };

  const cambiarEstado = async (estado: EstadoTicket) => {
    if (!id) return;
    setCambiandoEstado(true);
    setErrorAccion(null);
    try {
      await api.patch<Ticket>(`/tickets/${id}/estado`, { estado });
      await cargar();
    } catch {
      setErrorAccion('No se pudo cambiar el estado.');
    } finally {
      setCambiandoEstado(false);
      setNuevoEstado('');
    }
  };

  if (cargando) return <Spinner className="py-16" tamano={28} />;

  if (error || !detalle) {
    return (
      <div>
        <Link to="/tickets" className="text-emerald-700 hover:underline text-sm">
          ← Volver a tickets
        </Link>
        <div className="mt-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
          {error ?? 'Ticket no encontrado.'}
        </div>
      </div>
    );
  }

  const { ticket, eventos, sugerencia } = detalle;

  return (
    <div>
      <Link to="/tickets" className="text-emerald-700 hover:underline text-sm">
        ← Volver a tickets
      </Link>

      {/* Encabezado */}
      <div className="mt-3">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800">{ticket.titulo}</h1>
        <div className="mt-2 flex flex-wrap gap-2 items-center">
          <BadgeEstado estado={ticket.estado} />
          <BadgeCategoria categoria={ticket.categoria} />
          <BadgePrioridad prioridad={ticket.prioridad} />
          {ticket.etiquetas.map((et) => (
            <BadgeEtiqueta key={et} texto={et} />
          ))}
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Creado: {new Date(ticket.created_at).toLocaleString('es')}
        </p>
      </div>

      {/* Descripción */}
      <div className="card p-4 mt-4">
        <h2 className="text-sm font-semibold text-slate-600 mb-2">Descripción</h2>
        <p className="text-sm text-slate-700 whitespace-pre-wrap">{ticket.descripcion}</p>
        {ticket.servicio_afectado && (
          <p className="mt-2 text-sm text-slate-500">
            <span className="font-medium">Servicio afectado:</span> {ticket.servicio_afectado}
          </p>
        )}
      </div>

      {/* Sugerencia del agente IA (solo agente/admin) */}
      {esAgente && sugerencia && (
        <div className="card p-4 mt-4 border-emerald-300">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <h2 className="text-sm font-semibold text-slate-700">
              Sugerencia del agente IA
            </h2>
            <span
              className={`badge ${
                sugerencia.salida.confianza === 'alta'
                  ? 'bg-emerald-100 text-emerald-800'
                  : sugerencia.salida.confianza === 'media'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-red-100 text-red-800'
              }`}
            >
              Confianza: {sugerencia.salida.confianza}
            </span>
          </div>

          {sugerencia.salida.puede_resolver ? (
            editandoBorrador ? (
              <textarea
                className="input min-h-[140px]"
                value={borradorEditado}
                onChange={(e) => setBorradorEditado(e.target.value)}
              />
            ) : (
              <p className="text-sm text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-lg p-3">
                {borradorEditado}
              </p>
            )
          ) : (
            <p className="text-sm text-slate-600 bg-amber-50 rounded-lg p-3">
              La IA determinó que este ticket <strong>no puede resolverse automáticamente</strong>.
              Respuesta borrador: {sugerencia.salida.respuesta_borrador}
            </p>
          )}

          {sugerencia.salida.fuentes.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {sugerencia.salida.fuentes.map((f) => (
                <BadgeEtiqueta key={f} texto={f} />
              ))}
            </div>
          )}

          {!sugerencia.aceptado && (
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                className="btn-primary"
                onClick={() => void decidir(true)}
                disabled={decidiendo}
              >
                Aceptar
              </button>
              {editandoBorrador ? (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => void decidir(true, borradorEditado)}
                  disabled={decidiendo}
                >
                  Guardar y aceptar
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setBorradorEditado(sugerencia.salida.respuesta_borrador);
                    setEditandoBorrador(true);
                  }}
                >
                  Editar y aceptar
                </button>
              )}
              <button
                type="button"
                className="btn-danger"
                onClick={() => void decidir(false)}
                disabled={decidiendo}
              >
                Rechazar
              </button>
            </div>
          )}
          {sugerencia.aceptado && (
            <p className="mt-2 text-sm text-emerald-700">
              Sugerencia aceptada
              {sugerencia.editado_por_humano ? ' (editada por un humano)' : ''}.
            </p>
          )}
        </div>
      )}

      {/* Reconsultar a la IA (solo agente/admin) */}
      {esAgente && ticket.estado !== 'cerrado' && (
        <div className="card p-4 mt-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-700">Reconsultar al agente IA</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Regenera la sugerencia teniendo en cuenta la descripción y los comentarios
              del ticket. Útil si el cliente aportó información nueva.
            </p>
          </div>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => void reconsultarIA()}
            disabled={reconsultando}
          >
            {reconsultando ? (
              <span className="flex items-center gap-2">
                <Spinner tamano={16} /> Consultando a la IA…
              </span>
            ) : (
              'Reconsultar a la IA'
            )}
          </button>
        </div>
      )}

      {errorAccion && (
        <div className="mt-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
          {errorAccion}
        </div>
      )}

      {/* Cambio de estado (solo agente/admin) */}
      {esAgente && (
        <div className="card p-4 mt-4">
          <label className="label" htmlFor="c-estado">
            Cambiar estado
          </label>
          <div className="flex flex-wrap gap-2 items-center">
            <select
              id="c-estado"
              className="input sm:max-w-xs"
              value={nuevoEstado || ticket.estado}
              onChange={(e) => setNuevoEstado(e.target.value as EstadoTicket)}
            >
              {ESTADOS.map((e) => (
                <option key={e} value={e}>{TEXTO_ESTADO[e]}</option>
              ))}
            </select>
            <button
              type="button"
              className="btn-secondary"
              disabled={
                cambiandoEstado || !nuevoEstado || nuevoEstado === ticket.estado
              }
              onClick={() => nuevoEstado && void cambiarEstado(nuevoEstado)}
            >
              Aplicar
            </button>
          </div>
        </div>
      )}

      {/* Timeline de eventos */}
      <div className="card p-4 mt-4">
        <h2 className="text-sm font-semibold text-slate-600 mb-3">Actividad</h2>
        <ol className="space-y-3">
          {eventos.map((ev) => (
            <li key={ev.id} className="border-l-2 border-slate-200 pl-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-500 uppercase">
                  {ev.tipo.replace('_', ' ')}
                </span>
                {(ev.tipo.includes('agente') || ev.datos_agente) && <BadgeIA />}
                <span className="text-xs text-slate-400">
                  {new Date(ev.created_at).toLocaleString('es')}
                </span>
              </div>
              {ev.contenido && (
                <p className="text-sm text-slate-700 mt-1 whitespace-pre-wrap">
                  {ev.contenido}
                </p>
              )}
              {ev.autor_nombre && (
                <p className="text-xs text-slate-400 mt-0.5">— {ev.autor_nombre}</p>
              )}
            </li>
          ))}
          {eventos.length === 0 && (
            <li className="text-sm text-slate-400">Sin actividad todavía.</li>
          )}
        </ol>
      </div>

      {/* Caja de comentario */}
      <form onSubmit={enviarComentario} className="card p-4 mt-4">
        <label className="label" htmlFor="c-comentario">Agregar comentario</label>
        <textarea
          id="c-comentario"
          className="input min-h-[100px]"
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
          placeholder="Escribe un comentario…"
        />
        <div className="mt-3 flex justify-end">
          <button
            type="submit"
            className="btn-primary"
            disabled={enviandoComentario || !comentario.trim()}
          >
            {enviandoComentario ? <Spinner tamano={18} /> : 'Enviar comentario'}
          </button>
        </div>
      </form>
    </div>
  );
}
