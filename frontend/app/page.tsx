"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api, saveUser, loadUser } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [chesscom, setChesscom] = useState("");
  const [lichess, setLichess] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect returning users straight to their dashboard
  useEffect(() => {
    const saved = loadUser();
    if (saved) router.replace(`/dashboard?user_id=${saved.userId}`);
  }, [router]);

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    if (!chesscom.trim() && !lichess.trim()) {
      setError("Enter at least one chess username.");
      return;
    }
    if (!email.trim()) {
      setError("Enter your email so we can find your account next time.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { user_id, job_id } = await api.onboarding(
        email.trim(),
        chesscom.trim() || null,
        lichess.trim() || null,
      );
      saveUser(user_id, email.trim());
      router.push(`/dashboard?user_id=${user_id}&job_id=${job_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-col min-h-screen">
      {/* Nav */}
      <nav className="border-b border-slate-200 bg-white">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center">
          <span className="font-semibold text-lg tracking-tight">repertoire</span>
        </div>
      </nav>

      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Hero copy */}
        <section className="flex-1 flex flex-col justify-center px-8 py-16 lg:py-0 lg:px-16 max-w-xl">
          <p className="text-sm font-medium text-slate-500 mb-3 uppercase tracking-widest">
            For the 1200–2000 player
          </p>
          <h1 className="text-4xl font-bold tracking-tight leading-tight mb-4">
            Stop solving random puzzles.
          </h1>
          <p className="text-lg text-slate-600 mb-6">
            We ingest <strong>all</strong> your Chess.com and Lichess games,
            find the exact recurring mistakes costing you rating points, and
            drill you on them until they stick.
          </p>
          <ul className="space-y-2 text-sm text-slate-600">
            {[
              "Cross-game pattern detection — not just isolated puzzles",
              "Opening-aware: \"you go wrong on move 9 of the Caro-Kann\"",
              "Spaced repetition drill mode (FSRS)",
              "Ingests 500 to 15,000 games",
            ].map((f) => (
              <li key={f} className="flex gap-2 items-start">
                <span className="text-emerald-500 mt-0.5">✓</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Sign-up form */}
        <section className="flex-1 flex items-center justify-center px-8 py-12 bg-slate-50">
          <Card className="w-full max-w-sm">
            <CardHeader>
              <CardTitle>Analyze my games</CardTitle>
              <CardDescription>
                No account needed. Enter your chess username and we&apos;ll get started.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleStart} className="space-y-4">
                <div className="space-y-1">
                  <Label htmlFor="email">Your email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                  <p className="text-xs text-slate-400">Used to find your data if you return.</p>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="chesscom">Chess.com username</Label>
                  <Input
                    id="chesscom"
                    placeholder="e.g. hikaru"
                    value={chesscom}
                    onChange={(e) => setChesscom(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="lichess">Lichess username</Label>
                  <Input
                    id="lichess"
                    placeholder="e.g. DrNykterstein"
                    value={lichess}
                    onChange={(e) => setLichess(e.target.value)}
                  />
                </div>
                {error && <p className="text-sm text-red-500">{error}</p>}
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Starting…" : "Analyze my games →"}
                </Button>
                <p className="text-xs text-center text-slate-400">
                  We only access your public game history.
                </p>
              </form>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
