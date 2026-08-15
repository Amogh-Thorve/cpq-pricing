export interface CategoryRead {
  id: number;
  name: string;
  description?: string | null;
  parent_id?: number | null;
}

export interface CategoryCreate {
  name: string;
  description?: string | null;
  parent_id?: number | null;
}

export interface ProductRead {
  id: number;
  sku: string;
  name: string;
  description?: string | null;
  base_price: number;
  cost_price?: number | null;
  currency?: string;
  margin_amount?: number | null;
  margin_percentage?: number | null;
  is_active: boolean;
  billing_type: "MRC" | "NRC" | "USAGE";
  category_id?: number | null;
  external_crm_id?: string | null;
  category?: CategoryRead | null;
}

export interface ProductCreate {
  sku: string;
  name: string;
  description?: string | null;
  base_price: number;
  cost_price?: number | null;
  currency?: string;
  is_active?: boolean;
  billing_type: "MRC" | "NRC" | "USAGE";
  category_id?: number | null;
  external_crm_id?: string | null;
}

export interface ProductUpdate {
  sku?: string;
  name?: string;
  description?: string | null;
  base_price?: number;
  cost_price?: number | null;
  currency?: string;
  is_active?: boolean;
  billing_type?: "MRC" | "NRC" | "USAGE";
  category_id?: number | null;
  external_crm_id?: string | null;
}

export interface PriceBookEntryRead {
  id: number;
  price_book_id: number;
  product_id: number;
  custom_price: number;
  is_active: boolean;
  product?: ProductRead | null;
}

export interface PriceBookEntryCreate {
  product_id: number;
  custom_price: number;
  is_active?: boolean;
}

export interface PriceBookRead {
  id: number;
  name: string;
  description?: string | null;
  is_active: boolean;
  is_standard: boolean;
  entries: PriceBookEntryRead[];
}

export interface PriceBookCreate {
  name: string;
  description?: string | null;
  is_active?: boolean;
  is_standard?: boolean;
}
