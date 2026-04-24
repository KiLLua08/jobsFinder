"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "../lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, ExternalLink, BrainCircuit } from "lucide-react";

interface Job {
  id: number;
  title: string;
  company: string;
  location: string | null;
  is_relevant: boolean | null;
  relevance_score: number | null;
  extracted_skills: string[];
  nlp_processed: boolean;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [relevantFilter, setRelevantFilter] = useState<string>("all");
  const [error, setError] = useState("");

  const loadJobs = useCallback(async () => {
    setLoading(true);
    try {
      const relevant = relevantFilter === "all" ? undefined : relevantFilter === "yes";
      const data = await api.jobs.list({ search: search || undefined, relevant });
      setJobs(data);
    } catch (e: any) {
      setError(e.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, [search, relevantFilter]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Job Listings</h1>
        <span className="text-sm text-slate-500">{jobs.length} jobs</span>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search jobs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={relevantFilter} onValueChange={setRelevantFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Filter" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="yes">Relevant</SelectItem>
            <SelectItem value="no">Irrelevant</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 text-red-700 text-sm">{error}</CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))
        ) : jobs.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-slate-500">
              No jobs found. Try scraping some first.
            </CardContent>
          </Card>
        ) : (
          jobs.map((job) => (
            <Card key={job.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex flex-col gap-2">
                <div className="flex items-start justify-between">
                  <div>
                    <Link
                      href={`/jobs/${job.id}`}
                      className="font-semibold text-indigo-700 hover:underline"
                    >
                      {job.title}
                    </Link>
                    <p className="text-sm text-slate-600">
                      {job.company} {job.location && `· ${job.location}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {job.nlp_processed && (
                      <RelevanceBadge isRelevant={job.is_relevant} score={job.relevance_score} />
                    )}
                    <a href={job.link} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4 text-slate-400 hover:text-slate-600" />
                    </a>
                  </div>
                </div>
                {job.extracted_skills && job.extracted_skills.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {job.extracted_skills.slice(0, 8).map((skill) => (
                      <Badge key={skill} variant="secondary" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                    {job.extracted_skills.length > 8 && (
                      <Badge variant="outline" className="text-xs">
                        +{job.extracted_skills.length - 8}
                      </Badge>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

function RelevanceBadge({
  isRelevant,
  score,
}: {
  isRelevant: boolean | null;
  score: number | null;
}) {
  if (isRelevant === null || isRelevant === undefined) {
    return (
      <Badge variant="outline" className="text-xs flex items-center gap-1">
        <BrainCircuit className="h-3 w-3" />
        Unprocessed
      </Badge>
    );
  }
  if (isRelevant) {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 text-xs">
        Relevant {score !== null ? `${Math.round(score * 100)}%` : ""}
      </Badge>
    );
  }
  return (
    <Badge variant="secondary" className="text-xs">
      Irrelevant {score !== null ? `${Math.round(score * 100)}%` : ""}
    </Badge>
  );
}
