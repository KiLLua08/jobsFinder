"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { ThumbsUp, ThumbsDown, Tag, ChevronDown, ChevronUp, SkipForward, ExternalLink } from "lucide-react";

export default function LabelPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState(0);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState<{ jobId: number; label: boolean }[]>([]);

  useEffect(() => {
    api.jobs.unlabeled()
      .then((data) => { setJobs(data); setLoading(false); })
      .catch((e) => { setError(e.message || "Failed to load jobs"); setLoading(false); });
  }, []);

  // Keyboard shortcuts: Y = relevant, N = irrelevant, S = skip
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
      if (e.key === "y" || e.key === "Y") vote(true);
      if (e.key === "n" || e.key === "N") vote(false);
      if (e.key === "s" || e.key === "S") skip();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  async function vote(isRelevant: boolean) {
    const job = jobs[current];
    if (!job || submitting) return;
    setSubmitting(true);
    try {
      await api.jobs.label(job.id, isRelevant);
      setHistory((h) => [...h, { jobId: job.id, label: isRelevant }]);
      setCurrent((c) => c + 1);
      setExpanded(false);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  function skip() {
    if (current >= jobs.length - 1) return;
    setCurrent((c) => c + 1);
    setExpanded(false);
  }

  const job = jobs[current];
  const total = jobs.length;
  const done = current;
  const pct = total ? Math.round((done / total) * 100) : 0;

  if (loading) {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold">Label Jobs</h1>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50 max-w-2xl">
        <CardContent className="p-5 text-red-700">{error}</CardContent>
      </Card>
    );
  }

  if (total === 0) {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold">Label Jobs</h1>
        <Card>
          <CardContent className="p-8 text-center text-slate-500">
            All jobs have been labeled. Great work! 🎉
          </CardContent>
        </Card>
      </div>
    );
  }

  if (current >= total) {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold">Label Jobs</h1>
        <Card>
          <CardContent className="p-8 text-center space-y-3">
            <p className="text-lg font-semibold text-slate-700">Session complete! 🎉</p>
            <p className="text-slate-500">You labeled {history.length} jobs this session.</p>
            <p className="text-sm text-slate-400">
              {history.filter((h) => h.label).length} relevant ·{" "}
              {history.filter((h) => !h.label).length} irrelevant
            </p>
            <Button onClick={() => { setCurrent(0); setHistory([]); }} variant="outline" className="mt-2">
              Start Over
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Label Jobs</h1>
        <span className="text-sm text-slate-500">{done} / {total} labeled</span>
      </div>

      <Progress value={pct} className="h-2" />

      <Card>
        <CardContent className="p-6 space-y-4">
          {/* Job header */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold leading-tight">{job.title}</h2>
              <p className="text-slate-600 text-sm">
                {job.company}{job.location && ` · ${job.location}`}
              </p>
            </div>
            <a href={job.link} target="_blank" rel="noopener noreferrer" title="Open original posting">
              <ExternalLink className="h-4 w-4 text-slate-400 hover:text-indigo-600 mt-1 shrink-0" />
            </a>
          </div>

          {/* Skills */}
          {job.extracted_skills?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {job.extracted_skills.map((s: string) => (
                <Badge key={s} variant="secondary" className="text-xs flex items-center gap-1">
                  <Tag className="h-2.5 w-2.5" />{s}
                </Badge>
              ))}
            </div>
          )}

          {/* Description */}
          {job.description ? (
            <div>
              <div className={`rounded-md bg-slate-50 p-3 text-sm text-slate-700 overflow-hidden transition-all ${expanded ? "" : "max-h-36"}`}>
                <p className="whitespace-pre-wrap">{job.description}</p>
              </div>
              {job.description.length > 300 && (
                <button
                  onClick={() => setExpanded((e) => !e)}
                  className="mt-1 text-xs text-indigo-600 hover:underline flex items-center gap-1"
                >
                  {expanded ? <><ChevronUp className="h-3 w-3" />Show less</> : <><ChevronDown className="h-3 w-3" />Show more</>}
                </button>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic">No description available</p>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={skip}
              disabled={submitting || current >= total - 1}
              className="gap-1.5 text-slate-500"
            >
              <SkipForward className="h-4 w-4" /> Skip
            </Button>
            <div className="flex gap-3">
              <Button
                variant="outline"
                size="lg"
                onClick={() => vote(false)}
                disabled={submitting}
                className="gap-2 border-red-200 hover:bg-red-50 hover:text-red-700"
              >
                <ThumbsDown className="h-5 w-5" />
                Irrelevant
                <kbd className="ml-1 text-xs opacity-50 hidden sm:inline">N</kbd>
              </Button>
              <Button
                size="lg"
                onClick={() => vote(true)}
                disabled={submitting}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700"
              >
                <ThumbsUp className="h-5 w-5" />
                Relevant
                <kbd className="ml-1 text-xs opacity-50 hidden sm:inline">Y</kbd>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <p className="text-xs text-center text-slate-400">
        Keyboard: <kbd className="px-1 bg-slate-100 border rounded">Y</kbd> relevant ·{" "}
        <kbd className="px-1 bg-slate-100 border rounded">N</kbd> irrelevant ·{" "}
        <kbd className="px-1 bg-slate-100 border rounded">S</kbd> skip
      </p>
    </div>
  );
}
