import { api } from '../lib/api'

export const admin = {
  stats: () => api.get('/api/v1/admin/stats', true),
  listIncidents: (page = 1, per_page = 25) => api.get(`/api/v1/admin/incidents?page=${page}&per_page=${per_page}`, true),
  intelligence: (id: string) => api.get(`/api/v1/admin/incidents/${id}/intelligence`, true),
  listEscalations: (page = 1, per_page = 25) => api.get(`/api/v1/admin/escalations?page=${page}&per_page=${per_page}`, true),
  getRecommendation: (id: string) => api.get(`/api/v1/recommendations/${id}`, true),
}
