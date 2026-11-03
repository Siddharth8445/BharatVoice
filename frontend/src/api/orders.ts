import { api } from './client';
import { OrderResponse, OrderItemCreate, ParsedOrderResponse } from '../types/order';

export interface CreateVoiceOrderResponse extends OrderResponse {}

export const createVoiceOrder = async (
  audioFile: File
): Promise<CreateVoiceOrderResponse> => {
  const form = new FormData();
  form.append('audio_file', audioFile);
  const res = await api.post<CreateVoiceOrderResponse>('/orders/voice', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const getOrder = async (orderId: number): Promise<OrderResponse> => {
  const res = await api.get<OrderResponse>(`/orders/${orderId}`);
  return res.data;
};

export const listOrders = async (
  params?: { skip?: number; limit?: number; status_filter?: string }
): Promise<OrderResponse[]> => {
  const res = await api.get<OrderResponse[]>('/orders', { params });
  return res.data;
};

export const editOrder = async (
  orderId: number,
  items: OrderItemCreate[]
): Promise<OrderResponse> => {
  const payload = { items };
  const res = await api.patch<OrderResponse>(`/orders/${orderId}`, payload);
  return res.data;
};

export const confirmOrder = async (orderId: number): Promise<OrderResponse> => {
  const res = await api.post<OrderResponse>(`/orders/${orderId}/confirm`);
  return res.data;
};

export const cancelOrder = async (orderId: number): Promise<OrderResponse> => {
  const res = await api.post<OrderResponse>(`/orders/${orderId}/cancel`);
  return res.data;
};

export const speakConfirmation = async (
  orderId: number
): Promise<Blob> => {
  const res = await api.post(`/orders/${orderId}/speak-confirmation`, null, {
    responseType: 'blob',
  });
  return res.data;
};
