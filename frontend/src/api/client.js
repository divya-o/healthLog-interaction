// Base URL matches main.py router prefix: /api

import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',       // proxied to http://localhost:8000 via package.json "proxy"
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── HCP endpoints 

export const hcpApi = {
  // Search by partial name or specialty — used by HCPSearch autocomplete
  search: (query) =>
    apiClient.get('/hcps', { params: { specialty: query, limit: 20 } }),

  getById: (id) =>
    apiClient.get(`/hcps/${id}`),
};

// ── Interaction endpoints 

export const interactionsApi = {
  // POST /api/interactions — structured form submission
  create: (payload) =>
    apiClient.post('/interactions', payload),

  // GET /api/interactions — list with optional filters
  list: (params = {}) =>
    apiClient.get('/interactions', { params }),

  // PATCH /api/interactions/:id — partial update
  update: (id, data) =>
    apiClient.patch(`/interactions/${id}`, data),
};

// ── Chat endpoint 

export const chatApi = {
  // POST /api/chat/message — send message to LangGraph agent
  sendMessage: (payload) =>
    apiClient.post('/chat/message', payload),
};
