"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Bell, Search, Activity } from "lucide-react";

const pageTitles: Record<string, string> = {
  "/dashboard": "Executive SOC Dashboard",
  "/transactions": "Transaction Intelligence Ledger",
  "/graph": "Graph Intelligence Workspace",
  "/geo": "Geospatial Intelligence Map",
  "/alerts": "Suspicious Alert Triage Queue",
  "/investigations": "Investigation Case Workspace",
  "/reports": "Regulatory Compliance Reports",
};

function Header() {
  const pathname = usePathname();
  const title = pageTitles[pathname] || "MuleTrace AI";

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-navy-700/80 bg-navy-900/95 px-6">
      {/* Left: Page title */}
      <div className="flex items-center gap-3">
        <h2 className="font-display text-sm font-semibold tracking-tight text-white">{title}</h2>
        <span className="hidden sm:inline-flex rounded-[3px] border border-navy-700 bg-navy-800/80 px-1.5 py-0.5 text-[10px] font-mono text-slate-400 tracking-wider">
          LIVE FEED
        </span>
      </div>

      {/* Right: Status & Actions */}
      <div className="flex items-center gap-3">
        {/* System Status */}
        <div className="hidden md:flex items-center gap-1.5 rounded-[4px] border border-navy-700 bg-navy-800/60 px-2.5 py-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          <span className="text-[11px] font-mono font-medium text-emerald-400 uppercase tracking-wide">
            Operational
          </span>
        </div>

        {/* Live Activity */}
        <div className="hidden lg:flex items-center gap-2 rounded-[4px] border border-navy-700 bg-navy-800/60 px-2.5 py-1">
          <Activity className="h-3.5 w-3.5 text-indigo-400" />
          <span className="text-[11px] font-mono text-slate-400">
            <span className="font-semibold text-slate-200">14,832</span> txns/24h
          </span>
        </div>

        {/* Search */}
        <button
          aria-label="Global search"
          className="flex h-8 w-8 items-center justify-center rounded-[4px] border border-navy-700/60 text-slate-400 transition-colors hover:bg-navy-800 hover:text-white"
        >
          <Search className="h-4 w-4" />
        </button>

        {/* Alerts Bell */}
        <button
          aria-label="System notifications"
          className="relative flex h-8 w-8 items-center justify-center rounded-[4px] border border-navy-700/60 text-slate-400 transition-colors hover:bg-navy-800 hover:text-white"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-[3px] bg-red-600 px-1 text-[9px] font-mono font-bold text-white">
            23
          </span>
        </button>

        {/* Avatar */}
        <div className="flex h-7 w-7 items-center justify-center rounded-[4px] border border-navy-700 bg-navy-800 text-[11px] font-mono font-semibold text-slate-300">
          SP
        </div>
      </div>
    </header>
  );
}

export default React.memo(Header);
