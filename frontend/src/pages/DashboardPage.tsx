import { useCallback, useEffect, useState } from 'react';
import api, { type AgentRun, type EvalReport, type Ticket } from '../api';
import Spinner from '../components/Spinner';
import StatCard from '../components/StatCard';

/** Dashboard IA: métricas, últimas corridas del agente y reporte de evals. */
export default function DashboardPage() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [evals, setEvals] = useState<EvalReport | null>(null);
  const [totalTickets, setTotalTickets] = useState(0);
  const [ticketsAbiertos, setTicketsAbiertos] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [corriendoEvals, setCorriendoEvals] = useState(false);
  const [mensajeEvals, setMensajeEvals] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [respRuns, respEvals, respTickets] = await Promise.all([
        api.get<{ items: AgentRun[] }>('/agent/runs', { params: { limit: 20 } }),
        api.get<EvalReport>('/evals/report'),
        api.get<{ items: Ticket[]; total: number }>('/tickets'),
      ]);
      setRuns(respRuns.data.items);
      setEvals(respEvals.data);
      setTotalTickets(respTickets.data.total);
      // "Abiertos" = aún no resueltos ni cerrados
      setTicketsAbiertos(
        respTickets.data.items.filter(
          (t) => t.estado !== 'resuelto' && t.estado !== 'cerrado',
        ).length,
      );
    } catch {
      setError('No se pudieron cargar las métricas del dashboard.');
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  /** Ejecuta las evals (puede tardar varios minutos). */
  const correrEvals = async () => {
    const ok = window.confirm(
      'Las evals pueden tardar varios minutos ya que ejecutan el agente local sobre varios casos. ¿Continuar?',
    );
    if (!ok) return;
    setCorriendoEvals(true);
    setMensajeEvals(null);
    setError(null);
    try {
      const resp = await api.post<{ mensaje: string }>('/evals/run');
      setMensajeEvals(resp.data.mensaje ?? 'Evals iniciadas.');
      await cargar();
    } catch {
      setError('No se pudo ejecutar las evals.');
    } finally {
      setCorriendoEvals(false);
    }
  };

  // Métricas derivadas de los agent runs
  const totalRuns = runs.length;
  const aceptados = runs.filter((r) => r.aceptado === true).length;
  const tasaAceptacion = totalRuns > 0 ? Math.round((aceptados / totalRuns) * 100) : 0;
  const latencias = runs.map((r) => r.latencia_ms).sort((a, b) => a - b);
  const p50 =
    latencias.length > 0
      ? latencias[Math.max(0, Math.ceil(latencias.length / 2) - 1)]
      : 0;

  if (cargando) return <Spinner className="py-16" tamano={28} />;

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-800 mb-4">Dashboard IA</h1>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
          {error}
        </div>
      )}

      {/* Tarjetas de métricas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard titulo="Total tickets" valor={totalTickets} />
        <StatCard titulo="Tickets abiertos" valor={ticketsAbiertos} />
        <StatCard titulo="Tasa de aceptación IA" valor={`${tasaAceptacion}%`} detalle={`${aceptados}/${totalRuns} aceptados`} />
        <StatCard titulo="Latencia p50 (ms)" valor={p50} />
      </div>

      {mensajeEvals && (
        <div className="mt-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm px-3 py-2">
          {mensajeEvals}
        </div>
      )}

      {/* Últimas corridas del agente */}
      <div className="card mt-6 overflow-hidden">
        <div className="p-4 pb-0">
          <h2 className="text-sm font-semibold text-slate-600 mb-3">
            Últimas corridas del agente
          </h2>
        </div>
        {runs.length === 0 ? (
          <p className="p-4 pt-0 text-sm text-slate-400">Sin corridas registradas.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="px-4 py-2 font-medium">Ticket</th>
                  <th className="px-4 py-2 font-medium">Tipo de agente</th>
                  <th className="px-4 py-2 font-medium">Modelo</th>
                  <th className="px-4 py-2 font-medium">Latencia</th>
                  <th className="px-4 py-2 font-medium">Aceptado</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} className="border-b border-slate-100">
                    <td className="px-4 py-2 text-slate-700">
                      <a
                        href={`/tickets/${r.ticket_id}`}
                        className="text-emerald-700 hover:underline"
                      >
                        Ticket #{r.ticket_id}
                      </a>
                    </td>
                    <td className="px-4 py-2 text-slate-700">{r.tipo_agente}</td>
                    <td className="px-4 py-2 text-slate-500">{r.modelo}</td>
                    <td className="px-4 py-2 text-slate-700">{r.latencia_ms} ms</td>
                    <td className="px-4 py-2">
                      {r.aceptado === true ? (
                        <span className="badge bg-emerald-100 text-emerald-800">
                          {r.editado_por_humano ? 'Aceptado (editado)' : 'Aceptado'}
                        </span>
                      ) : r.aceptado === false ? (
                        <span className="badge bg-red-100 text-red-800">Rechazado</span>
                      ) : r.tipo_agente === 'resolucion' ? (
                        <span className="badge bg-slate-200 text-slate-600">Pendiente</span>
                      ) : (
                        /* Solo las sugerencias de resolución se aceptan/rechazan;
                           el triage no tiene decisión humana. */
                        <span className="badge bg-slate-100 text-slate-400">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reporte de evals */}
      <div className="card mt-6 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <h2 className="text-sm font-semibold text-slate-600">Reporte de evals</h2>
          {(!evals || !evals.disponible) && (
            <button
              type="button"
              className="btn-primary"
              onClick={() => void correrEvals()}
              disabled={corriendoEvals}
            >
              {corriendoEvals ? (
                <>
                  <Spinner tamano={18} /> Ejecutando…
                </>
              ) : (
                'Correr evals'
              )}
            </button>
          )}
        </div>

        {corriendoEvals && (
          <p className="text-sm text-amber-700 mb-3">
            Las evals están corriendo. Esto puede tardar varios minutos.
          </p>
        )}

        {evals?.disponible && evals.reporte ? (
          <pre className="bg-slate-50 rounded-lg p-3 text-xs text-slate-700 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(evals.reporte, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-slate-500">
            {evals && !evals.disponible
              ? 'Aún no hay reporte de evals disponible. Ejecuta las evals para generarlo.'
              : 'No se pudo cargar el reporte.'}
          </p>
        )}
      </div>
    </div>
  );
}
