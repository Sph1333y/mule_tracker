"use client";

import React, { useState } from "react";
import { Filter, X, CheckCircle, AlertTriangle, Clock, ArrowUpCircle } from "lucide-react";
import { useAlerts } from "@/hooks/useAlerts";
import type { AlertRead } from "@/lib/types";
import { formatTimeAgo, cn, getRiskBg, getStatusColor } from "@/lib/utils";

// -----------------------------------------------------------------------------
// Triage Modal
// -----------------------------------------------------------------------------
function TriageModal({
  alert,
  onClose,
  onTriage,
}: {
  alert: AlertRead;
  onClose: () => void;
  onTriage: (id: string, status: string, notes: string) => void;
}) {
  const [status, setStatus] = useState(alert.alert_status);
  const [notes, setNotes] = useState("");

  const statuses = [
    { value: "UNDER_INVESTIGATION", label: "Under Investigation", icon: Clock, color: "text-amber-400" },
    { value: "ESCALATED", label: "Escalated", icon: ArrowUpCircle, color: "text-red-400" },
    { value: "CLOSED_FALSE_POSITIVE", label: "Closed — False Positive", icon: X, color: "text-slate-400" },
    { value: "CLOSED_CONFIRMED", label: "Closed — Confirmed", icon: CheckCircle, color: "text-emerald-400" },
  ];

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/70" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 z-50 w-[500px] -translate-x-1/2 -translate-y-1/2 animate-fade-in">
        <div className="rounded-[4px] border border-navy-700 bg-navy-900/95 p-5 shadow-2xl">
          <div className="flex items-center justify-between mb-4 border-b border-navy-700/80 pb-3">
            <div>
              <h3 className="font-mono text-xs uppercase tracking-wider font-semibold text-white">Triage Disposition</h3>
              <p className="mt-0.5 font-mono text-xs text-indigo-400">{alert.alert_number}</p>
            </div>
            <button
              onClick={onClose}
              className="rounded-[3px] border border-navy-700/60 p-1 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="rounded-[4px] border border-navy-700/80 bg-navy-950/60 p-3 mb-4">
            <p className="text-xs text-slate-200 font-medium">{alert.title}</p>
            {alert.description && <p className="mt-1 text-[11px] font-mono text-slate-400">{alert.description}</p>}
          </div>

          {/* Status Selection */}
          <div className="mb-4">
            <label className="mb-2 block text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Select Disposition State
            </label>
            <div className="grid grid-cols-2 gap-2">
              {statuses.map((s) => {
                const Icon = s.icon;
                return (
                  <button
                    key={s.value}
                    onClick={() => setStatus(s.value)}
                    className={cn(
                      "flex items-center gap-2 rounded-[3px] border p-2.5 text-left text-xs font-mono transition-colors",
                      status === s.value
                        ? "border-indigo-500 bg-indigo-500/15 text-white font-semibold"
                        : "border-navy-700 bg-navy-800/60 text-slate-400 hover:border-navy-600 hover:bg-navy-800"
                    )}
                  >
                    <Icon className={cn("h-3.5 w-3.5", s.color)} />
                    <span className="truncate">{s.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Notes */}
          <div className="mb-4">
            <label className="mb-1.5 block text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Forensic Notes / Justification
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record forensic evidence, rationale, or instructions..."
              rows={3}
              className="w-full rounded-[3px] border border-navy-700 bg-navy-950 p-2.5 font-mono text-xs text-white placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 border-t border-navy-700/80 pt-3">
            <button
              onClick={onClose}
              className="rounded-[3px] border border-navy-700 bg-navy-800/80 px-3 py-1.5 font-mono text-xs text-slate-300 hover:bg-navy-700 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => onTriage(alert.id, status, notes)}
              className="rounded-[3px] bg-indigo-600 px-3.5 py-1.5 font-mono text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
            >
              Commit Disposition
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// -----------------------------------------------------------------------------
// Alerts Page
// -----------------------------------------------------------------------------
export default function AlertsPage() {
  const [triageTarget, setTriageTarget] = useState<AlertRead | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { alerts, pagination, loading, triage, triaging, isLive } = useAlerts({
    severity: severityFilter || undefined,
    alert_status: statusFilter || undefined,
  });

  const handleTriage = async (id: string, status: string, notes: string) => {
    try {
      await triage(id, { alert_status: status, notes });
      setTriageTarget(null);
    } catch (err) {
      console.error("Failed to triage:", err);
      // In a real app, show a toast notification here
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-navy-700/60 pb-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-white">Suspicious Alert Triage Queue</h1>
          <p className="mt-0.5 text-xs text-slate-400">
            Surveillance alert prioritization, disposition workflows, and forensic escalation
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-0.5 rounded-[3px] text-[10px] font-mono border",
            isLive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-slate-800/80 text-slate-400 border-slate-700"
          )}>
            <span className={cn("h-1.5 w-1.5 rounded-full", isLive ? "bg-emerald-400" : "bg-slate-400")} />
            {isLive ? "QUEUE ACTIVE" : "OFFLINE / MOCK"}
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-card flex flex-wrap items-center gap-3 p-3">
        <Filter className="h-3.5 w-3.5 text-slate-500 shrink-0" />
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-mono uppercase text-slate-500 mr-1">Severity:</span>
          {["", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={cn(
                "rounded-[3px] px-2.5 py-1 text-[11px] font-mono font-medium transition-colors",
                severityFilter === s
                  ? s === "CRITICAL"
                    ? "bg-red-500/15 text-red-400 border border-red-500/40"
                    : s === "HIGH"
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                      : s === "MEDIUM"
                        ? "bg-blue-500/15 text-blue-400 border border-blue-500/40"
                        : s === "LOW"
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/40"
                          : "bg-indigo-600 text-white border border-indigo-500"
                  : "border border-navy-700 bg-navy-800/60 text-slate-400 hover:text-slate-200 hover:bg-navy-800"
              )}
            >
              {s || "ALL"}
            </button>
          ))}
        </div>
        <div className="h-4 w-px bg-navy-700 hidden sm:block" />
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-mono uppercase text-slate-500 mr-1">Status:</span>
          {["", "NEW", "UNDER_INVESTIGATION", "ESCALATED"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                "rounded-[3px] px-2.5 py-1 text-[11px] font-mono font-medium transition-colors",
                statusFilter === s
                  ? "bg-indigo-600 text-white border border-indigo-500"
                  : "border border-navy-700 bg-navy-800/60 text-slate-400 hover:text-slate-200 hover:bg-navy-800"
              )}
            >
              {s ? s.replace(/_/g, " ") : "ALL"}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="space-y-2 p-4">
            {[...Array(8)].map((_, i) => <div key={i} className="skeleton h-9 rounded" />)}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ALERT ID</th>
                  <th>INCIDENT TITLE</th>
                  <th>PATTERN</th>
                  <th>SEVERITY</th>
                  <th>RISK SCORE</th>
                  <th>STATUS</th>
                  <th>TRIGGERED</th>
                  <th className="text-right">ACTION</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td className="font-mono text-xs font-medium text-indigo-400">{alert.alert_number}</td>
                    <td className="max-w-[220px] truncate text-xs text-slate-200 font-medium">{alert.title}</td>
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
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-[2px] bg-navy-800 border border-navy-700/50">
                          <div
                            className="h-full transition-all duration-300"
                            style={{
                              width: `${alert.risk_score}%`,
                              backgroundColor: alert.risk_score >= 80 ? "#ef4444" : alert.risk_score >= 60 ? "#f59e0b" : "#3b82f6",
                            }}
                          />
                        </div>
                        <span className="font-mono text-[11px] font-medium text-slate-300">{alert.risk_score}</span>
                      </div>
                    </td>
                    <td>
                      <span className={cn("badge", getStatusColor(alert.alert_status))}>
                        {alert.alert_status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="font-mono text-[11px] text-slate-400">{formatTimeAgo(alert.triggered_at)}</td>
                    <td className="text-right">
                      <button
                        onClick={() => setTriageTarget(alert)}
                        disabled={triaging === alert.id}
                        className={cn(
                          "rounded-[3px] border px-2.5 py-1 font-mono text-[11px] font-medium transition-colors",
                          triaging === alert.id
                            ? "border-navy-700 bg-navy-800 text-slate-500 cursor-not-allowed"
                            : "border-navy-700 bg-navy-800/80 text-indigo-400 hover:bg-navy-700 hover:text-white"
                        )}
                      >
                        {triaging === alert.id ? "UPDATING..." : "TRIAGE"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {pagination && (
          <div className="flex items-center justify-between border-t border-navy-700/60 px-4 py-2.5 bg-navy-900/40">
            <p className="font-mono text-[11px] text-slate-400">
              TOTAL RECORDS: {pagination.total_items}
            </p>
          </div>
        )}
      </div>

      {/* Triage Modal */}
      {triageTarget && (
        <TriageModal
          alert={triageTarget}
          onClose={() => setTriageTarget(null)}
          onTriage={handleTriage}
        />
      )}
    </div>
  );
}
