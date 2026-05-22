"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Activity, Database, CheckCircle, Filter,
  BrainCircuit, AlertTriangle, RefreshCw, Zap, Loader2,
} from "lucide-react";

function StatCard({
  title, value, icon: Icon, sub,
}: {
  title: string; value: string | number; icon: React.ComponentType<{ className?: string }>; sub?: string;
}) {
  return (
    <Card>
      <CardContent className="p-5 flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm text-slate-500">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {sub && <p className="text-xs text-slate-400">{sub}</p>}
        </div>
        <div className="p-2 bg-slate-100 rounded-lg">
          <Icon className="h-5 w-5 text-slate-600" />
        </div>
      </CardContent>
    </Card>
  );
}

function StatusDot({ active }: { active?: boolean }) {
  return (
    <span className={`inline-block h-2.5 w-2.5 rounded-full ${active ? "bg-emerald-500" : "bg-slate-300"}`} />
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);
  const [batchResult, setBatchResult] = useState<any>(null);
  const [batchError, setBatchError] = useState("");

  const load = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([api.ml.stats(), api.ml.health()]);
      setStats(s);
      setHealth(h);
      setError("");
    } catch (e: any) {
      setError(e.message || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10_000);
    return () => clearInterval(interval);
  }, [load]);

  async function handleProcessBatch() {
    setProcessing(true);
    setBatchResult(null);
    setBatchError("");
    try {
      const result = await api.ml.processBatch(50);
      setBatchResult(result);
      await load(); // refresh stats immediately after
    } catch (e: any) {
      setBatchError(e.message || "Batch processing failed");
    } finally {
      setProcessing(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 w-full" />)}
        </div>
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-5 flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const unprocessed = (stats?.total ?? 0) - (stats?.processed ?? 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Button variant="outline" size="sm" onClick={load} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Jobs" value={stats?.total ?? 0} icon={Database} />
        <StatCard title="Processed" value={stats?.processed ?? 0} icon={CheckCircle} />
        <StatCard title="Relevant" value={stats?.relevant ?? 0} icon={Filter} />
        <StatCard
          title="Completion"
          value={`${stats?.percentage ?? 0}%`}
          icon={Activity}
          sub={`${stats?.processed ?? 0} / ${stats?.total ?? 0} analyzed`}
        />
      </div>

      {/* Progress bar */}
      {(stats?.total ?? 0) > 0 && (
        <Card>
          <CardContent className="p-5 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium">ML Processing Progress</span>
              <span className="text-slate-500">{stats?.percentage ?? 0}%</span>
            </div>
            <Progress value={stats?.percentage ?? 0} className="h-2" />
            {unprocessed > 0 && (
              <p className="text-xs text-slate-400">{unprocessed} jobs still need processing</p>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ML Pipeline Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BrainCircuit className="h-5 w-5 text-indigo-600" />
              ML Pipeline Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "Classifier", active: health?.classifier_loaded },
              { label: "NER Model", active: health?.ner_loaded },
              { label: "Model Cache", active: health?.cache_initialized },
            ].map(({ label, active }) => (
              <div key={label} className="flex items-center gap-3">
                <StatusDot active={active} />
                <span className="text-sm flex-1">{label}</span>
                <span className={`text-xs font-medium ${active ? "text-emerald-600" : "text-slate-400"}`}>
                  {active ? "Ready" : "Not loaded"}
                </span>
              </div>
            ))}
            {health?.active_model && (
              <div className="mt-3 pt-3 border-t border-slate-100 space-y-1">
                <p className="text-xs font-medium text-slate-500">Fine-tuned model active</p>
                <p className="text-xs text-slate-700">{health.active_model.name}</p>
                <div className="flex gap-3 text-xs text-slate-500">
                  {health.active_model.accuracy != null && (
                    <span>Acc: <strong>{(health.active_model.accuracy * 100).toFixed(1)}%</strong></span>
                  )}
                  {health.active_model.f1_score != null && (
                    <span>F1: <strong>{(health.active_model.f1_score * 100).toFixed(1)}%</strong></span>
                  )}
                  {health.active_model.training_date && (
                    <span>Trained: <strong>{new Date(health.active_model.training_date).toLocaleDateString()}</strong></span>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Process Batch */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-5 w-5 text-indigo-600" />
              Run ML Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-500">
              Process up to 50 unprocessed jobs through the relevance classifier and skills extractor.
            </p>
            <Button
              onClick={handleProcessBatch}
              disabled={processing || unprocessed === 0}
              className="gap-2 w-full"
            >
              {processing ? (
                <><Loader2 className="h-4 w-4 animate-spin" />Processing...</>
              ) : (
                <><Zap className="h-4 w-4" />Process Next 50 Jobs</>
              )}
            </Button>
            {unprocessed === 0 && !processing && (
              <p className="text-xs text-emerald-600 text-center">✓ All jobs are processed</p>
            )}
            {batchError && (
              <p className="text-xs text-red-600 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" /> {batchError}
              </p>
            )}
            {batchResult && (
              <div className="rounded-md bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800 space-y-1">
                <p className="font-medium">Batch complete!</p>
                <p>✓ {batchResult.successful} processed · {batchResult.relevant_count} relevant · {batchResult.failed} failed</p>
                <p className="text-emerald-600">Avg {batchResult.avg_processing_time_ms?.toFixed(0)}ms per job</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <a href="/classify" className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors">
            Try Classify Demo
          </a>
          <a href="/scrape" className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            Run Scraper
          </a>
          <a href="/label" className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            Label Jobs
          </a>
          <a href="/jobs" className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            Browse Jobs
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
