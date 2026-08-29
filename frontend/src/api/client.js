import axios from 'axios';

const getBaseURL = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== 'undefined' && !['localhost', '127.0.0.1'].includes(window.location.hostname)) {
    // Deployed (e.g. Vercel): call the backend on the same origin.
    return '/api/v1';
  }
  return 'http://localhost:8000/api/v1';
};

const api = axios.create({
  baseURL: getBaseURL(),
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
      // Only bounce to login if a session existed and expired. Anonymous/public
      // calls (e.g. loading the university directory on the register page) must
      // not be redirected.
      if (localStorage.getItem('token')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
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
  deleteAccount: () => api.delete('/auth/me'),
  updateProfile: (data) => api.patch('/auth/me', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  requestOtp: (email, purpose = 'verify') => api.post('/auth/request-otp', { email, purpose }),
  verifyOtp: (email, code, purpose = 'verify') => api.post('/auth/verify-otp', { email, code, purpose }),
  loginRequestCode: (email, password) => api.post('/auth/login/request-code', { email, password }),
  loginVerify: (email, code) => api.post('/auth/login/verify', { email, code }),
};

// Problems
export const problemsApi = {
  list: (params = {}) => api.get('/problems', { params }),
  get: (id) => api.get(`/problems/${id}`),
  create: (data) => api.post('/problems', data),
  remove: (id, reason) => api.delete(`/problems/${id}`, { data: { reason } }),
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
  extractTags: (title, description, transcript = '') =>
    api.post('/ai/extract-tags', { title, description, transcript }),
  translate: (text, target_language) => api.post('/ai/translate', { text, target_language }),
};

export const tagsApi = {
  list: () => api.get('/tags'),
};

export const notificationsApi = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
};

// Phase 4 — Universities / HEI
export const universitiesApi = {
  list: (params = {}) => api.get('/universities', { params }),
  create: (data) => api.post('/universities', data),
  get: (id) => api.get(`/universities/${id}`),
  addMember: (id, data) => api.post(`/universities/${id}/members`, data),
  members: (id) => api.get(`/universities/${id}/members`),
  listStudents: (id) => api.get(`/universities/${id}/students`),
  addStudentsBulk: (id, data) => api.post(`/universities/${id}/students/bulk`, data),
  options: () => api.get('/universities/options'),
  suggest: (data) => api.post('/universities/suggest', data),
};

// Phase 4 — Teams
export const teamsApi = {
  create: (data) => api.post('/teams', data),
  list: () => api.get('/teams'),
  get: (id) => api.get(`/teams/${id}`),
  addMember: (id, data) => api.post(`/teams/${id}/members`, data),
};

// Phase 4 — Proposals (solutions)
export const proposalsApi = {
  create: (data) => api.post('/proposals', data),
  list: (params = {}) => api.get('/proposals', { params }),
  get: (id) => api.get(`/proposals/${id}`),
  update: (id, data) => api.patch(`/proposals/${id}`, data),
  submit: (id) => api.post(`/proposals/${id}/submit`),
  approve: (id) => api.post(`/proposals/${id}/approve`),
};

// Phase 5 — Industries
export const industriesApi = {
  list: () => api.get('/industries'),
  create: (data) => api.post('/industries', data),
  get: (id) => api.get(`/industries/${id}`),
  update: (id, data) => api.patch(`/industries/${id}`, data),
  proposals: (id) => api.get(`/industries/${id}/proposals`),
};

// Phase 5 — Collaborations
export const collaborationsApi = {
  create: (data) => api.post('/collaborations', data),
  list: () => api.get('/collaborations'),
  get: (id) => api.get(`/collaborations/${id}`),
  update: (id, data) => api.patch(`/collaborations/${id}`, data),
  addMilestone: (id, data) => api.post(`/collaborations/${id}/milestones`, data),
  updateMilestone: (id, mid, data) => api.patch(`/collaborations/${id}/milestones/${mid}`, data),
  addDeliverable: (id, data) => api.post(`/collaborations/${id}/deliverables`, data),
  addIp: (id, data) => api.post(`/collaborations/${id}/ip`, data),
  addImpact: (id, data) => api.post(`/collaborations/${id}/impact`, data),
};

// Phase 6 — Government analytics
export const governmentApi = {
  analytics: () => api.get('/government/analytics'),
  leaderboards: () => api.get('/government/leaderboards'),
  impactReports: () => api.get('/government/impact-reports'),
};

// Phase 7 — Admin
export const adminApi = {
  users: () => api.get('/admin/users'),
  updateUser: (id, data) => api.patch(`/admin/users/${id}`, data),
  moderation: () => api.get('/admin/moderation'),
  setStatus: (id, data) => api.post(`/admin/problems/${id}/status`, data),
  aiConfig: () => api.get('/admin/ai-config'),
  broadcast: (data) => api.post('/admin/notifications/broadcast', data),
};

// Engagement — comments + upvotes
export const engagementApi = {
  addComment: (data) => api.post('/engagement/comments', data),
  listComments: (entity_type, entity_id) => api.get('/engagement/comments', { params: { entity_type, entity_id } }),
  toggleUpvote: (problem_id) => api.post('/engagement/upvotes', { problem_id }),
  upvoteCount: (problem_id) => api.get('/engagement/upvotes', { params: { problem_id } }),
};

export default api;