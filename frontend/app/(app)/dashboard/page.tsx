"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, type JobStatus, loadUser, clearUser } from "@/lib/api";

function ProgressBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
      <div
        className="bg-slate-800 h-2 rounded-full transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

const statusLabel: Record<string, string> = {
  queued: "Queued",
  running: "Analyzing",
  done: "Complete",
  failed: "Failed",
};

function AnalysisProgress({ jobId, userId }: { jobId: string; userId: string }) {
  const [job, setJob] = useState<JobStatus | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      while (!cancelled) {
        try {
          const j = await api.getJob(jobId, userId);
          if (!cancelled) setJob(j);
          if (j.status === "done" || j.status === "failed") break;
        } catch {
          // silently retry
        }
        await new Promise((r) => setTimeout(r, 3000));
      }
    }

    poll();
    return () => { cancelled = true; };
  }, [jobId, userId]);

  if (!job) return <p className="text-sm text-slate-500">Starting analysis…</p>;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Badge
          variant={
            job.status === "done"
              ? "success"
              : job.status === "failed"
              ? "destructive"
              : "secondary"
          }
        >
          {statusLabel[job.status] ?? job.status}
        </Badge>
        <span className="text-sm text-slate-600">
          {job.status === "running"
            ? `Analyzed ${job.games_done} of ${job.games_total} games`
            : job.status === "done"
            ? `${job.games_total} games · ${job.positions_analyzed} positions`
            : job.status === "failed"
            ? job.error ?? "Analysis failed"
            : "Waiting to start…"}
        </span>
      </div>
      {job.status === "running" && (
        <ProgressBar value={job.games_done} max={Math.max(job.games_total, 1)} />
      )}
      {job.status === "running" && (
        <p className="text-xs text-slate-400">
          {job.cache_hits > 0 && `${job.cache_hits} cache hits · `}
          First 200 games takes 3–8 minutes.
        </p>
      )}
    </div>
  );
}

function DashboardContent() {
  const params = useSearchParams();
  const router = useRouter();

  const jobId = params.get("job_id");
  const userId = params.get("user_id") ?? loadUser()?.userId ?? "";

  useEffect(() => {
    if (!userId) router.replace("/");
  }, [userId, router]);

  function handleStartOver() {
    clearUser();
    router.replace("/");
  }

  if (!userId) return null;

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Your chess weaknesses</h1>
          <p className="text-slate-500 text-sm mt-1">
            Patterns are detected across all analyzed games.
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={handleStartOver}>
          Start over
        </Button>
      </div>

      {jobId && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Analysis in progress</CardTitle>
          </CardHeader>
          <CardContent>
            <AnalysisProgress jobId={jobId} userId={userId} />
          </CardContent>
        </Card>
      )}

      {/* Patterns — populated in Week 3 */}
      <div className="grid gap-4">
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <p className="text-sm">
              {jobId
                ? "Patterns will appear here once analysis completes."
                : "No patterns yet — trigger a new analysis to get started."}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen text-slate-400 text-sm">Loading…</div>}>
      <DashboardContent />
    </Suspense>
  );
}
