"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "../../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ExternalLink, ThumbsUp, ThumbsDown, BrainCircuit, Tag, ArrowLeft, CheckCircle } from "lucide-react";

export default function JobDetail() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [labelSaved, setLabelSaved] = useState(false);
  const [labeling, setLabeling] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.jobs.get(id)
      .then((data) => { setJob(data); setLoading(false); })
      .catch((e) => { setError(e.message || "Failed to load job"); setLoading(false); });
  }, [id]);

  async function label(isRelevant: boolean) {
    setLabeling(true);
    try {
      await api.jobs.label(id, isRelevant);
      setJob((prev: any) => ({ ...prev, is_relevant_human_label: isRelevant }));
      setLabelSaved(true);
      setTimeout(() => setLabelSaved(false), 3000);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLabeling(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <Card className="border-red-200 bg-red-50 max-w-3xl">
        <CardContent className="p-5 text-red-700">{error || "Job not found"}</CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-3xl space-y-5">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{job.title}</h1>
          <p className="text-slate-600 mt-0.5">
            {job.company}{job.location && ` · ${job.location}`}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Scraped {new Date(job.date_scraped).toLocaleDateString()}
          </p>
        </div>
        <a href={job.link} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm" className="gap-1 shrink-0">
            <ExternalLink className="h-4 w-4" />
            Apply
          </Button>
        </a>
      </div>

      {/* ML Analysis */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-indigo-600" />
            ML Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {job.nlp_processed ? (
            <>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">
                    {job.is_relevant ? "✓ Relevant" : "✗ Irrelevant"}
                  </span>
                  <span className="text-slate-500">
                    {Math.round((job.relevance_score || 0) * 100)}% confidence
                  </span>
                </div>
                <Progress value={(job.relevance_score || 0) * 100} className="h-2" />
              </div>
              {job.extracted_skills?.length > 0 && (
                <div>
                  <p className="text-sm font-medium flex items-center gap-1.5 mb-2">
                    <Tag className="h-3.5 w-3.5 text-indigo-600" /> Extracted Skills
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {job.extracted_skills.map((s: string) => (
                      <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-500">Not yet processed by ML pipeline.</p>
          )}
        </CardContent>
      </Card>

      {/* Description */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
            {job.description || "No description available."}
          </div>
        </CardContent>
      </Card>

      {/* Human Feedback */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Your Feedback</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-500">
            Is this job relevant to you? Your label helps train the ML model.
          </p>
          <div className="flex items-center gap-3">
            <Button
              variant={job.is_relevant_human_label === true ? "default" : "outline"}
              size="sm"
              onClick={() => label(true)}
              disabled={labeling}
              className={`gap-1.5 ${job.is_relevant_human_label === true ? "bg-emerald-600 hover:bg-emerald-700" : ""}`}
            >
              <ThumbsUp className="h-4 w-4" />
              Relevant
            </Button>
            <Button
              variant={job.is_relevant_human_label === false ? "destructive" : "outline"}
              size="sm"
              onClick={() => label(false)}
              disabled={labeling}
              className="gap-1.5"
            >
              <ThumbsDown className="h-4 w-4" />
              Irrelevant
            </Button>
            {labelSaved && (
              <span className="flex items-center gap-1 text-sm text-emerald-600 font-medium">
                <CheckCircle className="h-4 w-4" /> Saved!
              </span>
            )}
          </div>
          {job.is_relevant_human_label !== null && job.is_relevant_human_label !== undefined && !labelSaved && (
            <p className="text-xs text-slate-400">
              Currently labeled as: <strong>{job.is_relevant_human_label ? "Relevant" : "Irrelevant"}</strong>
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
