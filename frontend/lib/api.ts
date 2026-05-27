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
  getMinisters: () => apiClient.get("/api/ministers"),
  getMinister: (id: number) => apiClient.get(`/api/ministers/${id}`),
};
