/**
 * Typed client for the StadiumMind FastAPI backend.
 *
 * All calls go through the Next.js rewrite proxy (`/api/*` -> backend), so the
 * browser never needs to know the backend host. Types mirror the pydantic
 * schemas in backend/stadiummind/api/schemas.py.
 */

export type CongestionLevel = "normal" | "moderate" | "busy" | "congested";

export interface ZoneHeat {
  id: string;
  name: string;
  type: string;
  x: number;
  y: number;
  lat: number | null;
  lng: number | null;
  occupancy: number;
  capacity: number;
  ratio: number;
  level: CongestionLevel;
  accessible: boolean;
}

export interface Match {
  id: string;
  home_team: string;
  away_team: string;
  competition: string;
  venue: string;
  kickoff_utc: string | null;
  status: string;
  home_score: number | null;
  away_score: number | null;
  minute: number | null;
  source: string;
}

export interface Directions {
  origin: string;
  destination: string;
  distance_m: number;
  duration_min: number;
  provider: string;
  polyline: [number, number][];
  steps: string[];
}

export interface VenueAnchor {
  name: string;
  lat: number;
  lng: number;
  footprint_m: number;
}

export interface Recommendation {
  id: string;
  agent: string;
  title: string;
  explanation: string;
  confidence: number;
  zone_id: string | null;
  severity: string;
  actions: string[];
  metadata: Record<string, unknown>;
  approved: boolean | null;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () =>
    http<{ status: string; match_minute: number; llm: string; maps_enabled: boolean; venue: string }>(
      "/api/health",
    ),
  match: () => http<Match>("/api/match"),
  venue: () => http<{ anchor: VenueAnchor; zones: ZoneHeat[] }>("/api/venue"),
  directions: (origin: string, destination: string) =>
    http<Directions>(`/api/directions?origin=${origin}&destination=${destination}`),
  heatmap: () => http<ZoneHeat[]>("/api/crowd/heatmap"),
  tick: () => http<ZoneHeat[]>("/api/crowd/tick", { method: "POST" }),
  recommendations: () => http<Recommendation[]>("/api/ai/recommendations"),
  surge: (zoneId: string, people = 8000) =>
    http(`/api/crowd/surge?zone_id=${zoneId}&people=${people}`, { method: "POST" }),
  query: (intent: string, params: Record<string, unknown> = {}) =>
    http<Recommendation>("/api/ai/query", {
      method: "POST",
      body: JSON.stringify({ intent, params }),
    }),
  login: (username: string, role: string) =>
    http<{ access_token: string; role: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, role }),
    }),
  decide: (recId: string, approved: boolean, token: string) =>
    http<Recommendation>(`/api/ai/recommendations/${recId}/decision`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ approved }),
    }),
};

export const LEVEL_COLOR: Record<CongestionLevel, string> = {
  normal: "#16a34a",
  moderate: "#f59e0b",
  busy: "#ea580c",
  congested: "#dc2626",
};
