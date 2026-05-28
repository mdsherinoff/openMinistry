import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    apiClient.get("/api/statements", { params }),

  // Ministers
  getMinisters: (activeOnly: boolean = true) =>
    apiClient.get("/api/ministers/", { params: { active_only: activeOnly } }),
  getMinister: (id: number) => apiClient.get(`/api/ministers/${id}`),
  createMinister: (data: Record<string, unknown>) =>
    apiClient.post("/api/ministers/", data),
  updateMinister: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/api/ministers/${id}`, data),

  // Sources
  getSources: () => apiClient.get("/api/sources/"),
  createSource: (data: Record<string, unknown>) =>
    apiClient.post("/api/sources/", data),
  updateSource: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/api/sources/${id}`, data),
  deleteSource: (id: number) => apiClient.delete(`/api/sources/${id}`),
};
