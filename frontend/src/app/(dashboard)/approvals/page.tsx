import React from "react";
import { CheckSquare, Clock, Filter, CheckCircle2, ShieldAlert } from "lucide-react";

export default function ApprovalsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2 flex items-center gap-2">
          <CheckSquare size={28} className="text-zinc-500" />
          <span>Approvals Workflow</span>
        </h1>
        <p className="text-sm text-zinc-400">
          Review, sign off on, or reject quotes flagged for discount overrides or low margins.
        </p>
      </div>

      {/* Tabs / Filter states */}
      <div className="flex gap-4 border-b border-zinc-800">
        <button className="px-4 py-2 text-sm font-semibold border-b-2 border-teal-400 text-teal-400">
          Pending Review (0)
        </button>
        <button className="px-4 py-2 text-sm font-semibold text-zinc-500 hover:text-zinc-300">
          Completed History (0)
        </button>
      </div>

      {/* Approvals Listing Card Placeholder */}
      <div className="border border-zinc-800 rounded-xl bg-zinc-900/40 p-12 text-center shadow-lg">
        <CheckSquare size={48} className="mx-auto text-zinc-700 mb-4" />
        <h3 className="text-lg font-bold text-zinc-200 mb-1">Queue is clear</h3>
        <p className="text-sm text-zinc-500 max-w-sm mx-auto">
          There are currently no discount override or margin violation requests pending sign-off for your role.
        </p>
      </div>
    </div>
  );
}
