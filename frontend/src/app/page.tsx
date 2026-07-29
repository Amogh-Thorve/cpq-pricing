import React from "react";
import Link from "next/link";
import { ShieldCheck, Sparkles, Lock } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col justify-between p-8 font-sans">
      {/* Top Brand Header */}
      <header className="flex justify-between items-center max-w-7xl mx-auto w-full py-4 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <ShieldCheck className="text-teal-400" size={24} />
          <span className="font-extrabold text-lg tracking-wider bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
            CPQ COGNITIVE
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/auth/login" className="text-sm font-semibold text-zinc-400 hover:text-zinc-100 transition-colors">
            Sign In
          </Link>
          <Link href="/auth/register" className="px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg text-sm font-semibold hover:bg-zinc-700/50 transition-colors">
            Register
          </Link>
        </div>
      </header>

      {/* Main Hero Landing content */}
      <main className="max-w-4xl mx-auto text-center py-20 space-y-8 flex-1 flex flex-col justify-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-950/30 border border-teal-800/40 text-teal-400 text-xs font-semibold uppercase tracking-wider mx-auto">
          <Sparkles size={14} className="animate-pulse" />
          <span>Google Gemini AI-Native Engine</span>
        </div>

        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-none bg-gradient-to-br from-white via-zinc-100 to-zinc-500 bg-clip-text text-transparent">
          Enterprise Configure, Price, & Quote Platform
        </h1>

        <p className="text-base text-zinc-400 max-w-xl mx-auto leading-relaxed">
          Configure bundles, calculate volumes, evaluate dynamic discounts, route multi-stage approvals, and sync results to Salesforce.
        </p>

        {/* Portals to features */}
        <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
          <Link 
            href="/auth/login"
            className="flex items-center justify-center gap-2 bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 px-6 py-3.5 rounded-xl font-bold text-sm text-zinc-300 transition-all duration-200"
          >
            <Lock size={18} />
            <span>Rep Security Login</span>
          </Link>
        </div>
      </main>

      {/* Footer copyright */}
      <footer className="text-center py-6 text-xs text-zinc-600 border-t border-zinc-900 max-w-7xl mx-auto w-full">
        &copy; {new Date().getFullYear()} CPQ Cognitive. All rights reserved. Mapped on standard REST API.
      </footer>
    </div>
  );
}
