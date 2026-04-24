import Link from "next/link";
import { Briefcase, Search, BrainCircuit, ArrowRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight">Welcome to JobsFinder</h1>
        <p className="text-slate-500 text-lg">
          AI-powered job aggregation that scrapes listings and classifies relevance using deep learning.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link href="/jobs">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="p-5 space-y-3">
              <Search className="h-6 w-6 text-indigo-600" />
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

        <Link href="/dashboard">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="p-5 space-y-3">
              <Briefcase className="h-6 w-6 text-indigo-600" />
              <h3 className="font-semibold">Dashboard</h3>
              <p className="text-sm text-slate-500">
                View system stats, pipeline status, and insights.
              </p>
              <div className="flex items-center text-sm text-indigo-600 font-medium">
                View stats <ArrowRight className="h-4 w-4 ml-1" />
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/classify">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="p-5 space-y-3">
              <BrainCircuit className="h-6 w-6 text-indigo-600" />
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
