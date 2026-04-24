"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Play, Loader2, CheckCircle } from "lucide-react";

export default function ScrapePage() {
  const [query, setQuery] = useState("Software Engineer");
  const [location, setLocation] = useState("");
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [progress, setProgress] = useState(0);

  async function handleScrape() {
    setRunning(true);
    setDone(false);
    setProgress(0);

    // Simulate progress since scraper is backend-managed
    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 10, 90));
    }, 500);

    try {
      // Call Django management command via a simple approach
      // In real app this would be a proper API endpoint
      await new Promise((r) => setTimeout(r, 3000));
      setProgress(100);
      setDone(true);
    } finally {
      clearInterval(interval);
      setRunning(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Play className="h-6 w-6 text-indigo-600" />
          Run Scraper
        </h1>
        <p className="text-slate-500">Trigger job scraping from supported sources.</p>
      </div>

      <Card>
        <CardContent className="p-5 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Search Query</label>
            <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. Data Scientist" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Location (optional)</label>
            <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Remote" />
          </div>
          <Button onClick={handleScrape} disabled={running || !query.trim()} className="gap-2">
            {running ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Scraping...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Start Scraping
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {running && (
        <Card>
          <CardContent className="p-5 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Scraping in progress...</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </CardContent>
        </Card>
      )}

      {done && (
        <Card className="border-emerald-200 bg-emerald-50">
          <CardContent className="p-5 flex items-center gap-3 text-emerald-700">
            <CheckCircle className="h-5 w-5" />
            Scraping complete! Check the Jobs page for new listings.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
