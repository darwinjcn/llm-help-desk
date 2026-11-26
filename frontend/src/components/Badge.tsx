import type { Categoria, EstadoTicket, Prioridad } from '../api';

interface BadgeProps {
  texto: string;
  color: string; // clases tailwind completas
}

function BadgeBase({ texto, color }: BadgeProps) {
  return <span className={`badge ${color}`}>{texto}</span>;
}

/** Color por estado del ticket (sin azul/cyan). */
export function BadgeEstado({ estado }: { estado: EstadoTicket }) {
  const colores: Record<EstadoTicket, string> = {
    nuevo: 'bg-emerald-100 text-emerald-800',
    en_triage: 'bg-orange-100 text-orange-800',
    abierto: 'bg-amber-100 text-amber-800',
    en_resolucion: 'bg-orange-100 text-orange-800',
    resuelto: 'bg-emerald-100 text-emerald-800',
    cerrado: 'bg-slate-200 text-slate-700',
  };
  const textos: Record<EstadoTicket, string> = {
    nuevo: 'Nuevo',
    en_triage: 'En triage',
    abierto: 'Abierto',
    en_resolucion: 'En resolución',
    resuelto: 'Resuelto',
    cerrado: 'Cerrado',
  };
  return <BadgeBase texto={textos[estado]} color={colores[estado]} />;
}

/** Color por prioridad del ticket. */
export function BadgePrioridad({ prioridad }: { prioridad: Prioridad }) {
  const colores: Record<Prioridad, string> = {
    critica: 'bg-red-100 text-red-800',
    alta: 'bg-orange-100 text-orange-800',
    media: 'bg-amber-100 text-amber-800',
    baja: 'bg-slate-200 text-slate-700',
  };
  const textos: Record<Prioridad, string> = {
    critica: 'Crítica',
    alta: 'Alta',
    media: 'Media',
    baja: 'Baja',
  };
  return <BadgeBase texto={textos[prioridad]} color={colores[prioridad]} />;
}

/** Color por categoría del ticket. */
export function BadgeCategoria({ categoria }: { categoria: Categoria }) {
  const textos: Record<Categoria, string> = {
    hardware: 'Hardware',
    software: 'Software',
    red: 'Red',
    accesos: 'Accesos',
    otro: 'Otro',
  };
  return <BadgeBase texto={textos[categoria]} color="bg-slate-100 text-slate-600" />;
}

/** Badge genérico para etiquetas libres. */
export function BadgeEtiqueta({ texto }: { texto: string }) {
  return <BadgeBase texto={texto} color="bg-slate-100 text-slate-600" />;
}

/** Badge para eventos generados por IA. */
export function BadgeIA() {
  return <BadgeBase texto="IA" color="bg-emerald-100 text-emerald-800" />;
}

export default BadgeBase;
