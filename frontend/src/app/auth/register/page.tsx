"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { ShieldCheck, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { useRegister } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types/auth";

// ─── Validation schema ────────────────────────────────────────────────────────

const registerSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters"),
  role: z.enum(["sales_rep", "manager", "executive", "admin"] as const),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

// ─── Component ────────────────────────────────────────────────────────────────

export default function RegisterPage() {
  const register = useRegister();

  const {
    register: field,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: "sales_rep" },
  });

  const onSubmit = (values: RegisterFormValues) => {
    register.mutate(values);
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-6 font-sans">
      <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-2xl p-8 space-y-8 shadow-2xl">
        {/* Brand header */}
        <div className="flex flex-col items-center space-y-2">
          <div className="p-3 rounded-2xl bg-zinc-800 border border-zinc-700/50">
            <ShieldCheck className="text-teal-400" size={32} />
          </div>
          <h1 className="text-2xl font-extrabold tracking-wider bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
            CPQ COGNITIVE
          </h1>
          <p className="text-xs text-zinc-500 font-semibold tracking-wide uppercase">
            Request Platform Access
          </p>
        </div>

        {/* Success banner */}
        {register.isSuccess && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-sm text-emerald-300">
            <CheckCircle2 size={16} className="shrink-0 text-emerald-400" />
            <span>Account created! Redirecting to login…</span>
          </div>
        )}

        {/* API error banner */}
        {register.error && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-950/40 border border-red-800/50 text-sm text-red-300">
            <AlertCircle size={16} className="shrink-0 text-red-400" />
            <span>
              {(register.error as { detail?: string }).detail ??
                "Registration failed. Please try again."}
            </span>
          </div>
        )}

        {/* Form */}
        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
          {/* Full name */}
          <div className="space-y-1.5">
            <label htmlFor="full_name" className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
              Full Name
            </label>
            <input
              id="full_name"
              type="text"
              autoComplete="name"
              placeholder="John Doe"
              className={cn(
                "w-full px-4 py-3 bg-zinc-950 border rounded-xl text-sm text-zinc-200 focus:outline-none placeholder-zinc-600 transition-colors",
                errors.full_name ? "border-red-700" : "border-zinc-800 focus:border-teal-600"
              )}
              {...field("full_name")}
            />
            {errors.full_name && (
              <p className="text-xs text-red-400">{errors.full_name.message}</p>
            )}
          </div>

          {/* Email */}
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="name@company.com"
              className={cn(
                "w-full px-4 py-3 bg-zinc-950 border rounded-xl text-sm text-zinc-200 focus:outline-none placeholder-zinc-600 transition-colors",
                errors.email ? "border-red-700" : "border-zinc-800 focus:border-teal-600"
              )}
              {...field("email")}
            />
            {errors.email && (
              <p className="text-xs text-red-400">{errors.email.message}</p>
            )}
          </div>

          {/* Role */}
          <div className="space-y-1.5">
            <label htmlFor="role" className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
              Role
            </label>
            <select
              id="role"
              className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 focus:border-teal-600 rounded-xl text-sm text-zinc-200 focus:outline-none transition-colors"
              {...field("role")}
            >
              <option value="sales_rep">Sales Representative</option>
              <option value="manager">Sales Manager</option>
              <option value="executive">Executive</option>
            </select>
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <label htmlFor="password" className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              placeholder="Min. 8 characters"
              className={cn(
                "w-full px-4 py-3 bg-zinc-950 border rounded-xl text-sm text-zinc-200 focus:outline-none placeholder-zinc-600 transition-colors",
                errors.password ? "border-red-700" : "border-zinc-800 focus:border-teal-600"
              )}
              {...field("password")}
            />
            {errors.password && (
              <p className="text-xs text-red-400">{errors.password.message}</p>
            )}
          </div>

          {/* Submit */}
          <button
            id="register-submit"
            type="submit"
            disabled={register.isPending || register.isSuccess}
            className="w-full py-3.5 bg-teal-500 text-zinc-950 rounded-xl font-bold text-sm hover:bg-teal-400 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-teal-500/10 flex items-center justify-center gap-2"
          >
            {register.isPending ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Creating account…</span>
              </>
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <div className="text-center text-xs text-zinc-500 font-medium">
          Already registered?{" "}
          <Link href="/auth/login" className="text-teal-400 hover:text-teal-300 font-bold">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
