import type { ScrapeJob } from "./types";

// In Docker the browser always accesses the app via localhost.
// Django runs on port 8000, accessible directly from the browser.
// NEXT_PUBLIC_ vars are embedded at build time and available in the browser.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  jobs: {
    list: (params?: { search?: string; skill?: string; relevant?: boolean; page?: number }) => {
      const query = new URLSearchParams();
      if (params?.search) query.set("search", params.search);
      if (params?.skill) query.set("skill", params.skill);
      if (params?.relevant !== undefined) query.set("relevant", String(params.relevant));
      if (params?.page) query.set("page", String(params.page));
      return fetchAPI<{ results: any[]; total: number; page: number; page_size: number; total_pages: number }>(`/api/jobs/?${query.toString()}`);
    },
    get: (id: number) => fetchAPI<any>(`/api/jobs/${id}/`),
    label: (id: number, isRelevant: boolean) =>
      fetchAPI<any>(`/api/jobs/${id}/label/`, {
        method: "POST",
        body: JSON.stringify({ is_relevant: isRelevant }),
      }),
    unlabeled: () => fetchAPI<any[]>("/api/jobs/unlabeled/"),
  },
  scrape: {
    trigger: (query: string, site: string = "linkedin", pages: number = 3, enrich: boolean = true) =>
      fetchAPI<ScrapeJob>("/api/scrape/", {
        method: "POST",
        body: JSON.stringify({ query, site, pages, enrich }),
      }),
    status: (id: number) =>
      fetchAPI<ScrapeJob>(`/api/scrape/${id}/status/`),
    history: () =>
      fetchAPI<ScrapeJob[]>("/api/scrape/"),
  },
  ml: {
    stats: () => fetchAPI<any>("/api/ml/stats/"),
    health: () => fetchAPI<any>("/api/ml/health/"),
    classify: (description: string) =>
      fetchAPI<any>("/api/ml/classify/", {
        method: "POST",
        body: JSON.stringify({ description }),
      }),
    processBatch: (limit?: number) =>
      fetchAPI<any>("/api/ml/process-batch/", {
        method: "POST",
        body: JSON.stringify(limit ? { limit } : {}),
      }),
  },
};
