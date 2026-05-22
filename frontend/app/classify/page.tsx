"use client";

import { useState, useCallback } from "react";
import { api } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BrainCircuit, Sparkles, CheckCircle, XCircle, X } from "lucide-react";

const EXAMPLE = `We are looking for a Senior Python Developer to join our data engineering team.

Requirements:
- 3+ years of Python experience
- Strong knowledge of Django or FastAPI
- Experience with PostgreSQL and Redis
- Familiarity with Docker and Kubernetes
- AWS or GCP cloud experience preferred
- Knowledge of Spark or Airflow is a plus`;

export default function ClassifyPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleClassify = useCallback(async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await api.ml.classify(text);
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Classification failed");
    } finally {
      setLoading(false);
    }
  }, [text]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleClassify();
    }
  }

  function handleClear() {
    setText("");
    setResult(null);
    setError("");
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <BrainCircuit className="h-6 w-6 text-indigo-600" />
          ML Classify Demo
        </h1>
        <p className="text-slate-500">
          Paste any job description to see the AI classify it and extract skills.
          Press <kbd className="px-1.5 py-0.5 text-xs bg-slate-100 border rounded">Ctrl+Enter</kbd> to classify.
        </p>
      </div>

      <Card>
        <CardContent className="p-5 space-y-3">
          <Textarea
            placeholder="Paste a job description here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={9}
            className="resize-none font-mono text-sm"
          />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">{text.length} chars</span>
              {text.length === 0 && (
                <button
                  onClick={() => setText(EXAMPLE)}
                  className="text-xs text-indigo-600 hover:underline"
                >
                  Load example
                </button>
              )}
            </div>
            <div className="flex gap-2">
              {text.length > 0 && (
                <Button variant="ghost" size="sm" onClick={handleClear} className="gap-1 text-slate-500">
                  <X className="h-3.5 w-3.5" /> Clear
                </Button>
              )}
              <Button onClick={handleClassify} disabled={loading || !text.trim()} className="gap-2">
                {loading ? (
                  <><Sparkles className="h-4 w-4 animate-spin" />Analyzing...</>
                ) : (
                  <><Sparkles className="h-4 w-4" />Classify</>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 flex items-center gap-2 text-red-700">
            <XCircle className="h-5 w-5 shrink-0" />
            {error}
          </CardContent>
        </Card>
      )}

      {result && (
        <Card className={result.is_relevant ? "border-emerald-200" : "border-slate-200"}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle className={`h-5 w-5 ${result.is_relevant ? "text-emerald-600" : "text-slate-400"}`} />
              {result.is_relevant ? "Relevant Job Posting" : "Not Relevant"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-600">Relevance confidence</span>
                <span className={`font-bold ${result.is_relevant ? "text-emerald-600" : "text-slate-500"}`}>
                  {Math.round((result.relevance_score || 0) * 100)}%
                </span>
              </div>
              <Progress
                value={(result.relevance_score || 0) * 100}
                className={`h-2.5 ${result.is_relevant ? "[&>div]:bg-emerald-500" : ""}`}
              />
            </div>

            <div>
              <p className="text-sm font-medium mb-2">
                Extracted Skills
                {result.extracted_skills?.length > 0 && (
                  <span className="ml-2 text-xs text-slate-400 font-normal">
                    ({result.extracted_skills.length} found)
                  </span>
                )}
              </p>
              <div className="flex flex-wrap gap-2">
                {result.extracted_skills?.length ? (
                  result.extracted_skills.map((s: string) => (
                    <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>
                  ))
                ) : (
                  <span className="text-sm text-slate-400">No skills detected</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
