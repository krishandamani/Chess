import { getSupabaseBrowserClient } from "./supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getAuthHeader(): Promise<Record<string, string>> {
  const supabase = getSupabaseBrowserClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeader = await getAuthHeader();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeader,
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Typed API wrappers ────────────────────────────────────────────────────────

export type JobStatus = {
  id: string;
  kind: string;
  status: "queued" | "running" | "done" | "failed";
  games_total: number;
  games_done: number;
  positions_analyzed: number;
  cache_hits: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type Profile = {
  id: string;
  display_name: string | null;
  email: string;
  chesscom_username: string | null;
  lichess_username: string | null;
  subscription_status: string;
  trial_ends_at: string | null;
  timezone: string;
  created_at: string;
};

export const api = {
  getMe: () => apiFetch<Profile>("/api/me"),

  onboarding: (chesscom_username: string | null, lichess_username: string | null) =>
    apiFetch<{ job_id: string }>("/api/onboarding", {
      method: "POST",
      body: JSON.stringify({ chesscom_username, lichess_username }),
    }),

  getJob: (jobId: string) => apiFetch<JobStatus>(`/api/jobs/${jobId}`),

  triggerIngest: (days = 30) =>
    apiFetch<{ job_id: string }>("/api/ingest", {
      method: "POST",
      body: JSON.stringify({ days }),
    }),
};
