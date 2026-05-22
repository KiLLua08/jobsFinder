"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "../lib/api";
import type { ScrapeJob } from "../lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Play, Loader2, CheckCircle, XCircle, Clock, AlertCircle, Zap } from "lucide-react";

// ── Constants ────────────────────────────────────────────────────────────────

const POLL_INTERVAL_MS = 3_000;
const POLL_TIMEOUT_MS = 10 * 60 * 1_000; // 10 minutes

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatElapsed(ms: number): string {
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}m ${rem}s`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

function statusBadgeVariant(
  status: ScrapeJob["status"]
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "completed":
      return "default";
    case "failed":
      return "destructive";
    case "running":
    case "pending":
      return "secondary";
    default:
      return "outline";
  }
}

function statusLabel(status: ScrapeJob["status"]): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

// ── Sub-components ───────────────────────────────────────────────────────────

function HistoryRow({ job }: { job: ScrapeJob }) {
  const isActive = job.status === "running" || job.status === "pending";
  return (
    <tr className={`border-b last:border-0 text-sm ${isActive ? "bg-indigo-50" : ""}`}>
      <td className="py-2 pr-4 font-medium truncate max-w-[160px]">{job.query}</td>
      <td className="py-2 pr-4 capitalize">{job.site}</td>
      <td className="py-2 pr-4">
        <Badge variant={statusBadgeVariant(job.status)}>{statusLabel(job.status)}</Badge>
      </td>
      <td className="py-2 pr-4 text-slate-600">
        {job.jobs_found !== null ? job.jobs_found : "—"}
      </td>
      <td className="py-2 text-slate-500">{formatDate(job.finished_at)}</td>
    </tr>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

type PageState = "idle" | "polling" | "done" | "timeout";

export default function ScrapePage() {
  // Form state
  const [query, setQuery] = useState("Software Engineer");
  const [site, setSite] = useState("linkedin");
  const [pages, setPages] = useState("3");
  const [fastMode, setFastMode] = useState(false);

  // Page state machine
  const [pageState, setPageState] = useState<PageState>("idle");
  const [currentJob, setCurrentJob] = useState<ScrapeJob | null>(null);
  const [error, setError] = useState("");
  const [conflictMessage, setConflictMessage] = useState("");

  // Elapsed time
  const [elapsedMs, setElapsedMs] = useState(0);
  const pollStartRef = useRef<number | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const elapsedIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // History
  const [history, setHistory] = useState<ScrapeJob[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  // ── Load history on mount ──────────────────────────────────────────────────
  useEffect(() => {
    api.scrape
      .history()
      .then((jobs) => setHistory(jobs))
      .catch(() => {/* silently ignore history load errors */})
      .finally(() => setHistoryLoading(false));
  }, []);

  // ── Cleanup on unmount ────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Polling helpers ───────────────────────────────────────────────────────
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (elapsedIntervalRef.current) {
      clearInterval(elapsedIntervalRef.current);
      elapsedIntervalRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (jobId: number) => {
      pollStartRef.current = Date.now();
      setElapsedMs(0);

      // Elapsed time ticker
      elapsedIntervalRef.current = setInterval(() => {
        if (pollStartRef.current !== null) {
          setElapsedMs(Date.now() - pollStartRef.current);
        }
      }, 500);

      // Poll for status
      intervalRef.current = setInterval(async () => {
        try {
          const job = await api.scrape.status(jobId);
          setCurrentJob(job);
          // Update history entry in-place
          setHistory((prev) =>
            prev.map((h) => (h.id === job.id ? job : h))
          );
          if (job.status === "completed" || job.status === "failed") {
            stopPolling();
            setPageState("done");
          }
        } catch {
          // Network error — keep polling; timeout will handle persistent failures
        }
      }, POLL_INTERVAL_MS);

      // Hard timeout
      timeoutRef.current = setTimeout(() => {
        stopPolling();
        setPageState("timeout");
      }, POLL_TIMEOUT_MS);
    },
    [stopPolling]
  );

  // ── Submit handler ────────────────────────────────────────────────────────
  async function handleScrape() {
    setError("");
    setConflictMessage("");
    setCurrentJob(null);

    try {
      const job = await api.scrape.trigger(query.trim(), site, parseInt(pages, 10) || 3, !fastMode);
      setCurrentJob(job);
      // Prepend to history
      setHistory((prev) => [job, ...prev.slice(0, 19)]);
      setPageState("polling");
      startPolling(job.id);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Scrape request failed";
      // Detect 409 conflict
      if (message.includes("409")) {
        setConflictMessage("A scrape is already running. Wait for it to finish before starting a new one.");
      } else {
        setError(message);
      }
    }
  }

  const isPolling = pageState === "polling";
  const formDisabled = isPolling;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-2xl space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Play className="h-6 w-6 text-indigo-600" />
          Run Scraper
        </h1>
        <p className="text-slate-500">
          Triggers a background scrape job on the server. New jobs appear in the Jobs page once
          complete.
        </p>
      </div>

      {/* Form */}
      <Card>
        <CardContent className="p-5 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Search Query</label>
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Data Scientist"
              disabled={formDisabled}
            />
          </div>

          <div className="flex gap-3">
            <div className="space-y-2 flex-1">
              <label className="text-sm font-medium">Site</label>
              <Select
                value={site}
                onValueChange={(v) => setSite(v ?? "linkedin")}
                disabled={formDisabled}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="linkedin">LinkedIn</SelectItem>
                  <SelectItem value="indeed">Indeed</SelectItem>
                  <SelectItem value="all">Both</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 w-24">
              <label className="text-sm font-medium">Pages</label>
              <Input
                type="number"
                min={1}
                max={10}
                value={pages}
                onChange={(e) => setPages(e.target.value)}
                disabled={formDisabled}
              />
            </div>
          </div>

          <Button
            onClick={handleScrape}
            disabled={formDisabled || !query.trim()}
            className="gap-2 cursor-pointer"
          >
            {isPolling ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Scraping…
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Start Scraping
              </>
            )}
          </Button>

          {/* Fast mode toggle */}
          <div className="flex items-center gap-3 pt-1">
            <button
              type="button"
              onClick={() => setFastMode((v) => !v)}
              disabled={formDisabled}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none ${
                fastMode ? "bg-amber-400" : "bg-slate-200"
              } disabled:opacity-50`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                  fastMode ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
            <div>
              <span className="text-sm font-medium flex items-center gap-1">
                <Zap className={`h-3.5 w-3.5 ${fastMode ? "text-amber-500" : "text-slate-400"}`} />
                Fast mode
              </span>
              <p className="text-xs text-slate-400">
                {fastMode
                  ? "Titles & companies only (~30s). ML won't classify these jobs."
                  : "Full descriptions (~5–15 min). Required for ML classification."}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Conflict message (409) */}
      {conflictMessage && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-5 flex items-center gap-3 text-amber-800">
            <AlertCircle className="h-5 w-5 shrink-0" />
            {conflictMessage}
          </CardContent>
        </Card>
      )}

      {/* Generic error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-5 flex items-center gap-3 text-red-700">
            <XCircle className="h-5 w-5 shrink-0" />
            {error}
          </CardContent>
        </Card>
      )}

      {/* Progress card (polling) */}
      {isPolling && currentJob && (
        <Card className="border-indigo-200 bg-indigo-50">
          <CardContent className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-medium text-indigo-800">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Scraping in progress</span>
              </div>
              <Badge variant="secondary">{statusLabel(currentJob.status)}</Badge>
            </div>
            <p className="text-sm text-indigo-700">
              Searching <strong>{currentJob.query}</strong> on{" "}
              <strong>{currentJob.site}</strong> ({currentJob.pages} pages)
            </p>
            <div className="flex items-center gap-1 text-sm text-indigo-600">
              <Clock className="h-4 w-4" />
              Elapsed: {formatElapsed(elapsedMs)}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Completed result */}
      {pageState === "done" && currentJob?.status === "completed" && (
        <Card className="border-emerald-200 bg-emerald-50">
          <CardContent className="p-5 space-y-1 text-emerald-800">
            <div className="flex items-center gap-2 font-medium">
              <CheckCircle className="h-5 w-5" />
              Scrape complete!
            </div>
            <p className="text-sm">
              Found <strong>{currentJob.jobs_found ?? 0}</strong> new jobs for{" "}
              <strong>{currentJob.query}</strong> on <strong>{currentJob.site}</strong>.
              Total time: {formatElapsed(elapsedMs)}.
            </p>
            <p className="text-sm">
              Check the <a href="/jobs" className="underline">Jobs page</a> for new listings.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Failed result */}
      {pageState === "done" && currentJob?.status === "failed" && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-5 space-y-1 text-red-700">
            <div className="flex items-center gap-2 font-medium">
              <XCircle className="h-5 w-5" />
              Scrape failed
            </div>
            <p className="text-sm">
              {currentJob.error_message ?? "An unknown error occurred."}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Timeout */}
      {pageState === "timeout" && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-5 flex items-center gap-3 text-amber-800">
            <Clock className="h-5 w-5 shrink-0" />
            The scrape job is taking longer than expected (10 min timeout). It may still be
            running in the background — check the history below.
          </CardContent>
        </Card>
      )}

      {/* Scrape history */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Recent Scrape Jobs</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {historyLoading ? (
            <p className="p-5 text-sm text-slate-500">Loading history…</p>
          ) : history.length === 0 ? (
            <p className="p-5 text-sm text-slate-500">No scrape jobs yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-slate-50 text-slate-600 text-xs uppercase tracking-wide">
                    <th className="py-2 px-4 text-left font-medium">Query</th>
                    <th className="py-2 pr-4 text-left font-medium">Site</th>
                    <th className="py-2 pr-4 text-left font-medium">Status</th>
                    <th className="py-2 pr-4 text-left font-medium">Jobs</th>
                    <th className="py-2 pr-4 text-left font-medium">Finished</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {history.map((job) => (
                    <HistoryRow key={job.id} job={job} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
