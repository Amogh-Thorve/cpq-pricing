import React from "react";
import { Users, Search, Plus, Sparkles } from "lucide-react";

export default function CustomersPage() {
  return (
    <div className="space-y-8">
      {/* Header section */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2 flex items-center gap-2">
            <Users size={28} className="text-zinc-500" />
            <span>Customer Accounts</span>
          </h1>
          <p className="text-sm text-zinc-400">
            View directory of customer profiles and contact stakeholders mapped to CRM records.
          </p>
        </div>
        <button className="flex items-center gap-2 bg-zinc-800 border border-zinc-700 text-zinc-100 px-4 py-2.5 rounded-lg text-sm font-semibold hover:bg-zinc-700/50 transition-all duration-200">
          <Plus size={16} />
          <span>New Customer</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex items-center gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-xl shadow-lg">
        <div className="flex-1 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
          <input
            type="text"
            placeholder="Search accounts by name, domain, industry, or Salesforce ID..."
            className="w-full pl-11 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 placeholder-zinc-600"
            disabled
          />
        </div>
      </div>

      {/* Customer Directory Placeholder Card Grid */}
      <div className="border border-zinc-800 rounded-xl bg-zinc-900/40 p-12 text-center shadow-lg">
        <Users size={48} className="mx-auto text-zinc-700 mb-4" />
        <h3 className="text-lg font-bold text-zinc-200 mb-1">No customer accounts loaded</h3>
        <p className="text-sm text-zinc-500 max-w-sm mx-auto mb-6">
          To get started, import accounts using Excel/CSV upload or link your Salesforce CRM connector.
        </p>
        <div className="flex justify-center gap-3">
          <button className="px-4 py-2 bg-teal-500 text-zinc-950 rounded-lg text-sm font-bold hover:bg-teal-400 transition-all duration-200">
            Link Salesforce CRM
          </button>
        </div>
      </div>
    </div>
  );
}
