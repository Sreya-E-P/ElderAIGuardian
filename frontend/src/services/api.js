import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor for debugging and auth
api.interceptors.request.use(
  (config) => {
    console.log('🚀 Request:', config.method.toUpperCase(), config.url);

    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    if (config.url.includes('/devops/')) {
      config.headers['X-DevOps-Key'] = import.meta.env.VITE_DEVOPS_API_KEY || 'devops-secret-key';
    }

    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('✅ Response:', response.status, response.config.url);
    return response;
  },
  async (error) => {
    console.error('❌ API Error:', error.message);

    if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      console.error('🔥 Backend not running at', API_BASE);
      console.error('   Start backend with: python run.py');
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default api;