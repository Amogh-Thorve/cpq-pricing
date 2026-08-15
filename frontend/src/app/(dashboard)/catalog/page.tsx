import React from "react";
import { BookOpen, Search, Filter, Sparkles } from "lucide-react";

export default function ProductCatalogPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2 flex items-center gap-2">
            <BookOpen size={28} className="text-zinc-500" />
            <span>Product Catalog</span>
          </h1>
          <p className="text-sm text-zinc-400">
            Browse through active product lines, classifications, and custom Price Books.
          </p>
        </div>
      </div>

      {/* Toolbar filter */}
      <div className="flex gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-xl shadow-lg">
        <div className="flex-1 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
          <input
            type="text"
            placeholder="Search items by name, SKU, category, or CRM product code..."
            className="w-full pl-11 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 placeholder-zinc-600"
            disabled
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm font-semibold hover:bg-zinc-700/50 text-zinc-300">
          <Filter size={16} />
          <span>Filters</span>
        </button>
      </div>

      {/* Catalog Table Card Placeholder */}
      <div className="border border-zinc-800 rounded-xl bg-zinc-900/40 p-12 text-center shadow-lg">
        <BookOpen size={48} className="mx-auto text-zinc-700 mb-4" />
        <h3 className="text-lg font-bold text-zinc-200 mb-1">Catalog empty</h3>
        <p className="text-sm text-zinc-500 max-w-sm mx-auto mb-6">
          Upload your product listings using the Integrations tab or sync with Salesforce CRM to view active SKUs.
        </p>
      </div>
    </div>
  );
}
