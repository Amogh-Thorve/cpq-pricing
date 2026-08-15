import React from "react";
import { FileText, Plus, Search, Filter, Sparkles, Send } from "lucide-react";

export default function QuoteBuilderPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2 flex items-center gap-2">
            <FileText size={28} className="text-zinc-500" />
            <span>Quotation Builder</span>
          </h1>
          <p className="text-sm text-zinc-400">
            Create, revise, and dispatch sales quotes with automatic pricing rule audits.
          </p>
        </div>
        <button className="flex items-center gap-2 bg-teal-500 text-zinc-950 px-4 py-2.5 rounded-lg text-sm font-bold hover:bg-teal-400 transition-all duration-200">
          <Plus size={16} />
          <span>Create Quote</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-xl shadow-lg">
        <div className="flex-1 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
          <input
            type="text"
            placeholder="Search quotations by number, customer, status, or owner..."
            className="w-full pl-11 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 placeholder-zinc-600"
            disabled
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm font-semibold hover:bg-zinc-700/50 text-zinc-300">
          <Filter size={16} />
          <span>Filters</span>
        </button>
      </div>

      {/* Quotes Listing Table Card Placeholder */}
      <div className="border border-zinc-800 rounded-xl bg-zinc-900/40 p-12 text-center shadow-lg">
        <FileText size={48} className="mx-auto text-zinc-700 mb-4" />
        <h3 className="text-lg font-bold text-zinc-200 mb-1">No quotes found</h3>
        <p className="text-sm text-zinc-500 max-w-sm mx-auto mb-6">
          Get started by configuring a new proposal or importing CRM records to populate pipeline opportunities.
        </p>
      </div>
    </div>
  );
}
