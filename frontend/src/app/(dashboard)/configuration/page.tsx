import React from "react";
import { Sliders, Plus, HelpCircle, FilePlus } from "lucide-react";

export default function ProductConfigurationPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2 flex items-center gap-2">
            <Sliders size={28} className="text-zinc-500" />
            <span>Product Configuration</span>
          </h1>
          <p className="text-sm text-zinc-400">
            Define dynamic bundle constraints, required dependencies, and validation rules.
          </p>
        </div>
        <button className="flex items-center gap-2 bg-zinc-800 border border-zinc-700 text-zinc-100 px-4 py-2.5 rounded-lg text-sm font-semibold hover:bg-zinc-700/50 transition-all duration-200">
          <Plus size={16} />
          <span>New Rule</span>
        </button>
      </div>

      {/* Rules Workspace Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Rule creation helper */}
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl space-y-4">
          <h3 className="font-bold text-zinc-200 text-lg">Exclusion Rule</h3>
          <p className="text-sm text-zinc-500">
            Prevents sales representatives from combining incompatible items (e.g. Premium Support SLA cannot be bundled with standard tier support).
          </p>
          <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-950/50 flex justify-between items-center text-xs">
            <span className="text-zinc-400">Configured exclusion dependencies</span>
            <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-semibold border border-zinc-700">
              0 Rules
            </span>
          </div>
        </div>

        {/* Dependency rule helper */}
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl space-y-4">
          <h3 className="font-bold text-zinc-200 text-lg">Required Dependency</h3>
          <p className="text-sm text-zinc-500">
            Automatically triggers required item additions (e.g. buying hardware Server nodes requires purchasing rack brackets).
          </p>
          <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-950/50 flex justify-between items-center text-xs">
            <span className="text-zinc-400">Configured dependency checks</span>
            <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-semibold border border-zinc-700">
              0 Rules
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
