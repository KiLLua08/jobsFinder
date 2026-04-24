"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "../../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ExternalLink, ThumbsUp, ThumbsDown, BrainCircuit, Tag } from "lucide-react";

export default function JobDetail() {
  const params = useParams();
  const id = Number(params.id);
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api.jobs
      .get(id)
      .then((data) => {
        setJob(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message || "Failed to load job");
        setLoading(false);
      });
  }, [id]);

  async function label(isRelevant: boolean) {
    try {
      await api.jobs.label(id, isRelevant);
      setJob((prev: any) => ({ ...prev, is_relevant_human_label: isRelevant }));
    } catch (e: any) {
      alert(e.message);
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-5 text-red-700">{error || "Job not found"}</CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{job.title}</h1>
          <p className="text-slate-600">
            {job.company} {job.location && `· ${job.location}`}
          </p>
        </div>
        <a href={job.link} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm" className="gap-1">
            <ExternalLink className="h-4 w-4" />
            Apply
          </Button>
        </a>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-indigo-600" />
            ML Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {job.nlp_processed ? (
            <>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium">Relevance:</span>
                {job.is_relevant ? (
                  <Badge className="bg-emerald-100 text-emerald-700">
                    Relevant ({Math.round((job.relevance_score || 0) * 100)}%)
                  </Badge>
                ) : (
                  <Badge variant="secondary">Irrelevant ({Math.round((job.relevance_score || 0) * 100)}%)</Badge>
                )}
              </div>
              <div>
                <span className="text-sm font-medium flex items-center gap-2 mb-2">
                  <Tag className="h-4 w-4 text-indigo-600" />
                  Extracted Skills
                </span>
                <div className="flex flex-wrap gap-2">
                  {job.extracted_skills?.length ? (
                    job.extracted_skills.map((s: string) => (
                      <Badge key={s} variant="secondary">{s}</Badge>
                    ))
                  ) : (
                    <span className="text-sm text-slate-400">No skills detected</span>
                  )}
                </div>
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">Not yet processed by ML pipeline.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
            {job.description || "No description available."}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Human Feedback</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-500">
            Is this job relevant? Your feedback helps train the ML model.
          </p>
          <div className="flex gap-3">
            <Button
              variant={job.is_relevant_human_label === true ? "default" : "outline"}
              size="sm"
              onClick={() => label(true)}
              className="gap-1"
            >
              <ThumbsUp className="h-4 w-4" />
              Relevant
            </Button>
            <Button
              variant={job.is_relevant_human_label === false ? "destructive" : "outline"}
              size="sm"
              onClick={() => label(false)}
              className="gap-1"
            >
              <ThumbsDown className="h-4 w-4" />
              Irrelevant
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
