"use client";

import { useState } from "react";
import { api } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BrainCircuit, Sparkles, CheckCircle, XCircle } from "lucide-react";

export default function ClassifyPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleClassify() {
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
        </p>
      </div>

      <Card>
        <CardContent className="p-5 space-y-4">
          <Textarea
            placeholder="Paste a job description here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            className="resize-none"
          />
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">{text.length} characters</span>
            <Button onClick={handleClassify} disabled={loading || !text.trim()} className="gap-2">
              {loading ? (
                <>
                  <Sparkles className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Classify
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 flex items-center gap-2 text-red-700">
            <XCircle className="h-5 w-5" />
            {error}
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              Results
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">
                  {result.is_relevant ? "Relevant" : "Irrelevant"}
                </span>
                <span className="text-sm text-slate-500">
                  {Math.round((result.relevance_score || 0) * 100)}% confidence
                </span>
              </div>
              <Progress value={(result.relevance_score || 0) * 100} className="h-2" />
            </div>

            <div>
              <span className="text-sm font-medium mb-2 block">Extracted Skills</span>
              <div className="flex flex-wrap gap-2">
                {result.extracted_skills?.length ? (
                  result.extracted_skills.map((s: string) => (
                    <Badge key={s} variant="secondary">{s}</Badge>
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
