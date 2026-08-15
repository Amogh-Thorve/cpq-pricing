import React from "react";
import { ArrowRightLeft, FileSpreadsheet, CloudLightning, ShieldCheck, Upload, AlertCircle } from "lucide-react";

export default function IntegrationsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-100 mb-2 flex items-center gap-2">
          <ArrowRightLeft size={28} className="text-zinc-500" />
          <span>Connectors & Integrations</span>
        </h1>
        <p className="text-sm text-zinc-400">
          Sync accounts and products using CSV imports or set up dynamic Salesforce CRM pipeline synchronization.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Salesforce Connection Panel */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-6 shadow-lg flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-900/30 text-blue-400 rounded-xl border border-blue-800/50">
                <CloudLightning size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-zinc-100">Salesforce CRM Integration</h3>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                  CRM Connector
                </span>
              </div>
            </div>
            
            <p className="text-sm text-zinc-400 leading-relaxed">
              Authenticate via secure OAuth 2.0 to import accounts, contacts, and opportunities. Automatically sync approved CPQ quotes back to Salesforce opportunities.
            </p>

            <div className="bg-zinc-950/60 border border-zinc-800 rounded-lg p-4 flex items-center gap-3 text-xs text-zinc-500">
              <AlertCircle size={16} className="text-zinc-500" />
              <span>Authorization state: Disconnected. Connect to import active opportunities.</span>
            </div>
          </div>

          <button className="w-full py-3 bg-blue-500 text-white rounded-lg font-bold text-sm hover:bg-blue-400 transition-all duration-200 mt-6">
            Link Salesforce Account
          </button>
        </div>

        {/* Excel / CSV Importer Panel */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-6 shadow-lg flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-900/30 text-emerald-400 rounded-xl border border-emerald-800/50">
                <FileSpreadsheet size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-zinc-100">Excel / CSV Batch Imports</h3>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                  Flat File Uploader
                </span>
              </div>
            </div>
            
            <p className="text-sm text-zinc-400 leading-relaxed">
              Batch import product lists, customer sheets, category trees, custom price books, or exclusion rules using CSV or Excel formats.
            </p>

            {/* Drag and Drop Zone Mock */}
            <div className="border-2 border-dashed border-zinc-800 bg-zinc-950/40 rounded-lg p-8 text-center cursor-not-allowed hover:bg-zinc-950/60 transition-all duration-200">
              <Upload className="mx-auto text-zinc-600 mb-2" size={24} />
              <div className="text-xs font-bold text-zinc-300">Drag files here or click to browse</div>
              <div className="text-[10px] text-zinc-600 mt-1">Supports CSV, XLS, XLSX up to 10MB</div>
            </div>
          </div>

          <button className="w-full py-3 bg-emerald-600 text-white rounded-lg font-bold text-sm hover:bg-emerald-500 transition-all duration-200" disabled>
            Upload Document
          </button>
        </div>
      </div>
    </div>
  );
}
