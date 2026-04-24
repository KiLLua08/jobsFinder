"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { ThumbsUp, ThumbsDown, Tag } from "lucide-react";

export default function LabelPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    api.jobs
      .unlabeled()
      .then((data) => {
        setJobs(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message || "Failed to load jobs");
        setLoading(false);
      });
  }, []);

  async function vote(isRelevant: boolean) {
    const job = jobs[current];
    if (!job) return;
    try {
      await api.jobs.label(job.id, isRelevant);
      setCurrent((c) => c + 1);
    } catch (e: any) {
      alert(e.message);
    }
  }

  const job = jobs[current];
  const total = jobs.length;
  const done = current;
  const pct = total ? Math.round((done / total) * 100) : 0;

  if (loading) {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold">Label Jobs</h1>
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
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
            All jobs have been labeled. Great work!
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
          <CardContent className="p-8 text-center text-slate-500">
            <p className="text-lg font-semibold text-slate-700 mb-2">All done!</p>
            <p>You labeled {total} jobs. These will be used to train the ML model.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Label Jobs</h1>
        <span className="text-sm text-slate-500">
          {done} / {total} labeled
        </span>
      </div>

      <Progress value={pct} className="h-2" />

      <Card>
        <CardContent className="p-6 space-y-4">
          <div>
            <h2 className="text-xl font-semibold">{job.title}</h2>
            <p className="text-slate-600">
              {job.company} {job.location && `· ${job.location}`}
            </p>
          </div>

          {job.extracted_skills?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {job.extracted_skills.map((s: string) => (
                <Badge key={s} variant="secondary" className="flex items-center gap-1">
                  <Tag className="h-3 w-3" />
                  {s}
                </Badge>
              ))}
            </div>
          )}

          <div className="max-h-48 overflow-y-auto rounded-md bg-slate-50 p-3 text-sm text-slate-700">
            {job.description ? job.description.slice(0, 800) : "No description"}
            {job.description && job.description.length > 800 && "..."}
          </div>

          <div className="flex justify-center gap-4 pt-2">
            <Button
              variant="outline"
              size="lg"
              onClick={() => vote(false)}
              className="gap-2 border-red-200 hover:bg-red-50"
            >
              <ThumbsDown className="h-5 w-5" />
              Irrelevant
            </Button>
            <Button
              size="lg"
              onClick={() => vote(true)}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              <ThumbsUp className="h-5 w-5" />
              Relevant
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
