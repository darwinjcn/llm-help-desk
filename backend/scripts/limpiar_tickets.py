"""Limpia TODOS los tickets demo: tickets, eventos y AgentRuns.

Conserva intactos: usuarios, artículos de la KB y sus chunks (embeddings).

Uso (dentro del contenedor backend):
    python scripts/limpiar_tickets.py          # solo muestra qué haría
    python scripts/limpiar_tickets.py --si     # ejecuta la limpieza
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import AgentRun, Ticket, TicketEvent  # noqa: E402


def main() -> None:
    confirmado = "--si" in sys.argv
    db = SessionLocal()
    try:
        n_tickets = db.query(Ticket).count()
        n_eventos = db.query(TicketEvent).count()
        n_runs = db.query(AgentRun).count()

        if n_tickets == 0 and n_eventos == 0 and n_runs == 0:
            print("No hay tickets, eventos ni AgentRuns que limpiar.")
            return

        print(f"Se eliminarán: {n_tickets} tickets, {n_eventos} eventos, {n_runs} agent_runs.")
        print("Se conservan: usuarios y artículos de la KB (con sus embeddings).")

        if not confirmado:
            print("\nSin cambios. Ejecuta de nuevo con --si para confirmar:")
            print("    python scripts/limpiar_tickets.py --si")
            return

        # Orden: primero hijos (FK), luego tickets.
        db.query(AgentRun).delete(synchronize_session=False)
        db.query(TicketEvent).delete(synchronize_session=False)
        db.query(Ticket).delete(synchronize_session=False)
        # Reiniciar secuencias para que los próximos tickets empiecen en #1
        for tabla in ("tickets", "ticket_events", "agent_runs"):
            db.execute(
                text("SELECT setval(pg_get_serial_sequence(:t, 'id'), 1, false)"),
                {"t": tabla},
            )
        db.commit()
        print("\nLimpieza completada. La base quedó lista para tickets reales (IDs desde 1).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
