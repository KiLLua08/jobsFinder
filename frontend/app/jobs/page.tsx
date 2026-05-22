"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { api } from "../lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, ExternalLink, BrainCircuit, ChevronLeft, ChevronRight } from "lucide-react";

interface Job {
  id: number;
  title: string;
  company: string;
  location: string | null;
  link: string;
  is_relevant: boolean | null;
  relevance_score: number | null;
  extracted_skills: string[];
  nlp_processed: boolean;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [relevantFilter, setRelevantFilter] = useState<string>("all");
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce search input by 400ms
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(search), 400);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [search]);

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1); }, [debouncedSearch, relevantFilter]);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const relevant = relevantFilter === "all" ? undefined : relevantFilter === "yes";
      const data = await api.jobs.list({ search: debouncedSearch || undefined, relevant, page });
      setJobs(data.results);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (e: any) {
      setError(e.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, relevantFilter, page]);

  useEffect(() => { loadJobs(); }, [loadJobs]);

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Job Listings</h1>
        <span className="text-sm text-slate-500">{total} jobs</span>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search by title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={relevantFilter} onValueChange={(v) => setRelevantFilter(v ?? "all")}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Filter" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Jobs</SelectItem>
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
          Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-28 w-full" />)
        ) : jobs.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-slate-500">
              No jobs found.{" "}
              <Link href="/scrape" className="text-indigo-600 hover:underline">
                Try scraping some first.
              </Link>
            </CardContent>
          </Card>
        ) : (
          jobs.map((job) => (
            <Card key={job.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <Link
                      href={`/jobs/${job.id}`}
                      className="font-semibold text-indigo-700 hover:underline line-clamp-1"
                    >
                      {job.title}
                    </Link>
                    <p className="text-sm text-slate-600">
                      {job.company}{job.location && ` · ${job.location}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {job.nlp_processed && (
                      <RelevanceBadge isRelevant={job.is_relevant} score={job.relevance_score} />
                    )}
                    <a
                      href={job.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Open original posting"
                    >
                      <ExternalLink className="h-4 w-4 text-slate-400 hover:text-indigo-600 transition-colors" />
                    </a>
                  </div>
                </div>
                {job.extracted_skills?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {job.extracted_skills.slice(0, 8).map((skill) => (
                      <Badge key={skill} variant="secondary" className="text-xs">{skill}</Badge>
                    ))}
                    {job.extracted_skills.length > 8 && (
                      <Badge variant="outline" className="text-xs">+{job.extracted_skills.length - 8}</Badge>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" /> Prev
          </Button>
          <span className="text-sm text-slate-500 px-2">Page {page} of {totalPages}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages || loading}
            className="gap-1"
          >
            Next <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

function RelevanceBadge({ isRelevant, score }: { isRelevant: boolean | null; score: number | null }) {
  if (isRelevant === null || isRelevant === undefined) {
    return (
      <Badge variant="outline" className="text-xs flex items-center gap-1">
        <BrainCircuit className="h-3 w-3" /> Unprocessed
      </Badge>
    );
  }
  if (isRelevant) {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 text-xs border-0">
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
