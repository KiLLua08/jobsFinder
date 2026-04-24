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
      return fetchAPI<any[]>(`/api/jobs/?${query.toString()}`);
    },
    get: (id: number) => fetchAPI<any>(`/api/jobs/${id}/`),
    label: (id: number, isRelevant: boolean) =>
      fetchAPI<any>(`/api/jobs/${id}/label/`, {
        method: "POST",
        body: JSON.stringify({ is_relevant: isRelevant }),
      }),
    unlabeled: () => fetchAPI<any[]>("/api/jobs/unlabeled/"),
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
