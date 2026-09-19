"use client";

import React, { useState, useEffect, useCallback } from "react";
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

  const loadIntel = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCaseIntelligence(caseNumber);
      if (res.data) {
        setIntel(res.data);
      } else {
        setError("No intelligence data returned for this case.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load intelligence");
    } finally {
      setLoading(false);
    }
  }, [caseNumber]);

  useEffect(() => {
    loadIntel();
  }, [loadIntel]);

  if (loading) {
    return (
      <div className="glass-card p-6 space-y-4 animate-pulse col-span-1 lg:col-span-2">
        <div className="flex items-center justify-between">
          <div className="h-5 w-64 bg-slate-700/50 rounded" />
          <div className="h-5 w-24 bg-slate-700/50 rounded" />
        </div>
        <div className="h-28 bg-slate-800/40 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-40 bg-slate-800/40 rounded-xl" />
          <div className="h-40 bg-slate-800/40 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !intel) {
    return (
      <div className="glass-card p-5 border-amber-500/20 bg-amber-500/5 text-slate-300 col-span-1 lg:col-span-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-amber-400">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Intelligence pipeline offline for {caseNumber}</span>
          </div>
          <button
            onClick={loadIntel}
            className="flex items-center gap-1 text-xs text-accent hover:underline font-semibold"
          >
            <RefreshCw className="h-3 w-3" /> Retry Pipeline
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="col-span-1 lg:col-span-2 space-y-5 animate-slide-up">
      {/* Header Banner */}
      <div className="glass-card p-5 border-accent/30 bg-gradient-to-r from-navy-800/90 via-navy-800/70 to-accent/10">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/20 text-accent">
                <Cpu className="h-4 w-4" />
              </span>
              <h2 className="text-base font-bold text-white tracking-wide">
                Deterministic Risk Intelligence & Copilot Dossier
              </h2>
              <span className="badge bg-indigo-500/20 text-indigo-300 border-indigo-500/30 text-[10px] font-mono font-semibold">
                M1–M12 Pipeline
              </span>
              {intel.is_degraded && (
                <span className="badge bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px] font-mono">
                  DEGRADED MODE
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-slate-400 max-w-2xl">
              Deterministic fusion of Modular Rules, Temporal Velocity, Graph Centrality, Tabular ML, GraphSAGE embeddings, and Auditable Evidence Items. Strictly 0% external LLM hallucinations.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">SUBJECT ID</span>
              <span className="text-accent-glow font-semibold">{intel.subject_id}</span>
            </div>
            {intel.transaction_id && (
              <div className="border-l border-navy-600 pl-4">
                <span className="text-slate-500 block text-[10px]">ANCHOR TXN</span>
                <span className="text-slate-300">{intel.transaction_id}</span>
              </div>
            )}
            <button
              onClick={loadIntel}
              title="Refresh intelligence"
              className="p-1.5 rounded bg-navy-700/60 hover:bg-navy-700 text-slate-400 hover:text-white transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Fusion Score Gauge + Evidence Breakdown */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-navy-700/60">
          <div className="flex items-center gap-4 bg-navy-900/60 p-3.5 rounded-lg border border-navy-700">
            <div>
              <span className="text-[11px] font-medium text-slate-400 block">COMPOSITE RISK SCORE (M10)</span>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-2xl font-bold font-mono text-white">
                  {(intel.composite_risk_score * 100).toFixed(1)}%
                </span>
                <span className={cn("badge text-[10px] px-2 py-0.5", getRiskBg(intel.risk_level))}>
                  {intel.risk_level}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-navy-900/60 p-3.5 rounded-lg border border-navy-700">
            <div>
              <span className="text-[11px] font-medium text-slate-400 block">AUDITABLE EVIDENCE (M11)</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xl font-bold font-mono text-white">
                  {intel.total_evidence_count} Items
                </span>
                <div className="flex gap-1">
                  {intel.severity_counts.CRITICAL ? (
                    <span className="badge bg-red-500/20 text-red-400 border-red-500/30 text-[10px]">
                      {intel.severity_counts.CRITICAL} Critical
                    </span>
                  ) : null}
                  {intel.severity_counts.HIGH ? (
                    <span className="badge bg-amber-500/20 text-amber-400 border-amber-500/30 text-[10px]">
                      {intel.severity_counts.HIGH} High
                    </span>
                  ) : null}
                  {intel.severity_counts.MEDIUM ? (
                    <span className="badge bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px]">
                      {intel.severity_counts.MEDIUM} Med
                    </span>
                  ) : null}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center bg-navy-900/60 p-3.5 rounded-lg border border-navy-700">
            <div className="w-full">
              <span className="text-[11px] font-medium text-slate-400 block">COPILOT ACTIONS (M12)</span>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xl font-bold font-mono text-white">
                  {intel.suggested_next_steps.length} Recommended
                </span>
                <span className="text-xs text-accent-glow flex items-center gap-1 font-semibold">
                  Deterministic <CheckCircle2 className="h-3.5 w-3.5" />
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Modal Signal Contributions (M10 Risk Fusion) */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4 text-accent-glow" />
          Multi-Modal Signal Contributions (M10 Risk Fusion)
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Deterministic weighted combination across 5 independent fraud modalities with dynamic weight redistribution.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {intel.risk_contributions.map((c) => (
            <div
              key={c.modality}
              className={cn(
                "p-3 rounded-lg border bg-navy-900/50 flex flex-col justify-between",
                c.is_available ? "border-navy-700" : "border-navy-800 opacity-60"
              )}
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-200 truncate" title={formatModalityTitle(c.modality)}>
                    {formatModalityTitle(c.modality)}
                  </span>
                  <span
                    className={cn(
                      "text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold",
                      c.is_available ? "bg-emerald-500/15 text-emerald-400" : "bg-slate-700 text-slate-400"
                    )}
                  >
                    {c.is_available ? "ACTIVE" : "N/A"}
                  </span>
                </div>

                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-lg font-mono font-bold text-white">
                    {(c.normalized_value * 100).toFixed(0)}%
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Weight: {(c.effective_weight * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="w-full bg-navy-700 h-1.5 rounded-full mt-1.5 overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
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

              <div className="mt-3 pt-2 border-t border-navy-800">
                <span className="text-[10px] text-slate-400 leading-tight block line-clamp-2" title={c.explanation}>
                  {c.explanation}
                </span>
                <span className="text-[9px] text-accent-glow font-mono mt-1 block">
                  +{(c.weighted_score * 100).toFixed(1)} risk pts
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Investigation Copilot & Key Findings (M12) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Narrative & Findings */}
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Brain className="h-4 w-4 text-accent-glow" />
            Deterministic Copilot Summary & Key Findings (M12)
          </h3>

          <div className="bg-navy-900/80 p-3.5 rounded-lg border border-navy-700 text-xs text-slate-300 leading-relaxed">
            <p className="font-semibold text-slate-200 mb-1 text-[11px] uppercase tracking-wider text-accent-glow">
              Executive Narrative
            </p>
            {intel.investigation_summary}
          </div>

          <div>
            <span className="text-xs font-semibold text-slate-300 block mb-2">Key Findings</span>
            <div className="space-y-2">
              {intel.key_findings.map((kf, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-navy-900/40 border border-navy-700/80 flex items-start gap-2 text-xs"
                >
                  <span className={cn("badge text-[9px] px-1.5 py-0.5 shrink-0 mt-0.5", getRiskBg(kf.severity))}>
                    {kf.severity}
                  </span>
                  <div className="space-y-1">
                    <p className="text-slate-200 font-medium">{kf.finding}</p>
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
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Shield className="h-4 w-4 text-accent-glow" />
            Recommended Investigation Actions (M12)
          </h3>
          <p className="text-xs text-slate-400">
            Deterministic step-by-step procedures tailored to observed evidence and statutory compliance requirements.
          </p>

          <div className="space-y-2.5">
            {intel.suggested_next_steps.map((action) => (
              <div
                key={action.action_id}
                className="p-3.5 rounded-lg bg-navy-900/50 border border-navy-700/80 hover:border-accent/40 transition-colors"
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "badge text-[9px] px-2 py-0.5 font-bold",
                        action.priority === "IMMEDIATE"
                          ? "bg-red-500/20 text-red-400 border-red-500/30"
                          : action.priority === "HIGH"
                          ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                          : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                      )}
                    >
                      {action.priority}
                    </span>
                    <span className="text-xs font-semibold text-white">{action.title}</span>
                  </div>
                  <span className="badge bg-navy-800 text-slate-400 font-mono text-[9px]">
                    {action.action_type}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mb-2 leading-relaxed">{action.description}</p>
                {action.related_evidence_ids && action.related_evidence_ids.length > 0 && (
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span>Evidence:</span>
                    {action.related_evidence_ids.map((eid) => (
                      <span key={eid} className="font-mono text-accent-glow">
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
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileText className="h-4 w-4 text-accent-glow" />
              Auditable Evidence Items (M11 Deterministic Evidence Engine)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Each item is an immutable, self-contained record of facts backed by transaction and entity references.
            </p>
          </div>
          <span className="badge bg-navy-700 text-slate-300 font-mono text-xs">
            {intel.evidence_items.length} verified records
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {intel.evidence_items.map((item) => (
            <div
              key={item.evidence_id}
              className="p-3.5 rounded-lg bg-navy-900/50 border border-navy-700/80 flex flex-col justify-between hover:border-navy-600 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-2">
                  <span className="font-mono text-[10px] font-bold text-accent-glow">
                    {item.evidence_id}
                  </span>
                  <span className={cn("badge text-[9px] px-1.5 py-0.5", getRiskBg(item.severity))}>
                    {item.severity}
                  </span>
                </div>

                <p className="text-xs font-semibold text-white mb-1">{item.title}</p>
                <p className="text-xs text-slate-300 line-clamp-3 mb-3">{item.description}</p>
              </div>

              <div className="pt-2 border-t border-navy-800 text-[10px] space-y-1 text-slate-400">
                <div className="flex justify-between">
                  <span>Category:</span>
                  <span className="text-slate-300 font-medium">{item.category}</span>
                </div>
                <div className="flex justify-between">
                  <span>Source:</span>
                  <span className="text-slate-300 font-medium">{item.source}</span>
                </div>
                {item.account_ids && item.account_ids.length > 0 && (
                  <div className="flex justify-between">
                    <span>Accounts:</span>
                    <span className="font-mono text-slate-300">{item.account_ids.join(", ")}</span>
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
          <div className="glass-card p-4">
            <h4 className="text-xs font-semibold text-white flex items-center gap-1.5 mb-2">
              <HelpCircle className="h-3.5 w-3.5 text-accent-glow" />
              Recommended Investigator Follow-Up Questions
            </h4>
            <ul className="space-y-1.5">
              {intel.follow_up_questions.map((q, i) => (
                <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-accent font-bold mt-0.5">•</span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {intel.limitations && intel.limitations.length > 0 && (
          <div className="glass-card p-4">
            <h4 className="text-xs font-semibold text-white flex items-center gap-1.5 mb-2">
              <Info className="h-3.5 w-3.5 text-slate-400" />
              Audit Scope & Pipeline Limitations
            </h4>
            <ul className="space-y-1.5">
              {intel.limitations.map((lim, i) => (
                <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                  <span className="text-slate-600 font-bold mt-0.5">•</span>
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
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-[180px] rounded-xl" />)}
        </div>
      </div>
    );
  }

  const activeCase = selectedCase ? cases.find((c) => c.case_number === selectedCase) : null;
  const evidence = selectedCase ? caseEvidence[selectedCase] : null;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="page-header flex justify-between items-start">
        <p className="page-subtitle">
          Active investigation cases, evidence boards, and linked alert timelines
        </p>
        <div className={cn(
          "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border",
          isLive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-slate-500/10 text-slate-400 border-slate-500/20"
        )}>
          <span className="relative flex h-1.5 w-1.5">
            {isLive && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
            <span className={cn("relative inline-flex rounded-full h-1.5 w-1.5", isLive ? "bg-emerald-500" : "bg-slate-500")}></span>
          </span>
          {isLive ? "LIVE" : "OFFLINE / MOCK"}
        </div>
      </div>

      {/* Case Cards Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 animate-stagger">
        {cases.map((c) => (
          <div
            key={c.case_number}
            onClick={() => setSelectedCase(c.case_number)}
            className={cn(
              "glass-card-hover cursor-pointer p-5",
              selectedCase === c.case_number && "ring-1 ring-accent/40"
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/15 text-accent">
                <Briefcase className="h-5 w-5" />
              </div>
              <span className={cn("badge", getRiskBg(c.priority))}>{c.priority}</span>
            </div>
            <div className="mt-3">
              <p className="font-mono text-xs text-accent-glow">{c.case_number}</p>
              <p className="mt-1 text-sm font-semibold text-white">{c.title}</p>
            </div>
            <div className="mt-3 flex items-center gap-4 text-xs text-slate-400">
              <span className={cn("badge", getStatusColor(c.case_status))}>{c.case_status.replace(/_/g, " ")}</span>
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {c.assigned_investigator_id}
              </span>
              <span className="flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                {c.alerts_count} alerts
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Case Detail / Evidence Board */}
      {activeCase && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 animate-slide-up">
          {/* Case Overview */}
          <div className="glass-card p-5">
            <h3 className="mb-4 text-sm font-semibold text-white flex items-center gap-2">
              <Shield className="h-4 w-4 text-accent-glow" />
              Case Overview
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Case Number</span>
                <span className="font-mono text-accent-glow">{activeCase.case_number}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Title</span>
                <span className="text-white text-right max-w-[250px]">{activeCase.title}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Priority</span>
                <span className={cn("badge", getRiskBg(activeCase.priority))}>{activeCase.priority}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Status</span>
                <span className={cn("badge", getStatusColor(activeCase.case_status))}>{activeCase.case_status.replace(/_/g, " ")}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Assigned</span>
                <span className="text-white">{activeCase.assigned_investigator_id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Linked Alerts</span>
                <span className="text-white font-semibold">{activeCase.alerts_count}</span>
              </div>
              {evidence && (
                <>
                  <div className="border-t border-navy-600 pt-3 flex justify-between text-sm">
                    <span className="text-slate-400">Combined Volume</span>
                    <span className="text-lg font-bold text-white">{evidence.total_volume}</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 mb-2 block">Linked Accounts</span>
                    <div className="flex flex-wrap gap-1.5">
                      {evidence.accounts.map((acc) => (
                        <span key={acc} className="badge bg-navy-700 border-navy-600 text-slate-300 font-mono">{acc}</span>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Evidence Timeline */}
          <div className="glass-card p-5">
            <h3 className="mb-4 text-sm font-semibold text-white flex items-center gap-2">
              <Clock className="h-4 w-4 text-accent-glow" />
              Evidence Timeline
            </h3>
            {evidence?.timeline ? (
              <div className="relative space-y-0">
                <div className="absolute left-[7px] top-2 bottom-2 w-px bg-navy-600" />
                {evidence.timeline.map((event, i) => (
                  <div key={i} className="relative flex gap-4 pb-5">
                    <div className="relative z-10 mt-1.5 h-[15px] w-[15px] shrink-0 rounded-full border-2 border-accent bg-navy-900" />
                    <div>
                      <p className="text-xs text-slate-500">{event.date}</p>
                      <p className="mt-0.5 text-sm text-slate-300">{event.event}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Select a case to view its evidence timeline.</p>
            )}
          </div>

          {/* M13 Deterministic Risk Intelligence & Copilot Insights */}
          <InvestigationIntelligencePanel caseNumber={activeCase.case_number} />
        </div>
      )}
    </div>
  );
}
