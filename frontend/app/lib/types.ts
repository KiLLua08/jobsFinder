export interface ScrapeJob {
  id: number;
  status: "pending" | "running" | "completed" | "failed";
  query: string;
  site: string;
  pages: number;
  jobs_found: number | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface JobListing {
  id: number;
  title: string;
  company: string;
  description: string;
  location: string | null;
  link: string;
  date_scraped: string;
  is_relevant: boolean | null;
  relevance_score: number | null;
  extracted_skills: string[];
  nlp_processed: boolean;
  is_relevant_human_label: boolean | null;
}

export interface MLStats {
  total: number;
  processed: number;
  relevant: number;
  percentage: number;
}

export interface MLHealth {
  status: string;
  cache_initialized: boolean;
  classifier_loaded: boolean;
  ner_loaded: boolean;
}

export interface ClassifyResponse {
  is_relevant: boolean;
  relevance_score: number;
  extracted_skills: string[];
}

export interface BatchResponse {
  total: number;
  processed: number;
  successful: number;
  failed: number;
  relevant_count: number;
  avg_processing_time_ms: number;
}
