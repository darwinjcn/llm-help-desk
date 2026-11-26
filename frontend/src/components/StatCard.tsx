interface StatCardProps {
  titulo: string;
  valor: string | number;
  detalle?: string;
}

/** Tarjeta de métrica para el dashboard. */
export default function StatCard({ titulo, valor, detalle }: StatCardProps) {
  return (
    <div className="card p-4 sm:p-5">
      <p className="text-sm text-slate-500">{titulo}</p>
      <p className="mt-1 text-2xl sm:text-3xl font-semibold text-slate-800">{valor}</p>
      {detalle && <p className="mt-1 text-xs text-slate-400">{detalle}</p>}
    </div>
  );
}
