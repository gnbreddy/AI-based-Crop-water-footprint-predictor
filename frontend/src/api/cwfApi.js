import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  const response = await client.get('/health');
  return response.data;
};

export const fetchCrops = async () => {
  const response = await client.get('/api/v1/crops');
  return response.data;
};

export const fetchSoils = async () => {
  const response = await client.get('/api/v1/soils');
  return response.data;
};

export const fetchAuditRecords = async (limit = 15) => {
  const response = await client.get(`/api/v1/records?limit=${limit}`);
  return response.data;
};

export const predictCwf = async (payload) => {
  const response = await client.post('/api/v1/cwf/predict', payload);
  return response.data;
};
