export const API_CONFIG = {
  BASE_URL: __DEV__
    ? 'http://localhost:8000' // Use your local IP for physical device: 'http://192.168.x.x:8000'
    : 'https://your-production-api.com',
  API_VERSION: '/api/v1',
  TIMEOUT: 10000,
};

export const COLORS = {
  primary: '#667eea',
  secondary: '#764ba2',
  success: '#4CAF50',
  error: '#f44336',
  warning: '#ff9800',
  text: '#333333',
  textLight: '#666666',
  background: '#ffffff',
  backgroundLight: '#f5f5f5',
  border: '#e0e0e0',
};
