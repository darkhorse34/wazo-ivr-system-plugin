import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/ivr';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

// System API
export const getSystemStatus = () => api.get('/status').then(res => res.data);

// Flows API
export const getFlows = () => api.get('/flows').then(res => res.data);
export const getFlow = (id) => api.get(`/flows/${id}`).then(res => res.data);
export const createFlow = (flowData) => api.post('/flows', flowData).then(res => res.data);
export const updateFlow = (id, flowData) => api.put(`/flows/${id}`, flowData).then(res => res.data);
export const deleteFlow = (id) => api.delete(`/flows/${id}`).then(res => res.data);
export const deployFlow = (id, wazoHost, token) => 
  api.post(`/flows/${id}/deploy`, { wazo_host: wazoHost, token }).then(res => res.data);

// TTS API
export const getAvailableVoices = (language = 'en-US') => 
  api.get(`/tts/voices?language=${language}`).then(res => res.data);
export const synthesizeSpeech = (text, voice, language, ttsBackend = 'polly') =>
  api.post('/tts/synthesize', { text, voice, language, tts_backend: ttsBackend }).then(res => res.data);

// Wazo Integration API
export const getWazoQueues = (wazoHost, token) =>
  api.get(`/wazo/queues?wazo_host=${wazoHost}&token=${token}`).then(res => res.data);
export const getWazoAgents = (wazoHost, token) =>
  api.get(`/wazo/agents?wazo_host=${wazoHost}&token=${token}`).then(res => res.data);

// Maintenance API
export const cleanupSystem = (maxAgeDays = 30) =>
  api.post('/maintenance/cleanup', { max_age_days: maxAgeDays }).then(res => res.data);

export default api;
