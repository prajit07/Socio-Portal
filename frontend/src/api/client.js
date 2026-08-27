import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// Auth
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => api.post('/auth/login', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }),
  me: () => api.get('/auth/me'),
};

// Problems
export const problemsApi = {
  list: (params = {}) => api.get('/problems', { params }),
  get: (id) => api.get(`/problems/${id}`),
  create: (data) => api.post('/problems', data),
  update: (id, data) => api.patch(`/problems/${id}`, data),
  delete: (id) => api.delete(`/problems/${id}`),
  // Evidence (multipart upload). `transcript` is optional client-side STT text
  // (e.g. from Puter.js); when supplied the backend uses it instead of server STT.
  uploadEvidence: (id, file, type, transcript) => {
    const form = new FormData();
    form.append('file', file);
    form.append('type', type);
    if (transcript) form.append('transcript', transcript);
    return api.post(`/problems/${id}/evidence`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  listEvidence: (id) => api.get(`/problems/${id}/evidence`),
  // AI pipeline
  analyze: (id) => api.post(`/ai/analyze/${id}`),
  // Solutions for a problem (Phase 4 preview)
  solutions: {
    list: (problemId, params = {}) => api.get(`/problems/${problemId}/solutions`, { params }),
    get: (problemId, solutionId) => api.get(`/problems/${problemId}/solutions/${solutionId}`),
    create: (problemId, data) => api.post(`/problems/${problemId}/solutions`, data),
    update: (problemId, solutionId, data) => api.patch(`/problems/${problemId}/solutions/${solutionId}`, data),
  },
};

export const aiApi = {
  analyze: (id) => api.post(`/ai/analyze/${id}`),
};

export const tagsApi = {
  list: () => api.get('/tags'),
};

export const notificationsApi = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
};

export default api;