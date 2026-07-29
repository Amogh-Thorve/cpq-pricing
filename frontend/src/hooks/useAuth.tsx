/**
 * Auth domain — API calls and React context.
 *
 * Provides:
 *   - useLogin()   – mutation that logs in and stores the token
 *   - useRegister() – mutation that creates a new user
 *   - useCurrentUser() – query that fetches the authed user profile
 *   - useLogout()  – clears token and redirects
 *   - AuthContext  – consumed by any component that needs the current user
 */
"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api, tokenStorage } from "@/lib/api";
import type { LoginRequest, RegisterRequest, Token, UserRead } from "@/types/auth";

// ─── API calls ────────────────────────────────────────────────────────────────

async function loginAPI(credentials: LoginRequest): Promise<Token> {
  return api.post<Token>("/auth/login", credentials);
}

async function registerAPI(data: RegisterRequest): Promise<UserRead> {
  return api.post<UserRead>("/auth/register", data);
}

async function getMeAPI(): Promise<UserRead> {
  return api.get<UserRead>("/auth/me");
}

// ─── Context ──────────────────────────────────────────────────────────────────

interface AuthContextValue {
  user: UserRead | null;
  isLoading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: user, isLoading } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMeAPI,
    // Only fetch if a token exists in storage
    enabled: !!tokenStorage.get(),
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const logout = useCallback(() => {
    tokenStorage.clear();
    queryClient.clear();
    router.push("/auth/login");
  }, [router, queryClient]);

  return (
    <AuthContext.Provider value={{ user: user ?? null, isLoading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

// ─── Mutation hooks ───────────────────────────────────────────────────────────

export function useLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: loginAPI,
    onSuccess: (data) => {
      tokenStorage.set(data.access_token);
      // Pre-populate the user cache so /auth/me is instant
      queryClient.setQueryData(["auth", "me"], data.user);
      router.push("/dashboard");
    },
  });
}

export function useRegister() {
  const router = useRouter();

  return useMutation({
    mutationFn: registerAPI,
    onSuccess: () => {
      router.push("/auth/login");
    },
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMeAPI,
    enabled: !!tokenStorage.get(),
    retry: false,
  });
}
