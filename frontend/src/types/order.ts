export interface OrderItemResponse {
  id: number;
  order_id: number;
  product_name: string;
  product_id?: string | null;
  quantity: number;
  unit: string;
  unit_price?: number | null;
}

export interface OrderResponse {
  id: number;
  transcript: string;
  status: string;
  created_at: string; // ISO datetime
  updated_at: string;
  items: OrderItemResponse[];
}

export interface OrderItemCreate {
  product_name: string;
  product_id?: string | null;
  quantity: number;
  unit: string;
  unit_price?: number | null;
}

export interface ParsedOrderItem {
  product_id: string;
  name: string;
  quantity: number;
  unit: string;
  unit_price?: number | null;
}

export interface ParsedOrderResponse {
  items: ParsedOrderItem[];
  status: string;
  clarification_required: boolean;
  clarification_message?: string | null;
  unsupported_products: string[];
}
