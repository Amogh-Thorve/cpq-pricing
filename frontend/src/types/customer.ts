export type CustomerType = "BUSINESS" | "INDIVIDUAL";
export type CustomerStatus = "PROSPECT" | "ACTIVE" | "INACTIVE" | "ARCHIVED";
export type AddressType = "BILLING" | "SHIPPING";

export interface ContactRead {
  id: number;
  customer_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  is_primary: boolean;
  created_at: string;
}

export interface ContactCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  is_primary: boolean;
}

export interface CustomerAddressRead {
  id: number;
  customer_id: number;
  address_type: AddressType;
  line1: string;
  line2?: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_primary: boolean;
  created_at: string;
}

export interface CustomerAddressCreate {
  address_type: AddressType;
  line1: string;
  line2?: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_primary: boolean;
}

export interface CustomerRead {
  id: number;
  tenant_id: string;
  customer_number: string;
  legal_name: string;
  display_name?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  industry?: string | null;
  customer_type: CustomerType;
  status: CustomerStatus;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  deleted_by?: string | null;
  contacts: ContactRead[];
  addresses: CustomerAddressRead[];
}

export interface CustomerCreate {
  customer_number: string;
  legal_name: string;
  display_name?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  industry?: string | null;
  customer_type: CustomerType;
  status: CustomerStatus;
  owner_id?: string | null;
}

export interface CustomerUpdate {
  customer_number?: string | null;
  legal_name?: string | null;
  display_name?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  industry?: string | null;
  customer_type?: CustomerType | null;
  status?: CustomerStatus | null;
  owner_id?: string | null;
}

export interface CustomerListResponse {
  items: CustomerRead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
