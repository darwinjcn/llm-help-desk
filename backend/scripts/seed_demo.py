"""Datos de demostración idempotentes para llm-help-desk.

Crea usuarios de prueba, 5 artículos de la KB (con ingesta de embeddings si
Ollama está disponible) y 8 tickets en distintos estados para que el
dashboard tenga datos desde el primer arranque.

Uso (desde /backend o dentro del contenedor):
    python scripts/seed_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    AgentRun,
    KnowledgeArticle,
    Ticket,
    TicketEvent,
    Usuario,
)
from app.security import hashear_password  # noqa: E402
from app.services import rag  # noqa: E402

USUARIOS = [
    ("admin@local.dev", "admin1234", "Administrador", "admin"),
    ("agente1@local.dev", "agente1234", "Laura Agente", "agente"),
    ("cliente1@local.dev", "cliente1234", "Carlos Cliente", "cliente"),
    ("cliente2@local.dev", "cliente1234", "Maria Cliente", "cliente"),
]

ARTICULOS = [
    (
        "Restablecimiento de contraseñas y accesos al ERP",
        "Procedimiento para resolver problemas de acceso al ERP.\n\n"
        "1. Verificar que el usuario existe y está activo en el módulo de administración.\n"
        "2. Restablecer la contraseña desde el panel: Usuarios > Buscar usuario > Restablecer contraseña. La clave temporal es Validez+dia en formato claveVAL2024.\n"
        "3. Si el error persiste tras el restablecimiento, revisar que la cuenta no esté bloqueada por intentos fallidos; el desbloqueo se hace en Usuarios > Seguridad > Desbloquear.\n"
        "4. Para solicitar acceso a un repositorio o módulo nuevo, el jefe directo debe enviar la solicitud por el sistema de accesos; el plazo habitual es de 48 horas.\n"
        "5. Escalar a administración de accesos si el problema continúa después del desbloqueo.",
        "accesos",
        ["erp", "contrasena", "accesos"],
    ),
    (
        "Error 500 en el ERP: diagnóstico y reinicio del servicio",
        "El error 500 al entrar al ERP suele significar que el servicio de aplicación está caído o sin memoria.\n\n"
        "1. Confirmar el alcance: si solo un usuario tiene el problema, pedirle limpiar caché del navegador; si son varios, seguir los pasos siguientes.\n"
        "2. Conectarse al servidor de aplicaciones y verificar el estado del servicio con: systemctl status app.service.\n"
        "3. Si el servicio está caído, reiniciarlo con: sudo systemctl restart app.service (el reinicio toma entre 2 y 3 minutos).\n"
        "4. Revisar los últimos errores en /var/log/app/app.log buscando la palabra ERROR.\n"
        "5. Si el error 500 reaparece después del reinicio, escalar al equipo de infraestructura adjuntando el log de la última hora.\n\n"
        "Nota: los problemas de lentitud general del ERP (sin error 500) se revisan primero con el artículo de rendimiento.",
        "software",
        ["erp", "error-500", "servicio"],
    ),
    (
        "Problemas de red y VPN: caída total y autenticación",
        "Guía de diagnóstico para problemas de conectividad.\n\n"
        "CAÍDA TOTAL DE RED EN UNA SEDE:\n"
        "1. Confirmar el alcance preguntando en el canal de la sede (si nadie tiene red, es caída total).\n"
        "2. Verificar si el router principal responde al ping en la IP 10.0.0.1.\n"
        "3. Si no responde, contactar al proveedor de internet y abrir incidencia con número de sede; es un escenario de escalado inmediato a redes.\n\n"
        "ERROR DE AUTENTICACIÓN DE VPN:\n"
        "1. Verificar que la cuenta no esté vencida en el portal de usuarios.\n"
        "2. Reinstalar el certificado VPN desde el portal: Descargas > Certificado VPN > Instalar.\n"
        "3. Probar la conexión desde otra red (compartir datos móviles) para descartar bloqueo del ISP.\n"
        "4. Si el error es 'certificado no válido', regenerar el certificado desde el portal y reintentar.\n\n"
        "DESCONECCIONES INTERMITENTES DE WIFI:\n"
        "1. Verificar la intensidad de señal en el área afectada; las salas de reuniones del segundo piso tienen un repetidor conocido por fallar.\n"
        "2. Olvidar la red y volver a conectar; si persiste, escalar a redes indicando sala y horario de las caídas.",
        "red",
        ["vpn", "internet", "wifi"],
    ),
    (
        "Impresoras de red: cola de impresión y conexión",
        "Resolución de problemas de impresión en red.\n\n"
        "1. Identificar la impresora por nombre (ej. IMP-3P-01 es la del tercer piso).\n"
        "2. Si aparece 'sin conexión': verificar que el cable de red esté conectado y que la impresora tenga IP (menú Configuración > Red en el panel de la impresora).\n"
        "3. Reiniciar el servidor de colas: Colas > Reiniciar servicio de impresión; las documentos pendientes se reenvían automáticamente.\n"
        "4. Si el documento se queda en 'enviando a impresora', cancelar el trabajo desde la cola y reintentar.\n"
        "5. Si la impresora no aparece en el listado, instalarla desde \\\\servidor-impresion con el nombre correspondiente.\n\n"
        "Los problemas físicos (atascos de papel, tóner) los atiende el personal de cada piso.",
        "hardware",
        ["impresora", "red", "cola"],
    ),
    (
        "Hardware: laptops, monitores y periféricos",
        "Diagnóstico rápido de problemas de hardware de escritorio.\n\n"
        "LAPTOP NO ENCIENDE:\n"
        "1. Verificar el cargador y la luz indicadora de carga.\n"
        "2. Reinicio forzado: mantener el botón de encendido 15 segundos con el cargador conectado.\n"
        "3. Si tiene batería removible, quitarla, esperar 1 minuto y reconectar.\n"
        "4. Si no enciende tras estos pasos, generar reclamo al taller de hardware; el préstamo de equipo se solicita al mismo ticket.\n\n"
        "MONITOR PARPADEA:\n"
        "1. Revisar el cable de video (HDMI/DP) y reconectarlo en ambos extremos.\n"
        "2. Probar con otro cable o con otro puerto de la laptop.\n"
        "3. Actualizar el driver de video desde el portal de software.\n"
        "4. Si el parpadeo persiste con otro cable, se solicita reposición del monitor (aprobación del jefe).\n\n"
        "TECLADO O MOUSE FALLANDO:\n"
        "1. Probar el periférico en otra computadora para confirmar el fallo.\n"
        "2. Si confirma el fallo, solicitar reposición por ticket indicando modelo y número de serie.",
        "hardware",
        ["laptop", "monitor", "perifericos"],
    ),
]

TICKETS_DEMO = [
    # (titulo, descripcion, servicio, estado, categoria, prioridad, cliente, etiquetas)
    ("El ERP no abre desde esta mañana", "Me da error 500 al intentar entrar al ERP. Trabajo en contabilidad.", "ERP", "nuevo", None, None, "cliente1", []),
    ("No me llega el correo", "Desde anoche no me llegan correos nuevos, el cliente Outlook queda cargando.", "Correo", "nuevo", None, None, "cliente2", []),
    ("La VPN no conecta desde casa", "Error de autenticación al conectar la VPN. Ayer funcionó bien.", "VPN", "en_triage", None, None, "cliente1", []),
    ("Impresora del 3er piso sin conexión", "Aparece sin conexión en la cola de impresión desde ayer.", "Impresora 3er Piso", "abierto", "hardware", "baja", "cliente2", ["impresora", "cola"]),
    ("Monitor parpadea a ratos", "El monitor parpadea de vez en cuando, ya reconecté el cable HDMI.", "Estación de trabajo", "abierto", "hardware", "baja", "cliente1", ["monitor", "video"]),
    ("WiFi inestable en sala de reuniones", "La conexión se corta cada pocos minutos en la sala 2.", "WiFi", "abierto", "red", "media", "cliente2", ["wifi", "sala"]),
    ("No puedo entrar al sistema de vacaciones", "Dice usuario no autorizado pero mi jefe dice que ya me dio el permiso.", "Portal RRHH", "resuelto", "accesos", "media", "cliente1", ["accesos", "portal"]),
    ("Solicito mouse adicional", "Para la estación de trabajo del área de diseño.", "Estación de trabajo", "cerrado", "hardware", "baja", "cliente2", ["perifericos"]),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # --- Usuarios -------------------------------------------------------
        usuarios: dict[str, Usuario] = {}
        for email, password, nombre, rol in USUARIOS:
            user = db.query(Usuario).filter(Usuario.email == email).first()
            if user is None:
                user = Usuario(
                    email=email,
                    password_hash=hashear_password(password),
                    nombre=nombre,
                    rol=rol,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"Usuario creado: {email} ({rol})")
            usuarios[rol if rol != "admin" else "admin"] = user
            usuarios[email] = user

        # --- Artículos de la KB ---------------------------------------------
        for titulo, contenido, categoria, etiquetas in ARTICULOS:
            if db.query(KnowledgeArticle).filter(KnowledgeArticle.titulo == titulo).first():
                continue
            art = KnowledgeArticle(
                titulo=titulo,
                contenido=contenido,
                categoria=categoria,
                etiquetas=etiquetas,
                created_by=usuarios["admin"].id,
            )
            db.add(art)
            db.commit()
            db.refresh(art)
            try:
                n = rag.ingesta_articulo(db, art)
                print(f"Artículo '{titulo[:50]}...' indexado ({n} chunks)")
            except Exception as exc:  # noqa: BLE001
                print(
                    f"AVISO: artículo '{titulo[:50]}...' guardado pero SIN embeddings "
                    f"(¿Ollama corriendo con nomic-embed-text?): {exc}"
                )

        # --- Tickets de demostración ----------------------------------------
        if db.query(Ticket).count() == 0:
            agente = usuarios["agente1@local.dev"]
            for (
                titulo,
                descripcion,
                servicio,
                estado,
                categoria,
                prioridad,
                cliente,
                etiquetas,
            ) in TICKETS_DEMO:
                t = Ticket(
                    titulo=titulo,
                    descripcion=descripcion,
                    servicio_afectado=servicio,
                    estado=estado,
                    categoria=categoria,
                    prioridad=prioridad,
                    etiquetas=etiquetas,
                    usuario_id=usuarios[f"{cliente}@local.dev"].id,
                    agente_asignado_id=agente.id if estado not in ("nuevo", "en_triage") else None,
                )
                db.add(t)
                db.commit()
                db.refresh(t)
                db.add(
                    TicketEvent(
                        ticket_id=t.id,
                        autor_id=usuarios[f"{cliente}@local.dev"].id,
                        tipo="creado",
                        contenido="Ticket creado por el usuario.",
                    )
                )
                if categoria:  # tickets ya triados: simulamos el evento del agente
                    db.add(
                        TicketEvent(
                            ticket_id=t.id,
                            autor_id=None,
                            tipo="triage_agente",
                            contenido=(
                                f"Clasificado como {categoria} con prioridad {prioridad}."
                            ),
                            datos_agente={
                                "categoria": categoria,
                                "prioridad": prioridad,
                                "servicio_afectado": servicio,
                                "requiere_escalado": False,
                                "etiquetas": etiquetas,
                                "justificacion": "Clasificación simulada por el seed.",
                            },
                        )
                    )
                if estado == "cerrado":
                    from datetime import datetime, timezone

                    t.closed_at = datetime.now(timezone.utc)
                db.commit()
                print(f"Ticket {t.id}: '{titulo[:45]}...' [{estado}]")

            # Dos AgentRun de ejemplo para que el dashboard muestre métricas
            runs_demo = [
                (4, True, False),   # sugerencia aceptada
                (5, False, False),  # sugerencia rechazada
                (6, True, True),    # sugerencia aceptada con edición humana
            ]
            for ticket_id, aceptado, editado in runs_demo:
                db.add(
                    AgentRun(
                        ticket_id=ticket_id,
                        tipo_agente="resolucion",
                        prompt_version="v1",
                        modelo="qwen2.5:3b-instruct",
                        entrada={"fuentes_recuperadas": ["KB-4", "KB-5"]},
                        salida_validada={
                            "puede_resolver": True,
                            "respuesta_borrador": "Borrador simulado por el seed de demostración.",
                            "fuentes": ["KB-4"],
                            "confianza": "media",
                        },
                        latencia_ms=5200,
                        aceptado=aceptado,
                        editado_por_humano=editado,
                    )
                )
            db.commit()
            print("AgentRuns de demostración creados (métricas del dashboard).")

        print("\nSeed completado. Usuarios de prueba:")
        for email, password, _, rol in USUARIOS:
            print(f"  {email} / {password}  [{rol}]")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
