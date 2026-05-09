"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, saveUser, loadUser } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [chesscom, setChesscom] = useState("");
  const [lichess, setLichess] = useState("");
  const [showLichess, setShowLichess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = loadUser();
    if (saved) router.replace(`/dashboard?user_id=${saved.userId}`);
  }, [router]);

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    const cc = chesscom.trim();
    const li = lichess.trim();
    if (!cc && !li) {
      setError("Enter at least one username.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { user_id, job_id } = await api.onboarding(cc || null, li || null);
      saveUser(user_id);
      router.push(`/dashboard?user_id=${user_id}&job_id=${job_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-white flex flex-col">
      <nav className="border-b px-6 h-14 flex items-center">
        <span className="font-semibold tracking-tight">repertoire</span>
      </nav>

      <div className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm space-y-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">
              Stop solving random puzzles.
            </h1>
            <p className="text-slate-500 text-sm leading-relaxed">
              Enter your Chess.com username. We&apos;ll find the mistakes that
              keep costing you rating points and drill you on them.
            </p>
          </div>

          <form onSubmit={handleStart} className="space-y-3">
            <div className="space-y-1">
              <label className="block text-sm font-medium" htmlFor="chesscom">
                Chess.com username
              </label>
              <input
                id="chesscom"
                className="block w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="hikaru"
                value={chesscom}
                onChange={(e) => setChesscom(e.target.value)}
                autoComplete="off"
                autoCapitalize="off"
                spellCheck={false}
              />
            </div>

            {showLichess ? (
              <div className="space-y-1">
                <label className="block text-sm font-medium" htmlFor="lichess">
                  Lichess username
                </label>
                <input
                  id="lichess"
                  className="block w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                  placeholder="DrNykterstein"
                  value={lichess}
                  onChange={(e) => setLichess(e.target.value)}
                  autoComplete="off"
                  autoCapitalize="off"
                  spellCheck={false}
                />
              </div>
            ) : (
              <button
                type="button"
                className="text-xs text-slate-400 hover:text-slate-600"
                onClick={() => setShowLichess(true)}
              >
                + Also add Lichess account
              </button>
            )}

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="block w-full bg-slate-900 text-white rounded-md py-2.5 text-sm font-medium hover:bg-slate-700 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loading ? "Starting analysis…" : "Analyze my games →"}
            </button>
            <p className="text-xs text-center text-slate-400">
              Public game history only. No account needed.
            </p>
          </form>
        </div>
      </div>
    </main>
  );
}
