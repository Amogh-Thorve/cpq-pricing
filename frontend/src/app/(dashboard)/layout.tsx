"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  BookOpen,
  DollarSign,
  Sliders,
  FileText,
  CheckSquare,
  Settings,
  ShieldCheck,
  Sparkles,
  Database,
  ArrowRightLeft
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarLinkProps {
  href: string;
  label: string;
  icon: React.ReactNode;
  active: boolean;
}

function SidebarLink({ href, label, icon, active }: SidebarLinkProps) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
        active
          ? "bg-zinc-800 text-teal-400 shadow-sm border border-zinc-700/50"
          : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/50"
      )}
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const links = [
    { href: "/dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
    { href: "/customers", label: "Customers", icon: <Users size={18} /> },
    { href: "/catalog", label: "Product Catalog", icon: <BookOpen size={18} /> },
    { href: "/pricing", label: "Pricing Engine", icon: <DollarSign size={18} /> },
    { href: "/configuration", label: "Product Config", icon: <Sliders size={18} /> },
    { href: "/quotes", label: "Quote Builder", icon: <FileText size={18} /> },
    { href: "/approvals", label: "Approvals", icon: <CheckSquare size={18} /> },
    { href: "/integrations", label: "Integrations", icon: <ArrowRightLeft size={18} /> },
  ];

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-100 font-sans">
      {/* Left Sidebar */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/60 backdrop-blur-xl flex flex-col fixed inset-y-0 left-0 z-20">
        {/* Brand Logo Header */}
        <div className="h-16 flex items-center gap-2 px-6 border-b border-zinc-800">
          <ShieldCheck className="text-teal-400" size={24} />
          <div className="font-bold text-lg tracking-wider bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
            CPQ COGNITIVE
          </div>
        </div>

        {/* Sidebar Nav Links */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {links.map((link) => (
            <SidebarLink
              key={link.href}
              href={link.href}
              label={link.label}
              icon={link.icon}
              active={pathname.startsWith(link.href)}
            />
          ))}
        </nav>

        {/* Copilot Indicator Footer */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-950/40">
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800">
            <Sparkles className="text-teal-400 animate-pulse" size={16} />
            <div className="text-xs">
              <div className="font-semibold text-zinc-200">Gemini Copilot</div>
              <div className="text-zinc-500 font-medium">Enterprise Assistant</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Pane */}
      <div className="flex-1 pl-64 flex flex-col">
        {/* Global Toolbar Header */}
        <header className="h-16 border-b border-zinc-800 bg-zinc-900/40 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <Database size={16} className="text-zinc-500" />
            <span className="text-sm font-semibold text-zinc-400">Environment:</span>
            <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs font-semibold uppercase tracking-wider border border-zinc-700">
              Local Dev
            </span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs font-semibold text-zinc-500">Sales Representative</span>
            <div className="w-8 h-8 rounded-full bg-teal-500 flex items-center justify-center text-zinc-950 font-bold text-sm">
              SR
            </div>
          </div>
        </header>

        {/* Dynamic Pages Container */}
        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
