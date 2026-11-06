
import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    "http://localhost:8000/api",

  headers: {
    "Content-Type": "application/json",
  },

  timeout: 30000,
});

// Analyze a new production incident
export const analyzeIncident = async (data) => {
  const response = await api.post("/analyze", data);
  return response.data;
};

// Get previous incidents
export const getIncidents = async () => {
  const response = await api.get("/incidents");
  return response.data;
};

// Save incident feedback
export const submitOutcome = async (data) => {
  const response = await api.post("/outcome", data);
  return response.data;
};

// Ask Hindsight to identify patterns
export const getLearnedPatterns = async (question) => {
  const response = await api.post("/reflect", {
    question,
  });

  return response.data;
};

// Check backend availability
export const checkBackend = async () => {
  const response = await api.get("/health");
  return response.data;
};

export default api;
