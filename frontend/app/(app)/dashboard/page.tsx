"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type JobStatus } from "@/lib/api";

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

function AnalysisProgress({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<JobStatus | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      while (!cancelled) {
        try {
          const j = await api.getJob(jobId);
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
  }, [jobId]);

  if (!job) return <p className="text-sm text-slate-500">Starting analysis…</p>;

  const statusLabel: Record<string, string> = {
    queued: "Queued",
    running: "Analyzing",
    done: "Complete",
    failed: "Failed",
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Badge variant={job.status === "done" ? "success" : job.status === "failed" ? "destructive" : "secondary"}>
          {statusLabel[job.status] ?? job.status}
        </Badge>
        <span className="text-sm text-slate-600">
          {job.status === "running"
            ? `Analyzed ${job.games_done} of ${job.games_total} games`
            : job.status === "done"
            ? `Analyzed ${job.games_total} games — ${job.positions_analyzed} positions`
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
          {job.cache_hits > 0 &&
            `${job.cache_hits} positions served from cache — `}
          This takes 3–8 minutes for 200 games.
        </p>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const params = useSearchParams();
  const jobId = params.get("job_id");

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Your chess weaknesses</h1>
        <p className="text-slate-500 text-sm mt-1">
          Patterns are computed across all your analyzed games.
        </p>
      </div>

      {jobId && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Analysis in progress</CardTitle>
          </CardHeader>
          <CardContent>
            <AnalysisProgress jobId={jobId} />
          </CardContent>
        </Card>
      )}

      {/* Patterns placeholder — populated in Week 3 */}
      <div className="grid gap-4">
        {!jobId && (
          <Card>
            <CardContent className="py-12 text-center text-slate-400">
              <p className="text-sm">
                No patterns yet. Run an analysis to get started.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
