"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Activity, Database, CheckCircle, Filter, Clock, BrainCircuit, AlertTriangle } from "lucide-react";

function StatCard({
  title,
  value,
  icon: Icon,
  description,
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}) {
  return (
    <Card>
      <CardContent className="p-5 flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm text-slate-500">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {description && <p className="text-xs text-slate-400">{description}</p>}
        </div>
        <div className="p-2 bg-slate-100 rounded-lg">
          <Icon className="h-5 w-5 text-slate-600" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [s, h] = await Promise.all([api.ml.stats(), api.ml.health()]);
        setStats(s);
        setHealth(h);
      } catch (e: any) {
        setError(e.message || "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Jobs" value={stats?.total ?? 0} icon={Database} />
        <StatCard title="Processed" value={stats?.processed ?? 0} icon={CheckCircle} />
        <StatCard title="Relevant" value={stats?.relevant ?? 0} icon={Filter} />
        <StatCard
          title="Completion"
          value={`${stats?.percentage ?? 0}%`}
          icon={Activity}
          description={`${stats?.processed ?? 0} / ${stats?.total ?? 0} jobs analyzed`}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <BrainCircuit className="h-5 w-5 text-indigo-600" />
            ML Pipeline Status
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <StatusDot active={health?.classifier_loaded} />
            <span className="text-sm">Classifier</span>
            <span className="text-xs text-slate-400">{health?.classifier_loaded ? "Loaded" : "Not loaded"}</span>
          </div>
          <div className="flex items-center gap-4">
            <StatusDot active={health?.ner_loaded} />
            <span className="text-sm">NER Model</span>
            <span className="text-xs text-slate-400">{health?.ner_loaded ? "Loaded" : "Not loaded"}</span>
          </div>
          <div className="flex items-center gap-4">
            <StatusDot active={health?.cache_initialized} />
            <span className="text-sm">Model Cache</span>
            <span className="text-xs text-slate-400">{health?.cache_initialized ? "Initialized" : "Not initialized"}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Clock className="h-5 w-5 text-indigo-600" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="flex gap-3">
          <a
            href="/classify"
            className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
          >
            Try Classify Demo
          </a>
          <a
            href="/scrape"
            className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Run Scraper
          </a>
          <a
            href="/label"
            className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Label Jobs
          </a>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusDot({ active }: { active?: boolean }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${
        active ? "bg-emerald-500" : "bg-slate-300"
      }`}
    />
  );
}
