"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Briefcase,
  AlertTriangle,
  User,
  Clock,
  Shield,
  Brain,
  FileText,
  Activity,
  AlertCircle,
  RefreshCw,
  Cpu,
  CheckCircle2,
  HelpCircle,
  Info,
} from "lucide-react";
import { useInvestigations } from "@/hooks/useInvestigations";
import { fetchCaseIntelligence } from "@/lib/api";
import type { InvestigationIntelligence } from "@/lib/types";
import { cn, getRiskBg, getStatusColor } from "@/lib/utils";

// Mock evidence linked to cases (baseline preserved)
const caseEvidence: Record<string, { accounts: string[]; total_volume: string; alerts: number; timeline: { date: string; event: string }[] }> = {
  "CAS-2025-0045": {
    accounts: ["XXXX1001", "XXXX1002", "XXXX1003", "XXXX1004", "XXXX1005"],
    total_volume: "₹48.7L",
    alerts: 8,
    timeline: [
      { date: "Jul 24, 2025 14:32", event: "Alert ALT-2025-0001 triggered — Mule chain detected" },
      { date: "Jul 24, 2025 13:15", event: "Account XXXX1002 flagged as Fan-In collector" },
      { date: "Jul 23, 2025 22:40", event: "Velocity spike on XXXX1009 — 18 txns in 1 hour" },
      { date: "Jul 23, 2025 18:05", event: "Case opened by INV-882" },
    ],
  },
  "CAS-2025-0046": {
    accounts: ["XXXX1002", "XXXX1009", "XXXX1010", "XXXX1011"],
    total_volume: "₹25.8L",
    alerts: 5,
    timeline: [
      { date: "Jul 24, 2025 11:20", event: "Fan-In collector pattern confirmed" },
      { date: "Jul 23, 2025 16:45", event: "Case assigned to INV-445" },
    ],
  },
};

function formatModalityTitle(modality: string): string {
  switch (modality.toLowerCase()) {
    case "rules":
    case "modular_rules":
      return "Modular Rules (M5)";
    case "temporal":
    case "temporal_engine":
      return "Temporal Intelligence (M6)";
    case "graph":
    case "graph_engine":
      return "Graph Intelligence (M7)";
    case "tabular_ml":
    case "tabular_ml_xgboost":
      return "Tabular ML (M8)";
    case "graph_ml":
    case "graph_ml_graphsage":
      return "Graph ML / GNN (M9)";
    default:
      return modality.replace(/_/g, " ");
  }
}

function InvestigationIntelligencePanel({ caseNumber }: { caseNumber: string }) {
  const [intel, setIntel] = useState<InvestigationIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(true);

  const loadIntel = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCaseIntelligence(caseNumber);
      if (!isMounted.current) return;
      if (res.data) {
        setIntel(res.data);
      } else {
        setError("No intelligence data returned for this case.");
      }
    } catch (err) {
      if (!isMounted.current) return;
      setError(err instanceof Error ? err.message : "Failed to load intelligence");
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [caseNumber]);

  useEffect(() => {
    isMounted.current = true;
    loadIntel();
    return () => {
      isMounted.current = false;
    };
  }, [loadIntel]);

  if (loading) {
    return (
      <div className="glass-card p-5 space-y-3 animate-pulse col-span-1 lg:col-span-2">
        <div className="flex items-center justify-between">
          <div className="h-4 w-60 bg-navy-800 rounded" />
          <div className="h-4 w-20 bg-navy-800 rounded" />
        </div>
        <div className="h-24 bg-navy-900/50 rounded border border-navy-800" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="h-32 bg-navy-900/50 rounded border border-navy-800" />
          <div className="h-32 bg-navy-900/50 rounded border border-navy-800" />
        </div>
      </div>
    );
  }

  if (error || !intel) {
    return (
      <div className="glass-card p-4 border border-amber-500/30 bg-amber-500/5 text-slate-300 col-span-1 lg:col-span-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-amber-400 font-mono text-xs">
            <AlertCircle className="h-4 w-4" />
            <span>INTELLIGENCE PIPELINE OFFLINE: {caseNumber}</span>
          </div>
          <button
            onClick={loadIntel}
            className="flex items-center gap-1 font-mono text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            <RefreshCw className="h-3 w-3" /> RETRY PIPELINE
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="col-span-1 lg:col-span-2 space-y-4 animate-slide-up">
      {/* Header Banner */}
      <div className="glass-card p-4 border border-navy-700/80 bg-navy-900/95">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="flex h-7 w-7 items-center justify-center rounded border border-indigo-500/30 bg-indigo-500/10 text-indigo-400">
                <Cpu className="h-3.5 w-3.5" />
              </span>
              <h2 className="text-sm font-semibold text-white tracking-tight">
                Deterministic Risk Intelligence & Copilot Dossier
              </h2>
              <span className="badge bg-indigo-500/15 text-indigo-300 border-indigo-500/30 text-[10px] font-mono font-medium">
                M1–M12 PIPELINE
              </span>
              {intel.is_degraded && (
                <span className="badge bg-amber-500/15 text-amber-300 border-amber-500/30 text-[10px] font-mono">
                  DEGRADED MODE
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-slate-400 max-w-2xl">
              Deterministic fusion of Modular Rules, Temporal Velocity, Graph Centrality, Tabular ML, GraphSAGE embeddings, and Auditable Evidence Items. Strictly 0% external LLM hallucinations.
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Subject ID</span>
              <span className="text-indigo-400 font-semibold">{intel.subject_id}</span>
            </div>
            {intel.transaction_id && (
              <div className="border-l border-navy-700 pl-3">
                <span className="text-slate-500 block text-[10px] uppercase">Anchor Txn</span>
                <span className="text-slate-300">{intel.transaction_id}</span>
              </div>
            )}
            <button
              onClick={loadIntel}
              title="Refresh intelligence"
              className="p-1 rounded-[3px] border border-navy-700/60 bg-navy-800 text-slate-400 hover:text-white transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Fusion Score Gauge + Evidence Breakdown */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 pt-3 border-t border-navy-700/60">
          <div className="flex items-center gap-3 bg-navy-950/60 p-3 rounded-[3px] border border-navy-700/70">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">COMPOSITE RISK (M10)</span>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-xl font-bold font-mono text-white">
                  {(intel.composite_risk_score * 100).toFixed(1)}%
                </span>
                <span className={cn("badge text-[10px] px-1.5 py-0.5", getRiskBg(intel.risk_level))}>
                  {intel.risk_level}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 bg-navy-950/60 p-3 rounded-[3px] border border-navy-700/70">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">AUDITABLE EVIDENCE (M11)</span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xl font-bold font-mono text-white">
                  {intel.total_evidence_count} Items
                </span>
                <div className="flex gap-1">
                  {intel.severity_counts.CRITICAL ? (
                    <span className="badge bg-red-500/15 text-red-400 border-red-500/30 text-[9px] font-mono">
                      {intel.severity_counts.CRITICAL} Crit
                    </span>
                  ) : null}
                  {intel.severity_counts.HIGH ? (
                    <span className="badge bg-amber-500/15 text-amber-400 border-amber-500/30 text-[9px] font-mono">
                      {intel.severity_counts.HIGH} High
                    </span>
                  ) : null}
                  {intel.severity_counts.MEDIUM ? (
                    <span className="badge bg-blue-500/15 text-blue-400 border-blue-500/30 text-[9px] font-mono">
                      {intel.severity_counts.MEDIUM} Med
                    </span>
                  ) : null}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center bg-navy-950/60 p-3 rounded-[3px] border border-navy-700/70">
            <div className="w-full">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">COPILOT ACTIONS (M12)</span>
              <div className="flex items-center justify-between mt-0.5">
                <span className="text-xl font-bold font-mono text-white">
                  {intel.suggested_next_steps.length} Actions
                </span>
                <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1 font-medium">
                  Verified <CheckCircle2 className="h-3 w-3" />
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Modal Signal Contributions (M10 Risk Fusion) */}
      <div className="glass-card p-4">
        <div className="flex items-center justify-between border-b border-navy-700/60 pb-2 mb-3">
          <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 flex items-center gap-2">
            <Activity className="h-3.5 w-3.5 text-indigo-400" />
            Multi-Modal Signal Contributions (M10 Risk Fusion)
          </h3>
          <span className="text-[10px] font-mono text-slate-400">5 MODALITIES</span>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Deterministic weighted combination across 5 independent fraud modalities with dynamic weight redistribution.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
          {intel.risk_contributions.map((c) => (
            <div
              key={c.modality}
              className={cn(
                "p-2.5 rounded-[3px] border bg-navy-950/60 flex flex-col justify-between",
                c.is_available ? "border-navy-700/80" : "border-navy-800 opacity-60"
              )}
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono text-[11px] font-semibold text-slate-300 truncate" title={formatModalityTitle(c.modality)}>
                    {formatModalityTitle(c.modality)}
                  </span>
                  <span
                    className={cn(
                      "text-[9px] px-1 py-0.5 rounded-[2px] font-mono font-semibold",
                      c.is_available ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : "bg-slate-800 text-slate-500"
                    )}
                  >
                    {c.is_available ? "ACTIVE" : "N/A"}
                  </span>
                </div>

                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-base font-mono font-bold text-white">
                    {(c.normalized_value * 100).toFixed(0)}%
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    W: {(c.effective_weight * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="w-full bg-navy-800 h-1.5 rounded-[2px] mt-1.5 overflow-hidden border border-navy-700/50">
                  <div
                    className={cn(
                      "h-full transition-all duration-300",
                      c.normalized_value >= 0.75
                        ? "bg-red-500"
                        : c.normalized_value >= 0.5
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    )}
                    style={{ width: `${Math.min(100, Math.max(0, c.normalized_value * 100))}%` }}
                  />
                </div>
              </div>

              <div className="mt-2.5 pt-2 border-t border-navy-800 text-[10px]">
                <span className="text-slate-400 leading-tight block line-clamp-2" title={c.explanation}>
                  {c.explanation}
                </span>
                <span className="text-indigo-400 font-mono mt-1 block">
                  +{(c.weighted_score * 100).toFixed(1)} risk pts
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Investigation Copilot & Key Findings (M12) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Narrative & Findings */}
        <div className="glass-card p-4 space-y-3">
          <div className="border-b border-navy-700/60 pb-2">
            <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 flex items-center gap-2">
              <Brain className="h-3.5 w-3.5 text-indigo-400" />
              Deterministic Copilot Narrative & Findings (M12)
            </h3>
          </div>

          <div className="bg-navy-950/80 p-3 rounded-[3px] border border-navy-700 font-mono text-xs text-slate-300 leading-relaxed">
            <p className="font-semibold text-indigo-400 mb-1 text-[10px] uppercase tracking-wider">
              Executive Forensic Brief
            </p>
            {intel.investigation_summary}
          </div>

          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-2">Key Findings</span>
            <div className="space-y-2">
              {intel.key_findings.map((kf, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-[3px] bg-navy-950/50 border border-navy-700/80 flex items-start gap-2 text-xs"
                >
                  <span className={cn("badge text-[9px] px-1.5 py-0.5 shrink-0 mt-0.5", getRiskBg(kf.severity))}>
                    {kf.severity}
                  </span>
                  <div className="space-y-1">
                    <p className="text-slate-200 font-medium text-xs">{kf.finding}</p>
                    <div className="flex flex-wrap gap-1">
                      {kf.evidence_ids.map((eid) => (
                        <span key={eid} className="badge bg-navy-800 text-slate-400 font-mono text-[9px]">
                          {eid}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Suggested Next Steps */}
        <div className="glass-card p-4 space-y-3">
          <div className="border-b border-navy-700/60 pb-2">
            <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 flex items-center gap-2">
              <Shield className="h-3.5 w-3.5 text-indigo-400" />
              Recommended Investigation Actions (M12)
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Deterministic step-by-step procedures tailored to observed evidence and statutory compliance requirements.
          </p>

          <div className="space-y-2">
            {intel.suggested_next_steps.map((action) => (
              <div
                key={action.action_id}
                className="p-3 rounded-[3px] bg-navy-950/50 border border-navy-700/80 hover:border-navy-600 transition-colors"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "badge text-[9px] px-1.5 py-0.5 font-bold",
                        action.priority === "IMMEDIATE"
                          ? "bg-red-500/15 text-red-400 border-red-500/30"
                          : action.priority === "HIGH"
                          ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
                          : "bg-blue-500/15 text-blue-400 border-blue-500/30"
                      )}
                    >
                      {action.priority}
                    </span>
                    <span className="text-xs font-semibold text-white font-mono">{action.title}</span>
                  </div>
                  <span className="badge bg-navy-800 text-slate-400 font-mono text-[9px]">
                    {action.action_type}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mb-1.5 leading-relaxed">{action.description}</p>
                {action.related_evidence_ids && action.related_evidence_ids.length > 0 && (
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
                    <span>EVIDENCE:</span>
                    {action.related_evidence_ids.map((eid) => (
                      <span key={eid} className="text-indigo-400">
                        {eid}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Auditable Evidence Items (M11 Evidence Engine) */}
      <div className="glass-card p-4">
        <div className="flex items-center justify-between border-b border-navy-700/60 pb-2 mb-3">
          <div>
            <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 text-indigo-400" />
              Auditable Evidence Items (M11 Deterministic Evidence Engine)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Each item is an immutable, self-contained record of facts backed by transaction and entity references.
            </p>
          </div>
          <span className="badge bg-navy-800 text-slate-300 font-mono text-[10px]">
            {intel.evidence_items.length} VERIFIED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {intel.evidence_items.map((item) => (
            <div
              key={item.evidence_id}
              className="p-3 rounded-[3px] bg-navy-950/50 border border-navy-700/80 flex flex-col justify-between hover:border-navy-600 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <span className="font-mono text-[10px] font-semibold text-indigo-400">
                    {item.evidence_id}
                  </span>
                  <span className={cn("badge text-[9px] px-1.5 py-0.5", getRiskBg(item.severity))}>
                    {item.severity}
                  </span>
                </div>

                <p className="text-xs font-semibold text-white mb-1">{item.title}</p>
                <p className="text-xs text-slate-300 line-clamp-3 mb-2.5">{item.description}</p>
              </div>

              <div className="pt-2 border-t border-navy-800 text-[10px] font-mono space-y-0.5 text-slate-400">
                <div className="flex justify-between">
                  <span>CATEGORY:</span>
                  <span className="text-slate-300">{item.category}</span>
                </div>
                <div className="flex justify-between">
                  <span>SOURCE:</span>
                  <span className="text-slate-300">{item.source}</span>
                </div>
                {item.account_ids && item.account_ids.length > 0 && (
                  <div className="flex justify-between">
                    <span>ACCOUNTS:</span>
                    <span className="text-slate-300 truncate max-w-[140px]">{item.account_ids.join(", ")}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Follow-Up Questions & Audit Boundaries */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {intel.follow_up_questions && intel.follow_up_questions.length > 0 && (
          <div className="glass-card p-3.5">
            <h4 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 flex items-center gap-1.5 mb-2 border-b border-navy-700/60 pb-1.5">
              <HelpCircle className="h-3.5 w-3.5 text-indigo-400" />
              Recommended Investigator Inquiries
            </h4>
            <ul className="space-y-1">
              {intel.follow_up_questions.map((q, i) => (
                <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-indigo-400 font-mono font-bold">•</span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {intel.limitations && intel.limitations.length > 0 && (
          <div className="glass-card p-3.5">
            <h4 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 flex items-center gap-1.5 mb-2 border-b border-navy-700/60 pb-1.5">
              <Info className="h-3.5 w-3.5 text-slate-400" />
              Audit Scope & Pipeline Limitations
            </h4>
            <ul className="space-y-1">
              {intel.limitations.map((lim, i) => (
                <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                  <span className="text-slate-600 font-mono font-bold">•</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default function InvestigationsPage() {
  const { cases, loading, isLive } = useInvestigations();
  const [selectedCase, setSelectedCase] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="space-y-5 animate-fade-in">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-[140px] rounded" />)}
        </div>
      </div>
    );
  }

  const activeCase = selectedCase ? cases.find((c) => c.case_number === selectedCase) : null;
  const evidence = selectedCase ? caseEvidence[selectedCase] : null;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-navy-700/60 pb-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-white">Investigation Case Workspace</h1>
          <p className="mt-0.5 text-xs text-slate-400">
            Multi-modal syndicate cases, auditable evidence boards, and linked chronological activity
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-0.5 rounded-[3px] text-[10px] font-mono border",
            isLive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-slate-800/80 text-slate-400 border-slate-700"
          )}>
            <span className={cn("h-1.5 w-1.5 rounded-full", isLive ? "bg-emerald-400" : "bg-slate-400")} />
            {isLive ? "SURVEILLANCE LIVE" : "OFFLINE / MOCK"}
          </div>
        </div>
      </div>

      {/* Case Cards Grid */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {cases.map((c) => (
          <div
            key={c.case_number}
            onClick={() => setSelectedCase(c.case_number)}
            className={cn(
              "cursor-pointer p-3.5 rounded-[4px] border transition-colors",
              selectedCase === c.case_number
                ? "border-indigo-500 bg-navy-900 shadow-md ring-1 ring-indigo-500/40"
                : "border-navy-700/80 bg-navy-900/60 hover:bg-navy-900 hover:border-navy-600"
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex h-7 w-7 items-center justify-center rounded-[3px] border border-indigo-500/30 bg-indigo-500/10 text-indigo-400">
                <Briefcase className="h-3.5 w-3.5" />
              </div>
              <span className={cn("badge font-mono text-[10px]", getRiskBg(c.priority))}>{c.priority}</span>
            </div>
            <div className="mt-2.5">
              <p className="font-mono text-xs font-semibold text-indigo-400">{c.case_number}</p>
              <p className="mt-0.5 text-xs font-semibold text-white truncate">{c.title}</p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-navy-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span className={cn("badge text-[9px]", getStatusColor(c.case_status))}>{c.case_status.replace(/_/g, " ")}</span>
              <span className="flex items-center gap-1">
                <User className="h-3 w-3 text-slate-500" />
                {c.assigned_investigator_id}
              </span>
              <span className="flex items-center gap-1">
                <AlertTriangle className="h-3 w-3 text-slate-500" />
                {c.alerts_count} alerts
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Case Detail / Evidence Board */}
      {activeCase && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 animate-slide-up">
          {/* Case Overview */}
          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 border-b border-navy-700/60 pb-2 flex items-center gap-2">
              <Shield className="h-3.5 w-3.5 text-indigo-400" />
              Case Overview & Evidence Metrics
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center py-0.5 border-b border-navy-800">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Case Identifier</span>
                <span className="font-mono text-xs font-semibold text-indigo-400">{activeCase.case_number}</span>
              </div>
              <div className="flex justify-between items-center py-0.5 border-b border-navy-800">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Title</span>
                <span className="text-slate-200 text-right max-w-[250px] font-medium">{activeCase.title}</span>
              </div>
              <div className="flex justify-between items-center py-0.5 border-b border-navy-800">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Priority</span>
                <span className={cn("badge font-mono text-[10px]", getRiskBg(activeCase.priority))}>{activeCase.priority}</span>
              </div>
              <div className="flex justify-between items-center py-0.5 border-b border-navy-800">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Status</span>
                <span className={cn("badge font-mono text-[10px]", getStatusColor(activeCase.case_status))}>{activeCase.case_status.replace(/_/g, " ")}</span>
              </div>
              <div className="flex justify-between items-center py-0.5 border-b border-navy-800">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Assigned Officer</span>
                <span className="text-slate-200 font-mono">{activeCase.assigned_investigator_id}</span>
              </div>
              <div className="flex justify-between items-center py-0.5 border-b border-navy-800">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Linked Alerts</span>
                <span className="text-white font-mono font-semibold">{activeCase.alerts_count}</span>
              </div>
              {evidence && (
                <>
                  <div className="pt-2 flex justify-between items-center">
                    <span className="text-slate-400 font-mono text-[11px] uppercase">Combined Volume</span>
                    <span className="text-sm font-bold font-mono text-white">{evidence.total_volume}</span>
                  </div>
                  <div className="pt-2 border-t border-navy-800">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5 block">Linked Accounts</span>
                    <div className="flex flex-wrap gap-1">
                      {evidence.accounts.map((acc) => (
                        <span key={acc} className="badge bg-navy-800 border-navy-700 text-slate-300 font-mono text-[10px]">{acc}</span>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Evidence Timeline */}
          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 border-b border-navy-700/60 pb-2 flex items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-indigo-400" />
              Chronological Evidence Timeline
            </h3>
            {evidence?.timeline ? (
              <div className="relative space-y-0 pl-1">
                <div className="absolute left-[8px] top-2 bottom-2 w-px bg-navy-700" />
                {evidence.timeline.map((event, i) => (
                  <div key={i} className="relative flex gap-3 pb-3.5">
                    <div className="relative z-10 mt-1 h-2 w-2 shrink-0 rounded-full border border-indigo-400 bg-navy-950" />
                    <div>
                      <p className="text-[10px] font-mono text-slate-400">{event.date}</p>
                      <p className="mt-0.5 text-xs text-slate-200">{event.event}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs font-mono text-slate-500">Select a case to view its evidence timeline.</p>
            )}
          </div>

          {/* M13 Deterministic Risk Intelligence & Copilot Insights */}
          <InvestigationIntelligencePanel caseNumber={activeCase.case_number} />
        </div>
      )}
    </div>
  );
}
