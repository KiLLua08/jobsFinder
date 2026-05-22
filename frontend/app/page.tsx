"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "./lib/api";
import { Briefcase, Search, BrainCircuit, ArrowRight, Database, CheckCircle, Filter, Activity } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function Home() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    api.ml.stats().then(setStats).catch(() => null);
  }, []);

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight">Welcome to JobsFinder</h1>
        <p className="text-slate-500 text-lg">
          AI-powered job aggregation that scrapes listings and classifies relevance using deep learning.
        </p>
      </div>

      {/* Live stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Total Jobs", value: stats?.total, icon: Database },
          { label: "Processed", value: stats?.processed, icon: CheckCircle },
          { label: "Relevant", value: stats?.relevant, icon: Filter },
          { label: "Completion", value: stats ? `${stats.percentage}%` : undefined, icon: Activity },
        ].map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="p-4 flex items-center gap-3">
              <Icon className="h-5 w-5 text-indigo-500 shrink-0" />
              <div>
                <p className="text-xs text-slate-500">{label}</p>
                {value !== undefined ? (
                  <p className="text-xl font-bold">{value}</p>
                ) : (
                  <Skeleton className="h-6 w-10 mt-0.5" />
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link href="/scrape">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full border-indigo-100">
            <CardContent className="p-5 space-y-3">
              <div className="p-2 bg-indigo-50 rounded-lg w-fit">
                <Search className="h-5 w-5 text-indigo-600" />
              </div>
              <h3 className="font-semibold">Scrape Jobs</h3>
              <p className="text-sm text-slate-500">
                Trigger a live scrape from LinkedIn or Indeed with one click.
              </p>
              <div className="flex items-center text-sm text-indigo-600 font-medium">
                Start scraping <ArrowRight className="h-4 w-4 ml-1" />
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/jobs">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="p-5 space-y-3">
              <div className="p-2 bg-slate-100 rounded-lg w-fit">
                <Briefcase className="h-5 w-5 text-slate-600" />
              </div>
              <h3 className="font-semibold">Browse Jobs</h3>
              <p className="text-sm text-slate-500">
                Search and filter job listings with ML-powered relevance scoring.
              </p>
              <div className="flex items-center text-sm text-indigo-600 font-medium">
                Explore <ArrowRight className="h-4 w-4 ml-1" />
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/classify">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="p-5 space-y-3">
              <div className="p-2 bg-slate-100 rounded-lg w-fit">
                <BrainCircuit className="h-5 w-5 text-slate-600" />
              </div>
              <h3 className="font-semibold">ML Demo</h3>
              <p className="text-sm text-slate-500">
                Paste any job description and see the AI classify it instantly.
              </p>
              <div className="flex items-center text-sm text-indigo-600 font-medium">
                Try it <ArrowRight className="h-4 w-4 ml-1" />
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
