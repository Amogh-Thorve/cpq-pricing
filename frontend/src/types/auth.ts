/**
 * Auth domain — TypeScript types mirroring backend Pydantic schemas.
 */

export type UserRole = "admin" | "sales_rep" | "manager" | "executive";

export interface UserRead {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: UserRead;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}
