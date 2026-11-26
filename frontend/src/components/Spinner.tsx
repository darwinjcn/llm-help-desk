interface SpinnerProps {
  /** Tamaño en píxeles (por defecto 24). */
  tamano?: number;
  /** Clases extra para el contenedor. */
  className?: string;
}

/** Spinner de carga reutilizable. */
export default function Spinner({ tamano = 24, className = '' }: SpinnerProps) {
  return (
    <div className={`flex items-center justify-center ${className}`} role="status" aria-label="Cargando">
      <svg
        className="animate-spin text-emerald-600"
        width={tamano}
        height={tamano}
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
        />
      </svg>
    </div>
  );
}
