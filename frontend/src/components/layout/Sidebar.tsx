"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ArrowLeftRight,
  Network,
  MapPin,
  ShieldAlert,
  Search as SearchIcon,
  FileText,
  ChevronLeft,
  ChevronRight,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navGroups = [
  {
    group: "MONITOR",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/transactions", label: "Transactions", icon: ArrowLeftRight },
    ],
  },
  {
    group: "INTELLIGENCE",
    items: [
      { href: "/graph", label: "Graph Intelligence", icon: Network },
      { href: "/geo", label: "Geo Intelligence", icon: MapPin },
    ],
  },
  {
    group: "OPERATIONS",
    items: [
      { href: "/alerts", label: "Alert Triage", icon: ShieldAlert },
      { href: "/investigations", label: "Investigations", icon: SearchIcon },
    ],
  },
  {
    group: "REPORTING",
    items: [
      { href: "/reports", label: "Reports", icon: FileText },
    ],
  },
];

function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-30 flex h-screen flex-col border-r border-navy-700/80 bg-navy-950 transition-all duration-200 select-none",
        collapsed ? "w-[64px]" : "w-[240px]"
      )}
    >
      {/* Brand */}
      <div className="flex h-14 items-center gap-2.5 border-b border-navy-700/80 px-4 bg-navy-900/60">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded border border-indigo-500/30 bg-indigo-500/10 text-indigo-400">
          <Shield className="h-4 w-4" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="font-display text-sm font-semibold text-white tracking-tight leading-none">
              MuleTrace <span className="text-indigo-400">AI</span>
            </h1>
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500 mt-0.5">
              Financial Crime SOC
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-4">
        {navGroups.map((g) => (
          <div key={g.group} className="space-y-1">
            {!collapsed && (
              <p className="text-[10px] font-mono font-semibold tracking-wider text-slate-500 px-2 py-0.5 uppercase">
                {g.group}
              </p>
            )}
            <div className="space-y-0.5">
              {g.items.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    prefetch={true}
                    className={cn(
                      "flex items-center gap-2.5 rounded-[4px] px-2.5 py-2 text-xs font-medium transition-colors",
                      isActive
                        ? "bg-navy-800 text-white border-l-2 border-indigo-500 font-semibold"
                        : "text-slate-400 hover:bg-navy-900/80 hover:text-slate-200 border-l-2 border-transparent"
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon
                      className={cn(
                        "h-4 w-4 shrink-0 transition-colors",
                        isActive ? "text-indigo-400" : "text-slate-500"
                      )}
                    />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* System Status Footer */}
      {!collapsed && (
        <div className="border-t border-navy-700/80 p-3 bg-navy-900/40">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block" />
              Intelligence Engine
            </span>
            <span className="text-slate-500">v1.0</span>
          </div>
        </div>
      )}

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex h-9 items-center justify-center border-t border-navy-700/80 text-slate-500 transition-colors hover:bg-navy-900 hover:text-slate-300"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
      </button>
    </aside>
  );
}

export default React.memo(Sidebar);
