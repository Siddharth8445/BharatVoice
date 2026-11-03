import { api } from './client';

export interface HealthResponse {
  status: 'healthy' | 'unhealthy' | string;
  app_name: string;
  environment: string;
  database: 'connected' | 'disconnected' | string;
  use_mock_gnani: boolean;
}

export const getHealth = async (): Promise<HealthResponse> => {
  const res = await api.get<HealthResponse>('/health');
  return res.data;
};
