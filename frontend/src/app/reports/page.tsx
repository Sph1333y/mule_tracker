"use client";

import React, { useState } from "react";
import {
  FileText,
  Plus,
  Download,
  X,
  FileJson,
  Sparkles,
  Send,
  AlertTriangle,
  User,
  Mail,
  Phone,
  DollarSign,
  Calendar,
  Hash,
  Eye,
  RefreshCw,
  MessageSquareWarning,
  ClipboardList,
} from "lucide-react";
import { fetchGraphTrace } from "@/lib/api";
import { useReports } from "@/hooks/useReports";
import type { ReportRead, ReportGenerateRequest } from "@/lib/types";
import { formatDate, cn, getStatusColor } from "@/lib/utils";
import { jsPDF } from "jspdf";

// -----------------------------------------------------------------------------
// Helper: Parse complaint JSON from summary_text
// -----------------------------------------------------------------------------
interface ComplaintData {
  transaction_id?: string;
  victim_name?: string;
  victim_email?: string;
  victim_phone?: string | null;
  incident_type?: string;
  amount_lost?: number;
  incident_date?: string | null;
  incidentDate?: string | null;
  date?: string | null;
  date_of_incident?: string | null;
  timestamp?: string | null;
  description?: string;
}

function parseComplaintData(summaryText: string | null): (ComplaintData & { display_date: string }) | null {
  if (!summaryText) return null;
  try {
    const data = JSON.parse(summaryText);
    const rawDate = data.incident_date || data.incidentDate || data.date || data.date_of_incident || data.timestamp || null;
    return {
      ...data,
      display_date: rawDate ? formatDate(rawDate) : "Not provided",
    };
  } catch {
    return null;
  }
}

// -----------------------------------------------------------------------------
// Complaint Detail Modal — View full complaint + Generate Report
// -----------------------------------------------------------------------------
function ComplaintDetailModal({
  report,
  onClose,
  onGenerate,
}: {
  report: ReportRead;
  onClose: () => void;
  onGenerate: (payload: ReportGenerateRequest) => Promise<ReportRead | null>;
}) {
  const complaint = parseComplaintData(report.summary_text);
  const [generating, setGenerating] = useState(false);

  const handleGenerateReport = async () => {
    if (!complaint?.transaction_id) {
      alert("No transaction ID provided in this complaint.");
      return;
    }

    setGenerating(true);
    try {
      // Analyze dataset correlation using Deep Graph Tracing
      const traceRes = await fetchGraphTrace(complaint.transaction_id).catch(() => null);

      if (!traceRes || !traceRes.success) {
        alert("Not applicable or not valid \u2014 Transaction ID not found in dataset.");
        setGenerating(false);
        return;
      }

      const datasetContext = `\n\n[DEEP GRAPH ANALYSIS]\n- Searched UTR: ${complaint.transaction_id}\n- Result: ${traceRes.data?.path_summary}`;

      await onGenerate({
        report_type: "CYBERCRIME_SUMMARY",
        title: `Investigation Report \u2014 ${report.report_number} \u2014 ${complaint?.victim_name || "Unknown"}`,
        summary_notes: `AUTO-ANALYZED INVESTIGATION REPORT\nComplaint Ref: ${report.report_number}\nIncident Date: ${complaint?.display_date || "N/A"}\nVictim Name: ${complaint?.victim_name || "N/A"}\nIncident Category: ${complaint?.incident_type || "N/A"}\nReported Amount Lost: \u20b9${complaint?.amount_lost?.toLocaleString("en-IN") || "N/A"}\nVictim Description: ${complaint?.description || "N/A"}${datasetContext}`,
        include_graph_visualization: true,
      });
    } catch (err) {
      console.error("Failed to generate report:", err);
    }
    setGenerating(false);
    onClose();
  };

  const fields = [
    { icon: Hash, label: "Transaction ID", value: complaint?.transaction_id },
    { icon: User, label: "Victim Name", value: complaint?.victim_name },
    { icon: Mail, label: "Email", value: complaint?.victim_email },
    { icon: Phone, label: "Phone", value: complaint?.victim_phone || "Not provided" },
    { icon: AlertTriangle, label: "Incident Type", value: complaint?.incident_type?.replace(/_/g, " ") },
    { icon: DollarSign, label: "Amount Lost", value: complaint?.amount_lost ? `₹${complaint.amount_lost.toLocaleString("en-IN")}` : "N/A" },
    { icon: Calendar, label: "Incident Date", value: complaint?.display_date || "Not provided" },
  ];

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 z-50 w-[620px] max-h-[90vh] -translate-x-1/2 -translate-y-1/2 animate-slide-up overflow-y-auto">
        <div className="glass-card p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
                <MessageSquareWarning className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-display text-lg font-bold text-white">Victim Complaint</h3>
                <p className="text-xs font-mono text-emerald-400">{report.report_number}</p>
              </div>
            </div>
            <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-navy-700 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Complaint title */}
          <div className="mb-4 rounded-lg border border-navy-600 bg-navy-800/50 p-3">
            <p className="text-xs text-slate-500 mb-1">Title</p>
            <p className="text-sm font-medium text-white">{report.title}</p>
          </div>

          {/* Fields Grid */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            {fields.map((field) => {
              const Icon = field.icon;
              return (
                <div key={field.label} className="rounded-lg border border-navy-600 bg-navy-800/50 p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Icon className="h-3 w-3 text-slate-500" />
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">{field.label}</p>
                  </div>
                  <p className="text-xs font-medium text-white">{field.value || "—"}</p>
                </div>
              );
            })}
          </div>

          {/* Description */}
          {complaint?.description && (
            <div className="mb-5 rounded-lg border border-navy-600 bg-navy-800/50 p-3">
              <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-1">Description</p>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{complaint.description}</p>
            </div>
          )}

          {/* Status + Submitted */}
          <div className="flex items-center gap-3 mb-5">
            <span className={cn("badge", getStatusColor(report.status))}>{report.status}</span>
            <span className="text-xs text-slate-500">Submitted: {formatDate(report.generated_at)}</span>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 border-t border-navy-600/50 pt-4">
            <button onClick={onClose} className="rounded-lg border border-navy-600 px-4 py-2 text-sm text-slate-400 hover:bg-navy-700">
              Close
            </button>
            <button
              onClick={handleGenerateReport}
              disabled={generating}
              className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow hover:bg-accent/90 transition-all disabled:opacity-40"
            >
              {generating ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Generate Investigation Report
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// -----------------------------------------------------------------------------
// Report Generator Modal (existing)
// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------
function ReportGeneratorModal({
  onClose,
  onGenerate,
}: {
  onClose: () => void;
  onGenerate: (payload: ReportGenerateRequest) => Promise<ReportRead | null>;
}) {
  const [reportType, setReportType] = useState("STR");
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [generating, setGenerating] = useState(false);

  const reportTypes = [
    { value: "STR", label: "Suspicious Transaction Report", desc: "For FIU-IND filing under PMLA" },
    { value: "CTR", label: "Currency Transaction Report", desc: "High-value cash transaction reporting" },
    { value: "CYBERCRIME_SUMMARY", label: "Cybercrime Summary", desc: "Investigation summary for LEA" },
    { value: "EXECUTIVE_BRIEF", label: "Executive Brief", desc: "Weekly/Monthly executive overview" },
  ];

  const handleGenerate = async () => {
    if (!title.trim()) return;
    setGenerating(true);
    await onGenerate({
      report_type: reportType,
      title,
      summary_notes: notes || undefined,
      include_graph_visualization: true,
    });
    setGenerating(false);
    onClose();
  };

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 z-50 w-[560px] -translate-x-1/2 -translate-y-1/2 animate-slide-up">
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 text-accent">
                <FileText className="h-4 w-4" />
              </div>
              <h3 className="font-display text-lg font-bold text-white">Generate Report</h3>
            </div>
            <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-navy-700 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Report Type */}
          <div className="mb-4">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Report Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {reportTypes.map((rt) => (
                <button
                  key={rt.value}
                  onClick={() => setReportType(rt.value)}
                  className={cn(
                    "rounded-lg border p-3 text-left transition-all",
                    reportType === rt.value
                      ? "border-accent/50 bg-accent/10"
                      : "border-navy-600 bg-navy-800 hover:border-navy-500"
                  )}
                >
                  <p className="text-xs font-semibold text-white">{rt.label}</p>
                  <p className="mt-0.5 text-[10px] text-slate-500">{rt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Title */}
          <div className="mb-4">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Report Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., STR — Mule Ring Western Region"
              className="w-full rounded-lg border border-navy-600 bg-navy-800 p-3 text-sm text-white placeholder:text-slate-600 focus:border-accent focus:outline-none"
            />
          </div>

          {/* AI Narrative Notes */}
          <div className="mb-5">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-accent-glow" />
              Executive Narrative Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add investigation summary for AI narrative generation..."
              rows={4}
              className="w-full rounded-lg border border-navy-600 bg-navy-800 p-3 text-sm text-white placeholder:text-slate-600 focus:border-accent focus:outline-none resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button onClick={onClose} className="rounded-lg border border-navy-600 px-4 py-2 text-sm text-slate-400 hover:bg-navy-700">
              Cancel
            </button>
            <button
              onClick={handleGenerate}
              disabled={!title.trim() || generating}
              className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow hover:bg-accent/90 transition-all disabled:opacity-40"
            >
              {generating ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              Generate Report
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// -----------------------------------------------------------------------------
// Victim Complaint Card
// -----------------------------------------------------------------------------
function ComplaintCard({
  report,
  onView,
}: {
  report: ReportRead;
  onView: () => void;
}) {
  const complaint = parseComplaintData(report.summary_text);

  return (
    <div className="glass-card-sm group relative overflow-hidden rounded-xl border border-navy-600/50 bg-navy-800/40 p-4 transition-all hover:border-emerald-500/30 hover:bg-navy-800/60">
      {/* Glow accent */}
      <div className="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-emerald-500/50 via-emerald-400/30 to-transparent" />

      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-400">
            <MessageSquareWarning className="h-4 w-4" />
          </div>
          <div>
            <p className="font-mono text-xs text-emerald-400 font-medium">{report.report_number}</p>
            <p className="text-[10px] text-slate-500">{formatDate(report.generated_at)}</p>
          </div>
        </div>
        <span className={cn("badge text-[10px]", getStatusColor(report.status))}>{report.status}</span>
      </div>

      {complaint && (
        <div className="space-y-2 mb-3">
          <div className="flex items-center gap-2">
            <User className="h-3 w-3 text-slate-500" />
            <span className="text-xs text-white font-medium">{complaint.victim_name}</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-3 w-3 text-amber-400" />
            <span className="text-xs text-amber-300">{complaint.incident_type?.replace(/_/g, " ")}</span>
          </div>
          {complaint.amount_lost && (
            <div className="flex items-center gap-2">
              <DollarSign className="h-3 w-3 text-red-400" />
              <span className="text-xs text-red-300 font-medium">₹{complaint.amount_lost.toLocaleString("en-IN")}</span>
            </div>
          )}
          {complaint.description && (
            <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{complaint.description}</p>
          )}
        </div>
      )}

      <button
        onClick={onView}
        className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-navy-500 bg-navy-700/50 px-3 py-1.5 text-xs font-medium text-slate-300 transition-all hover:border-emerald-500/40 hover:text-emerald-300"
      >
        <Eye className="h-3 w-3" />
        View Details & Generate Report
      </button>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Reports Page
// -----------------------------------------------------------------------------
export default function ReportsPage() {
  const [showGenerator, setShowGenerator] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");
  const [selectedComplaint, setSelectedComplaint] = useState<ReportRead | null>(null);

  const {
    victimComplaints,
    generatedReports,
    loading,
    refetch,
    generate,
    isLive,
    newComplaintCount,
  } = useReports(typeFilter);

  const handleDownloadPdf = (report: ReportRead) => {
    try {
      const doc = new jsPDF();
      
      // Title Header
      doc.setFontSize(22);
      doc.setTextColor(30, 58, 138); // Navy blue
      doc.text("OFFICIAL INVESTIGATION REPORT", 20, 20);
      
      // Meta Data Section
      doc.setFontSize(11);
      doc.setTextColor(80, 80, 80);
      doc.text(`Report Title: ${report.title || "Cybercrime Summary"}`, 20, 32);
      doc.text(`Report Tracking ID: ${report.report_number}`, 20, 38);
      doc.text(`Generation Date: ${formatDate(report.generated_at)}`, 20, 44);
      doc.text(`Case Status: ${report.status}`, 20, 50);
      
      // Line separator
      doc.setDrawColor(200, 200, 200);
      doc.line(20, 56, 190, 56);
      
      let currentY = 66;

      // Executive Summary
      if (report.summary_text) {
        doc.setFontSize(14);
        doc.setTextColor(30, 58, 138);
        doc.text("Detailed Analysis & Executive Summary", 20, currentY);
        currentY += 8;
        
        doc.setFontSize(11);
        doc.setTextColor(40, 40, 40);
        // Word wrap the summary text to fit the page width
        const splitText = doc.splitTextToSize(report.summary_text, 170);
        doc.text(splitText, 20, currentY);
        currentY += (splitText.length * 5) + 15;
      }

      // Actionable Advice Section
      doc.setDrawColor(220, 220, 220);
      doc.line(20, currentY - 5, 190, currentY - 5);
      
      doc.setFontSize(14);
      doc.setTextColor(220, 38, 38); // Red emphasis
      doc.text("Next Steps & Actionable Advice", 20, currentY + 5);
      
      doc.setFontSize(11);
      doc.setTextColor(0, 0, 0);
      const adviceText = "You can save your money and assist in the recovery of stolen funds by giving this detailed report to higher officials like the Police, CBI, or FIU-IND. We strongly recommend filing this exact document with your local Cybercrime Station or through the National Cyber Crime Reporting Portal. Providing this deep-traced evidence drastically increases the chances of freezing the destination accounts and recovering your assets.";
      
      const splitAdvice = doc.splitTextToSize(adviceText, 170);
      doc.text(splitAdvice, 20, currentY + 13);
      
      doc.save(`${report.report_number}.pdf`);
    } catch (err) {
      console.error("PDF generation failed:", err);
      alert("Failed to generate PDF locally.");
    }
  };

  const handleDownloadJson = (report: ReportRead) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
    const dlAnchorElem = document.createElement("a");
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `${report.report_number}.json`);
    document.body.appendChild(dlAnchorElem);
    dlAnchorElem.click();
    document.body.removeChild(dlAnchorElem);
  };

  const reportTypeColor: Record<string, string> = {
    STR: "bg-red-500/15 text-red-400 border-red-500/30",
    CTR: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    CYBERCRIME_SUMMARY: "bg-violet-500/15 text-violet-400 border-violet-500/30",
    EXECUTIVE_BRIEF: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    VICTIM_COMPLAINT: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  };

  const filterTypes = [
    { value: "", label: "All" },
    { value: "VICTIM_COMPLAINT", label: "Victim Complaints" },
    { value: "STR", label: "STR" },
    { value: "CTR", label: "CTR" },
    { value: "CYBERCRIME_SUMMARY", label: "Cybercrime" },
    { value: "EXECUTIVE_BRIEF", label: "Executive Brief" },
  ];

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <p className="page-subtitle">
            Manage compliance reports & victim complaints from the User Portal
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 rounded-lg border border-navy-600 bg-navy-800 px-3 py-2 text-xs text-slate-400 hover:text-white hover:bg-navy-700 transition-all"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setShowGenerator(true)}
            className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow hover:bg-accent/90 transition-all"
          >
            <Plus className="h-4 w-4" />
            Generate Report
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="glass-card flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">Type:</span>
          {filterTypes.map((ft) => (
          <button
            key={ft.value}
            onClick={() => setTypeFilter(ft.value)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium transition-all",
              typeFilter === ft.value
                ? "bg-accent/20 text-accent-glow border border-accent/30"
                : "border border-navy-600 bg-navy-800 text-slate-400 hover:text-white"
            )}
          >
            {ft.label}
            {ft.value === "VICTIM_COMPLAINT" && victimComplaints.length > 0 && (
              <span className="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-emerald-500/20 px-1 text-[10px] text-emerald-400">
                {victimComplaints.length}
              </span>
            )}
          </button>
        ))}
        </div>
        
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

      {loading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
        </div>
      ) : (
        <>
          {/* ── Victim Complaints Section ── */}
          {(typeFilter === "" || typeFilter === "VICTIM_COMPLAINT") && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <ClipboardList className="h-4 w-4 text-emerald-400" />
                <h2 className="text-sm font-semibold text-white">
                  Incoming Victim Complaints
                </h2>
                <span className="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-emerald-500/20 px-1.5 text-[10px] font-bold text-emerald-400">
                  {victimComplaints.length}
                </span>
                <div className="flex items-center gap-1 ml-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span className="text-[10px] text-emerald-400/70">Live from User Portal</span>
                </div>
                {newComplaintCount > 0 && (
                  <span className="ml-auto flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                    +{newComplaintCount} new since last view
                  </span>
                )}
              </div>
              
              {victimComplaints.length === 0 ? (
                <div className="glass-card p-10 text-center text-sm text-slate-500 border border-dashed border-emerald-500/20">
                  No victim complaints have been received yet from the User Portal.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                  {victimComplaints.map((report) => (
                    <ComplaintCard
                      key={report.id}
                      report={report}
                      onView={() => setSelectedComplaint(report)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Generated Reports Table ── */}
          {(typeFilter === "" || typeFilter !== "VICTIM_COMPLAINT") && (
            <div className="glass-card overflow-hidden">
              <div className="flex items-center gap-2 px-5 pt-4 pb-2">
                <FileText className="h-4 w-4 text-accent-glow" />
                <h2 className="text-sm font-semibold text-white">Generated Reports</h2>
              </div>
              {generatedReports.length === 0 && typeFilter !== "" ? (
                <div className="p-10 text-center text-sm text-slate-500">
                  No reports found for this filter.
                </div>
              ) : generatedReports.length === 0 ? (
                <div className="p-10 text-center text-sm text-slate-500">
                  No generated reports yet. Click &quot;Generate Report&quot; to create one.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Report ID</th>
                        <th>Type</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Generated</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {generatedReports.map((report) => (
                        <tr key={report.id}>
                          <td className="font-mono text-xs text-accent-glow">{report.report_number}</td>
                          <td>
                            <span className={cn("badge", reportTypeColor[report.report_type] || "bg-slate-500/15 text-slate-400 border-slate-500/30")}>
                              {report.report_type}
                            </span>
                          </td>
                          <td className="max-w-[280px]">
                            <p className="text-xs font-medium text-white truncate">{report.title}</p>
                            {report.summary_text && (
                              <p className="mt-0.5 text-[11px] text-slate-500 truncate max-w-[280px]">{report.summary_text}</p>
                            )}
                          </td>
                          <td>
                            <span className={cn("badge", getStatusColor(report.status))}>{report.status}</span>
                          </td>
                          <td className="text-xs text-slate-500">{formatDate(report.generated_at)}</td>
                          <td>
                            <div className="flex items-center gap-1">
                              {report.file_path && (
                                <button
                                  onClick={() => handleDownloadPdf(report)}
                                  className="flex items-center gap-1 rounded-lg border border-navy-600 bg-navy-800 px-2 py-1 text-xs text-slate-400 hover:text-white hover:bg-navy-700"
                                >
                                  <Download className="h-3 w-3" /> PDF
                                </button>
                              )}
                              <button
                                onClick={() => handleDownloadJson(report)}
                                className="flex items-center gap-1 rounded-lg border border-navy-600 bg-navy-800 px-2 py-1 text-xs text-slate-400 hover:text-white hover:bg-navy-700"
                              >
                                <FileJson className="h-3 w-3" /> JSON
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Complaint Detail Modal */}
      {selectedComplaint && (
        <ComplaintDetailModal
          report={selectedComplaint}
          onClose={() => setSelectedComplaint(null)}
          onGenerate={generate}
        />
      )}

      {/* Generator Modal */}
      {showGenerator && (
        <ReportGeneratorModal
          onClose={() => setShowGenerator(false)}
          onGenerate={generate}
        />
      )}
    </div>
  );
}
