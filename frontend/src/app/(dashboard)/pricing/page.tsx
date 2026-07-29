import React from "react";
import { DollarSign, Percent, Scale, ShieldAlert } from "lucide-react";

export default function PricingEnginePage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2 flex items-center gap-2">
          <DollarSign size={28} className="text-zinc-500" />
          <span>Pricing Engine</span>
        </h1>
        <p className="text-sm text-zinc-400">
          Configure discount schemas, volume thresholds, customer tier matrices, and minimum margin floors.
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl space-y-4">
          <div className="flex items-center gap-2 text-teal-400 font-bold text-sm">
            <Percent size={16} />
            <span>Volume Discounts</span>
          </div>
          <p className="text-xs text-zinc-500">
            Define volume-based discount triggers (e.g. quantity &gt; 50 receives 10% off).
          </p>
          <div className="text-zinc-400 text-sm font-semibold border-t border-zinc-800 pt-3">
            0 active schedules
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl space-y-4">
          <div className="flex items-center gap-2 text-teal-400 font-bold text-sm">
            <Scale size={16} />
            <span>Tiered Pricing Matrix</span>
          </div>
          <p className="text-xs text-zinc-500">
            Establish pricing based on contract terms, customer sizes, or geolocations.
          </p>
          <div className="text-zinc-400 text-sm font-semibold border-t border-zinc-800 pt-3">
            0 active schedules
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl space-y-4">
          <div className="flex items-center gap-2 text-teal-400 font-bold text-sm">
            <ShieldAlert size={16} />
            <span>Margin Guardrails</span>
          </div>
          <p className="text-xs text-zinc-500">
            Block quote generation if gross margin falls below company floors.
          </p>
          <div className="text-zinc-400 text-sm font-semibold border-t border-zinc-800 pt-3">
            0 active rules
          </div>
        </div>
      </div>
    </div>
  );
}
