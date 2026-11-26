import axios from 'axios';

/* ===================== Tipos del dominio ===================== */

export type Rol = 'cliente' | 'agente' | 'admin';
export type EstadoTicket =
  | 'nuevo'
  | 'en_triage'
  | 'abierto'
  | 'en_resolucion'
  | 'resuelto'
  | 'cerrado';
export type Categoria = 'hardware' | 'software' | 'red' | 'accesos' | 'otro';
export type Prioridad = 'baja' | 'media' | 'alta' | 'critica';
export type Confianza = 'alta' | 'media' | 'baja';

export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: Rol;
}

export interface Ticket {
  id: string;
  titulo: string;
  descripcion: string;
  estado: EstadoTicket;
  categoria: Categoria;
  prioridad: Prioridad;
  servicio_afectado: string | null;
  etiquetas: string[];
  usuario_id: string;
  agente_asignado_id: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface TicketEvent {
  id: string;
  tipo: string;
  contenido: string;
  datos_agente: Record<string, unknown> | null;
  autor_nombre: string | null;
  created_at: string;
}

export interface Sugerencia {
  id: string;
  salida: {
    puede_resolver: boolean;
    respuesta_borrador: string;
    fuentes: string[];
    confianza: Confianza;
  };
  aceptado: boolean;
  editado_por_humano: boolean;
}

export interface KbArticle {
  id: string;
  titulo: string;
  categoria: Categoria;
  etiquetas: string[];
  activo: boolean;
  version: number;
  created_at: string;
}

export interface AgentRun {
  id: string;
  ticket_id: string;
  tipo_agente: string;
  modelo: string;
  latencia_ms: number;
  aceptado: boolean | null;
  editado_por_humano: boolean;
  created_at: string;
}

export interface EvalReport {
  disponible: boolean;
  reporte?: {
    total_casos?: number;
    precision_categoria?: number;
    precision_prioridad?: number;
    latencia_ms?: { p50?: number; p95?: number };
    [clave: string]: unknown;
  };
}

/* ===================== Cliente axios ===================== */

const TOKEN_KEY = 'llm_help_desk_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

const api = axios.create({
  baseURL: '/api',
});

// Adjunta el token JWT a cada petición
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Si la sesión expira (401), limpia el token y redirige a /login
api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      clearToken();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

export default api;
