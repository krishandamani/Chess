"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [chesscom, setChesscom] = useState("");
  const [lichess, setLichess] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!chesscom.trim() && !lichess.trim()) {
      setError("Enter at least one username.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { job_id } = await api.onboarding(
        chesscom.trim() || null,
        lichess.trim() || null,
      );
      router.push(`/dashboard?job_id=${job_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Welcome to Repertoire</h1>
          <p className="text-slate-500 mt-1 text-sm">
            Enter your chess username to start analyzing your games.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Your chess accounts</CardTitle>
            <CardDescription>Add one or both — we'll analyze all your games.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
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
                {loading ? "Starting analysis…" : "Analyze my games"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-slate-400">
          We only access your <strong>public</strong> game history. No private data, ever.
        </p>
      </div>
    </div>
  );
}
