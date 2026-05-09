const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
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

export type UserProfile = {
  id: string;
  email: string | null;
  name: string | null;
  chesscom_username: string | null;
  lichess_username: string | null;
  subscription_status: string;
  trial_ends_at: string | null;
  timezone: string;
  created_at: string;
};

export const api = {
  getMe: (userId: string) => apiFetch<UserProfile>(`/api/me?user_id=${userId}`),

  onboarding: (chesscom_username: string | null, lichess_username: string | null) =>
    apiFetch<{ user_id: string; job_id: string }>("/api/onboarding", {
      method: "POST",
      body: JSON.stringify({ chesscom_username, lichess_username }),
    }),

  getJob: (jobId: string, userId: string) =>
    apiFetch<JobStatus>(`/api/jobs/${jobId}?user_id=${userId}`),

  triggerIngest: (userId: string, days = 30) =>
    apiFetch<{ user_id: string; job_id: string }>("/api/ingest", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, days }),
    }),
};

// ── LocalStorage helpers for persisting user identity across sessions ─────────

const STORAGE_KEY = "repertoire_user";

export function saveUser(userId: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ userId }));
}

export function loadUser(): { userId: string } | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearUser() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}
