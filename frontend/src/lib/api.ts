import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://openministry.live";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically attach auth token to every request if it exists
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// API functions
export const api = {
  // Health
  health: () => apiClient.get("/health"),

  // Statements
  getStatements: (params?: Record<string, string>) =>
    apiClient.get("/api/statements/", { params }),
  getStatementCount: (params?: Record<string, string>) =>
    apiClient.get("/api/statements/count", { params }),
  getTopics: () => apiClient.get("/api/statements/topics"),
  tagAllStatements: () => apiClient.post("/api/statements/tag-all"),

  // Ministers
  getMinisters: (activeOnly: boolean = true) =>
    apiClient.get("/api/ministers/", { params: { active_only: activeOnly } }),
  getMinister: (id: number) => apiClient.get(`/api/ministers/${id}/`),
  createMinister: (data: Record<string, unknown>) =>
    apiClient.post("/api/ministers/", data),
  updateMinister: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/api/ministers/${id}`, data),
  getMinisterStatements: (id: number, params?: Record<string, string>) =>
    apiClient.get(`/api/ministers/${id}/statements`, { params }),
  getMinisterStats: (id: number) => apiClient.get(`/api/ministers/${id}/stats`),

  // Sources
  getSources: () => apiClient.get("/api/sources/"),
  createSource: (data: Record<string, unknown>) =>
    apiClient.post("/api/sources/", data),
  updateSource: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/api/sources/${id}`, data),
  deleteSource: (id: number) => apiClient.delete(`/api/sources/${id}`),

  // Moderation
  getModerationQueue: (params?: Record<string, string>) =>
    apiClient.get("/api/moderation/queue", { params }),
  getModerationStats: () => apiClient.get("/api/moderation/stats/overview"),
  getStatementContext: (id: number) =>
    apiClient.get(`/api/moderation/${id}/context`),
  approveStatement: (id: number, notes?: string) =>
    apiClient.post(`/api/moderation/${id}/approve/`, { notes }),
  rejectStatement: (id: number, notes?: string) =>
    apiClient.post(`/api/moderation/${id}/reject/`, { notes }),
  reviewStatement: (id: number, data: Record<string, unknown>) =>
    apiClient.post(`/api/moderation/${id}/review/`, data),
  getStatementLogs: (id: number) =>
    apiClient.get(`/api/moderation/${id}/logs/`),
  updateStatement: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/api/statements/${id}/`, data),

  // Search
  search: (q: string, params?: Record<string, string>) =>
    apiClient.get("/api/search/", { params: { q, ...params } }),
  searchMinisters: (q: string) =>
    apiClient.get("/api/search/ministers/", { params: { q } }),
  getSearchSuggestions: (q: string) =>
    apiClient.get("/api/search/suggestions/", { params: { q } }),
};
