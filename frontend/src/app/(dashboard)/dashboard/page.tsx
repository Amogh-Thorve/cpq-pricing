import React from "react";
import {
  TrendingUp,
  FileSpreadsheet,
  AlertTriangle,
  Clock,
  Sparkles,
  ArrowRight
} from "lucide-react";
import Link from "next/link";

interface MetricCardProps {
  title: string;
  value: string;
  subtext: string;
  icon: React.ReactNode;
}

function MetricCard({ title, value, subtext, icon }: MetricCardProps) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-lg hover:border-zinc-700/50 transition-all duration-300">
      <div className="flex justify-between items-start mb-4">
        <span className="text-sm font-semibold text-zinc-400">{title}</span>
        <div className="p-2 bg-zinc-800 rounded-lg text-teal-400">{icon}</div>
      </div>
      <div className="text-2xl font-bold tracking-tight text-zinc-100">{value}</div>
      <div className="text-xs text-zinc-500 mt-2 font-medium">{subtext}</div>
    </div>
  );
}

export default function DashboardHome() {
  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2">
          Workspace Overview
        </h1>
        <p className="text-sm text-zinc-400">
          Monitor your quote builder pipe, approval queues, and CRM sync operations.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Quotation Revenue"
          value="$0"
          subtext="No data for this month"
          icon={<TrendingUp size={20} />}
        />
        <MetricCard
          title="Active Quotes Pipeline"
          value="0"
          subtext="No active quotes"
          icon={<Clock size={20} />}
        />
        <MetricCard
          title="Salesforce Sync Status"
          value="Not Connected"
          subtext="Integration offline"
          icon={<FileSpreadsheet size={20} />}
        />
        <MetricCard
          title="Pending Approvals"
          value="0"
          subtext="No pending requests"
          icon={<AlertTriangle size={20} />}
        />
      </div>

      {/* Copilot Action Board */}
      <div className="p-6 bg-gradient-to-br from-zinc-900 via-zinc-900 to-teal-950/20 border border-zinc-800 rounded-xl flex items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-teal-400 text-sm font-semibold">
            <Sparkles size={16} />
            <span>AI-Assisted Workflow Suggestion</span>
          </div>
          <h2 className="text-xl font-bold text-zinc-100">No active suggestions</h2>
          <p className="text-sm text-zinc-400 max-w-xl">
            Gemini Copilot is ready to analyze your pipeline and suggest actions as soon as new quotes or customers are registered in the workspace.
          </p>
        </div>
        <Link 
          href="/quotes"
          className="flex items-center gap-2 bg-teal-500 text-zinc-950 px-5 py-3 rounded-lg font-bold text-sm hover:bg-teal-400 transition-all duration-200"
        >
          <span>Open Quotes Builder</span>
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
