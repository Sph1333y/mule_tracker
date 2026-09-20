"use client";

import React from "react";
import {
  ArrowLeftRight,
  ShieldAlert,
  Users,
  IndianRupee,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ArrowUpRight,
  Eye,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";
import { useDashboard } from "@/hooks/useDashboard";
import type { AlertRead } from "@/lib/types";
import { formatCurrencyCompact, formatNumber, getRiskBg, formatTimeAgo, cn } from "@/lib/utils";

import Link from "next/link";

// -----------------------------------------------------------------------------
// Custom Recharts Tooltip
// -----------------------------------------------------------------------------
function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload) return null;
  return (
    <div className="rounded-[4px] border border-navy-700 bg-navy-900/95 px-3 py-2 shadow-lg">
      <p className="text-xs font-mono font-medium text-slate-300 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-xs font-mono" style={{ color: p.color }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
}

// -----------------------------------------------------------------------------
// KPI Card Component
// -----------------------------------------------------------------------------
function KPICard({
  icon: Icon,
  label,
  value,
  trend,
  trendLabel,
  variant,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  trend?: "up" | "down";
  trendLabel?: string;
  variant: string;
}) {
  const cardClass =
    variant === "critical"
      ? "kpi-card-critical"
      : variant === "amber"
        ? "kpi-card-amber"
        : variant === "blue"
          ? "kpi-card-blue"
          : "kpi-card-emerald";

  const iconStyle =
    variant === "critical"
      ? "text-red-400 bg-red-500/10 border-red-500/20"
      : variant === "amber"
        ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
        : variant === "blue"
          ? "text-blue-400 bg-blue-500/10 border-blue-500/20"
          : "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";

  return (
    <div className={cn(cardClass, "p-4")}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">{label}</span>
        <div className={cn("flex h-7 w-7 items-center justify-center rounded-[4px] border", iconStyle)}>
          <Icon className="h-3.5 w-3.5" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <p className="font-mono text-2xl font-semibold tracking-tight text-white">{value}</p>
        {trend && (
          <div
            className={cn(
              "flex items-center gap-1 text-[11px] font-mono",
              trend === "up" ? "text-red-400" : "text-emerald-400"
            )}
          >
            {trend === "up" ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {trendLabel}
          </div>
        )}
      </div>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Risk Score Bar
// -----------------------------------------------------------------------------
function RiskScoreBar({ score }: { score: number }) {
  const color = score >= 80 ? "#ef4444" : score >= 60 ? "#f59e0b" : score >= 40 ? "#3b82f6" : "#10b981";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-[2px] bg-navy-800 border border-navy-700/50">
        <div className="h-full transition-all duration-300" style={{ width: `${score}%`, backgroundColor: color }} />
      </div>
      <span className="font-mono text-[11px] font-medium" style={{ color }}>
        {score}
      </span>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Dashboard Page
// -----------------------------------------------------------------------------
export default function DashboardPage() {
  const { data, loading, isLive, lastUpdated } = useDashboard();

  if (loading || !data) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-[104px] rounded" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="skeleton h-[320px] rounded" />
          <div className="skeleton h-[320px] rounded" />
        </div>
        <div className="skeleton h-[380px] rounded" />
      </div>
    );
  }

  const { kpis, risk_distribution, top_patterns, recent_alerts } = data;

  const riskDonutData = [
    { name: "Critical", value: risk_distribution.critical, color: "#ef4444" },
    { name: "High", value: risk_distribution.high, color: "#f59e0b" },
    { name: "Medium", value: risk_distribution.medium, color: "#3b82f6" },
    { name: "Low", value: risk_distribution.low, color: "#10b981" },
  ];

  const patternData = top_patterns.slice(0, 10).map((p) => ({
    name: p.pattern_name.length > 18 ? p.pattern_name.slice(0, 18) + "…" : p.pattern_name,
    hits: p.hit_count,
    fill:
      p.severity === "CRITICAL" ? "#ef4444" : p.severity === "HIGH" ? "#f59e0b" : p.severity === "MEDIUM" ? "#3b82f6" : "#10b981",
  }));

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-navy-700/60 pb-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-white">Executive SOC Overview</h1>
          <p className="mt-0.5 text-xs text-slate-400">Real-time surveillance of mule accounts, syndicates, and forensic risk indicators</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-0.5 rounded-[3px] text-[10px] font-mono border",
            isLive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-slate-800/80 text-slate-400 border-slate-700"
          )}>
            <span className={cn("h-1.5 w-1.5 rounded-full", isLive ? "bg-emerald-400" : "bg-slate-400")} />
            {isLive ? "LIVE INGESTION" : "OFFLINE / MOCK"}
          </div>
          {lastUpdated && <p className="text-[10px] font-mono text-slate-500">SYNC: {lastUpdated.toLocaleTimeString()}</p>}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          icon={ArrowLeftRight}
          label="Transactions (24h)"
          value={formatNumber(kpis.total_transactions_24h)}
          trend="up"
          trendLabel="+12.4%"
          variant="blue"
        />
        <KPICard
          icon={Users}
          label="Flagged Mule Accounts"
          value={formatNumber(kpis.flagged_mule_accounts)}
          trend="up"
          trendLabel="+8"
          variant="critical"
        />
        <KPICard
          icon={ShieldAlert}
          label="Active Alert Queue"
          value={formatNumber(kpis.active_alerts_count)}
          trend="up"
          trendLabel="+5"
          variant="amber"
        />
        <KPICard
          icon={IndianRupee}
          label="Volume at Risk"
          value={formatCurrencyCompact(kpis.total_volume_at_risk_inr)}
          trend="up"
          trendLabel="+₹3.2Cr"
          variant="critical"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Risk Distribution Donut */}
        <div className="glass-card p-4">
          <div className="mb-4 flex items-center justify-between border-b border-navy-700/60 pb-3">
            <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200">Account Risk Distribution</h3>
            <span className="text-[10px] font-mono text-slate-400">4 RISK TIERS</span>
          </div>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="50%" height={210}>
              <PieChart>
                <Pie
                  data={riskDonutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {riskDonutData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2.5">
              {riskDonutData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-[2px]" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-400 font-mono text-[11px] uppercase">{item.name}</span>
                  </div>
                  <span className="font-mono font-medium text-slate-200">{formatNumber(item.value)}</span>
                </div>
              ))}
              <div className="border-t border-navy-700/80 pt-2 flex items-center justify-between">
                <span className="text-[11px] font-mono uppercase text-slate-500">Total Monitored</span>
                <span className="font-mono text-sm font-semibold text-white">
                  {formatNumber(riskDonutData.reduce((a, b) => a + b.value, 0))}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Top Fraud Patterns */}
        <div className="glass-card p-4">
          <div className="mb-4 flex items-center justify-between border-b border-navy-700/60 pb-3">
            <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200">Top Fraud Pattern Hits</h3>
            <span className="text-[10px] font-mono text-slate-400">DETECTION FREQUENCY</span>
          </div>
          <ResponsiveContainer width="100%" height={210}>
            <BarChart data={patternData} layout="vertical" margin={{ left: 0, right: 16 }}>
              <XAxis type="number" tick={{ fontSize: 10, fill: "#64748b", fontFamily: "monospace" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8", fontFamily: "monospace" }} width={120} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="hits" radius={[0, 2, 2, 0]} barSize={12}>
                {patternData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Live Alert Triage Feed */}
      <div className="glass-card p-4">
        <div className="mb-3 flex items-center justify-between border-b border-navy-700/60 pb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200">Live Alert Triage Feed</h3>
            <span className="rounded-[3px] border border-navy-700 bg-navy-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
              ACTIVE PRIORITY
            </span>
          </div>
          <Link
            href="/alerts"
            className="flex items-center gap-1 text-xs font-mono text-indigo-400 transition-colors hover:text-indigo-300"
          >
            VIEW QUEUE <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>ALERT ID</th>
                <th>TITLE</th>
                <th>PATTERN</th>
                <th>SEVERITY</th>
                <th>RISK SCORE</th>
                <th>STATUS</th>
                <th>TIME</th>
                <th className="text-right">ACTION</th>
              </tr>
            </thead>
            <tbody>
              {recent_alerts.map((alert: AlertRead) => (
                <tr key={alert.id}>
                  <td className="font-mono text-xs font-medium text-indigo-400">{alert.alert_number}</td>
                  <td className="max-w-[200px] truncate text-xs text-slate-200 font-medium">{alert.title}</td>
                  <td>
                    <span className="rounded-[3px] border border-navy-700 bg-navy-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-300">
                      {alert.pattern_type.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td>
                    <span className={cn("badge", getRiskBg(alert.severity))}>
                      {alert.severity === "CRITICAL" && <AlertTriangle className="h-2.5 w-2.5" />}
                      {alert.severity}
                    </span>
                  </td>
                  <td>
                    <RiskScoreBar score={alert.risk_score} />
                  </td>
                  <td>
                    <span
                      className={cn(
                        "badge",
                        alert.alert_status === "NEW"
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                          : alert.alert_status === "ESCALATED"
                            ? "bg-red-500/10 text-red-400 border-red-500/30"
                            : alert.alert_status === "UNDER_INVESTIGATION"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                      )}
                    >
                      {alert.alert_status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="font-mono text-[11px] text-slate-400">{formatTimeAgo(alert.triggered_at)}</td>
                  <td className="text-right">
                    <Link
                      href="/alerts"
                      className="inline-flex rounded-[3px] border border-navy-700/60 p-1 text-slate-400 transition-colors hover:bg-navy-800 hover:text-white"
                      title="Inspect Alert"
                    >
                      <Eye className="h-3.5 w-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
