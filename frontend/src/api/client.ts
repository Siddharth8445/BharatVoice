import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
});

// Simple response interceptor for global error handling (toast is used in components)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Let calling code handle the error; we just pass it on.
    return Promise.reject(error);
  }
);
