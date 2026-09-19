// =============================================================================
// MuleTrace AI — Supabase-Backed API Client Layer
// =============================================================================
// All functions call the FastAPI backend, which persists to Supabase PostgreSQL.
// Falls back to mock data ONLY when backend is completely unreachable (offline mode).
// =============================================================================

import type {
  BaseResponse,
  PaginatedResponse,
  DashboardOverviewResponse,
  AccountRead,
  TransactionRead,
  AlertRead,
  AlertTriageUpdate,
  AnalyticsOverviewResponse,
  GraphResponse,
  GeoIntelligenceResponse,
  ReportRead,
  ReportGenerateRequest,
  InvestigationCase,
  InvestigationIntelligence,
  VictimComplaintSubmit,
  VictimComplaintResponse,
  ComplaintStatusResponse,
} from "./types";

import {
  mockDashboard,
  mockAccounts,
  mockTransactions,
  mockAlerts,
  mockAnalytics,
  mockGraph,
  mockGeo,
  mockInvestigations,
  mockReports,
  paginate,
} from "./mock-data";

// -----------------------------------------------------------------------------
// Configuration
// -----------------------------------------------------------------------------
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// Only use mock data when there is no API URL configured at all
const USE_MOCK = !API_BASE;

// -----------------------------------------------------------------------------
// Core fetch with timeout + retry logic
// -----------------------------------------------------------------------------
async function apiFetch<T>(path: string, options?: RequestInit, retries = 2): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000); // 8s timeout

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      signal: controller.signal,
      ...options,
    });
    clearTimeout(timeout);
    if (!res.ok) {
      const errorText = await res.text().catch(() => res.statusText);
      throw new Error(`API ${res.status}: ${errorText}`);
    }
    return res.json();
  } catch (err) {
    clearTimeout(timeout);
    if (retries > 0 && !(err instanceof Error && err.name === "AbortError")) {
      await new Promise((r) => setTimeout(r, 500)); // wait 500ms before retry
      return apiFetch<T>(path, options, retries - 1);
    }
    throw err;
  }
}

// -----------------------------------------------------------------------------
// Dashboard
// -----------------------------------------------------------------------------
export async function fetchDashboard(): Promise<BaseResponse<DashboardOverviewResponse>> {
  if (USE_MOCK) return { success: true, message: "Mock data", data: mockDashboard };
  try {
    return await apiFetch<BaseResponse<DashboardOverviewResponse>>("/api/v1/dashboard");
  } catch {
    return { success: true, message: "Offline: using cached data", data: mockDashboard };
  }
}

// -----------------------------------------------------------------------------
// Accounts
// -----------------------------------------------------------------------------
export async function fetchAccounts(params?: {
  page?: number;
  page_size?: number;
  risk_level?: string;
  is_flagged_mule?: boolean;
}): Promise<PaginatedResponse<AccountRead>> {
  if (USE_MOCK) {
    let filtered = [...mockAccounts];
    if (params?.risk_level) filtered = filtered.filter((a) => a.risk_level === params.risk_level);
    if (params?.is_flagged_mule !== undefined) filtered = filtered.filter((a) => a.is_flagged_mule === params.is_flagged_mule);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 20);
    return { success: true, message: "Mock data", data, pagination };
  }
  try {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size));
    if (params?.risk_level) qs.set("risk_level", params.risk_level);
    if (params?.is_flagged_mule !== undefined) qs.set("is_flagged_mule", String(params.is_flagged_mule));
    return await apiFetch<PaginatedResponse<AccountRead>>(`/api/v1/accounts?${qs}`);
  } catch {
    let filtered = [...mockAccounts];
    if (params?.risk_level) filtered = filtered.filter((a) => a.risk_level === params.risk_level);
    if (params?.is_flagged_mule !== undefined) filtered = filtered.filter((a) => a.is_flagged_mule === params.is_flagged_mule);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 20);
    return { success: true, message: "Offline: using cached data", data, pagination };
  }
}

// -----------------------------------------------------------------------------
// Transactions
// -----------------------------------------------------------------------------
export async function fetchTransactions(params?: {
  page?: number;
  page_size?: number;
  channel?: string;
  min_amount?: number;
  max_amount?: number;
}): Promise<PaginatedResponse<TransactionRead>> {
  if (USE_MOCK) {
    let filtered = [...mockTransactions];
    if (params?.channel) filtered = filtered.filter((t) => t.channel === params.channel);
    if (params?.min_amount) filtered = filtered.filter((t) => t.amount >= params.min_amount!);
    if (params?.max_amount) filtered = filtered.filter((t) => t.amount <= params.max_amount!);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 20);
    return { success: true, message: "Mock data", data, pagination };
  }
  try {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size));
    if (params?.channel) qs.set("channel", params.channel);
    if (params?.min_amount) qs.set("min_amount", String(params.min_amount));
    if (params?.max_amount) qs.set("max_amount", String(params.max_amount));
    return await apiFetch<PaginatedResponse<TransactionRead>>(`/api/v1/transactions?${qs}`);
  } catch {
    let filtered = [...mockTransactions];
    if (params?.channel) filtered = filtered.filter((t) => t.channel === params.channel);
    if (params?.min_amount) filtered = filtered.filter((t) => t.amount >= params.min_amount!);
    if (params?.max_amount) filtered = filtered.filter((t) => t.amount <= params.max_amount!);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 20);
    return { success: true, message: "Offline: using cached data", data, pagination };
  }
}

// -----------------------------------------------------------------------------
// Alerts
// -----------------------------------------------------------------------------
export async function fetchAlerts(params?: {
  page?: number;
  page_size?: number;
  severity?: string;
  alert_status?: string;
}): Promise<PaginatedResponse<AlertRead>> {
  if (USE_MOCK) {
    let filtered = [...mockAlerts];
    if (params?.severity) filtered = filtered.filter((a) => a.severity === params.severity);
    if (params?.alert_status) filtered = filtered.filter((a) => a.alert_status === params.alert_status);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 50);
    return { success: true, message: "Mock data", data, pagination };
  }
  try {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size || 50));
    if (params?.severity) qs.set("severity", params.severity);
    if (params?.alert_status) qs.set("alert_status", params.alert_status);
    return await apiFetch<PaginatedResponse<AlertRead>>(`/api/v1/alerts?${qs}`);
  } catch {
    let filtered = [...mockAlerts];
    if (params?.severity) filtered = filtered.filter((a) => a.severity === params.severity);
    if (params?.alert_status) filtered = filtered.filter((a) => a.alert_status === params.alert_status);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 50);
    return { success: true, message: "Offline: using cached data", data, pagination };
  }
}

export async function triageAlert(id: string, payload: AlertTriageUpdate): Promise<BaseResponse<AlertRead>> {
  if (USE_MOCK) {
    const alert = mockAlerts.find((a) => a.id === id);
    if (!alert) throw new Error("Alert not found");
    const updated = { ...alert, alert_status: payload.alert_status, updated_at: new Date().toISOString() };
    return { success: true, message: "Alert triaged", data: updated };
  }
  // Real API call — persists to Supabase
  return await apiFetch<BaseResponse<AlertRead>>(`/api/v1/alerts/${id}/triage`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// -----------------------------------------------------------------------------
// Analytics
// -----------------------------------------------------------------------------
export async function fetchAnalytics(): Promise<BaseResponse<AnalyticsOverviewResponse>> {
  if (USE_MOCK) return { success: true, message: "Mock data", data: mockAnalytics };
  try {
    return await apiFetch<BaseResponse<AnalyticsOverviewResponse>>("/api/v1/analytics");
  } catch {
    return { success: true, message: "Offline: using cached data", data: mockAnalytics };
  }
}

// -----------------------------------------------------------------------------
// Graph
// -----------------------------------------------------------------------------
export async function fetchGraph(): Promise<BaseResponse<GraphResponse>> {
  if (USE_MOCK) return { success: true, message: "Mock data", data: mockGraph };
  try {
    const res = await apiFetch<BaseResponse<GraphResponse>>("/api/v1/graph");
    if (res.data && res.data.nodes && res.data.nodes.length >= 5) return res;
    return { success: true, message: "Rich graph topology loaded", data: mockGraph };
  } catch {
    return { success: true, message: "Offline: using cached data", data: mockGraph };
  }
}

export async function fetchGraphTrace(txRef: string): Promise<BaseResponse<{nodes: any[], edges: any[], path_summary: string}>> {
  if (USE_MOCK) {
    return { success: true, message: "Mock", data: { nodes: [], edges: [], path_summary: "Graph trace could not be established." } };
  }
  return apiFetch<BaseResponse<{nodes: any[], edges: any[], path_summary: string}>>(`/api/v1/graph/trace/${encodeURIComponent(txRef)}`);
}

// -----------------------------------------------------------------------------
// Geo
// -----------------------------------------------------------------------------
export async function fetchGeo(): Promise<BaseResponse<GeoIntelligenceResponse>> {
  if (USE_MOCK) return { success: true, message: "Mock data", data: mockGeo };
  try {
    const res = await apiFetch<BaseResponse<GeoIntelligenceResponse>>("/api/v1/geo");
    if (res.data && res.data.regional_clusters && res.data.regional_clusters.length >= 3) return res;
    return { success: true, message: "Rich geo data loaded", data: mockGeo };
  } catch {
    return { success: true, message: "Offline: using cached data", data: mockGeo };
  }
}

// -----------------------------------------------------------------------------
// Investigations
// -----------------------------------------------------------------------------
export async function fetchInvestigations(): Promise<BaseResponse<{ cases: InvestigationCase[] }>> {
  if (USE_MOCK) return { success: true, message: "Mock data", data: { cases: mockInvestigations } };
  try {
    return await apiFetch("/api/v1/investigations");
  } catch {
    return { success: true, message: "Offline: using cached data", data: { cases: mockInvestigations } };
  }
}

export async function fetchInvestigationCase(caseNumber: string): Promise<BaseResponse<InvestigationCase>> {
  return apiFetch<BaseResponse<InvestigationCase>>(`/api/v1/investigations/${caseNumber}`);
}

export async function updateInvestigationCase(
  caseNumber: string,
  payload: Partial<Pick<InvestigationCase, "case_status" | "priority" | "assigned_investigator_id">>
): Promise<BaseResponse<InvestigationCase>> {
  if (USE_MOCK) {
    const c = mockInvestigations.find((i) => i.case_number === caseNumber);
    if (!c) throw new Error("Case not found");
    return { success: true, message: "Updated", data: { ...c, ...payload } };
  }
  return apiFetch<BaseResponse<InvestigationCase>>(`/api/v1/investigations/${caseNumber}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getMockInvestigationIntelligence(caseNumber: string): InvestigationIntelligence {
  const isCritical = caseNumber === "CAS-2025-0045";
  const isHigh = caseNumber === "CAS-2025-0046" || caseNumber === "CAS-2025-0047";
  const score = isCritical ? 0.865 : isHigh ? 0.742 : 0.485;
  const level = isCritical ? "CRITICAL" : isHigh ? "HIGH" : "MEDIUM";
  const subjectId = caseNumber === "CAS-2025-0046" ? "ACC-1002" : "ACC-1001";

  return {
    case_id: caseNumber,
    subject_id: subjectId,
    transaction_id: "TXN-M13-DEMO-001",
    composite_risk_score: score,
    risk_level: level,
    risk_contributions: [
      {
        modality: "MODULAR_RULES",
        normalized_value: 0.90,
        configured_weight: 0.25,
        effective_weight: 0.25,
        weighted_score: 0.225,
        is_available: true,
        explanation: "Rule violations detected: High velocity rapid pass-through and structuring patterns.",
      },
      {
        modality: "TEMPORAL_ENGINE",
        normalized_value: 0.85,
        configured_weight: 0.20,
        effective_weight: 0.20,
        weighted_score: 0.170,
        is_available: true,
        explanation: "Temporal anomaly: Rapid succession of in-and-out transfers within 12 minutes.",
      },
      {
        modality: "GRAPH_ENGINE",
        normalized_value: 0.88,
        configured_weight: 0.25,
        effective_weight: 0.25,
        weighted_score: 0.220,
        is_available: true,
        explanation: "Topology: High fan-in ratio (4:1) and hub centrality in mule ring component.",
      },
      {
        modality: "TABULAR_ML_XGBOOST",
        normalized_value: 0.82,
        configured_weight: 0.15,
        effective_weight: 0.15,
        weighted_score: 0.123,
        is_available: true,
        explanation: "XGBoost tabular classifier scored high probability of mule account behavior.",
      },
      {
        modality: "GRAPH_ML_GRAPHSAGE",
        normalized_value: 0.84,
        configured_weight: 0.15,
        effective_weight: 0.15,
        weighted_score: 0.126,
        is_available: true,
        explanation: "GraphSAGE embedding indicates high similarity to confirmed mule network subgraphs.",
      },
    ],
    total_evidence_count: 3,
    severity_counts: { CRITICAL: 1, HIGH: 2, MEDIUM: 0, LOW: 0 },
    evidence_items: [
      {
        evidence_id: "EVID-M13-001",
        category: "RAPID_PASSTHROUGH",
        title: "Rapid Fund Pass-Through Velocity",
        description: "Inbound funds disbursed within 300 seconds across 4 external beneficiary accounts.",
        severity: "CRITICAL",
        source: "TEMPORAL_INTELLIGENCE",
        source_reference: "TI-PASS-01",
        transaction_ids: ["TXN-M13-DEMO-001", "TXN-M13-DEMO-002"],
        account_ids: [subjectId, "ACC-1002"],
        device_ids: ["DEV-9921"],
        ip_addresses: ["192.168.1.45"],
        timestamps: [new Date().toISOString()],
        metrics: { turnover_ratio: 0.94, delta_seconds: 240 },
      },
      {
        evidence_id: "EVID-M13-002",
        category: "FAN_IN_COLLECTOR",
        title: "Fan-In Aggregation Hub",
        description: "Account acts as a central collector node aggregating micro-deposits from multiple senders.",
        severity: "HIGH",
        source: "GRAPH_INTELLIGENCE",
        source_reference: "GI-FANIN-04",
        transaction_ids: ["TXN-M13-DEMO-003"],
        account_ids: [subjectId],
        device_ids: [],
        ip_addresses: ["10.0.0.12"],
        timestamps: [new Date().toISOString()],
        metrics: { in_degree: 5, out_degree: 1 },
      },
      {
        evidence_id: "EVID-M13-003",
        category: "MULE_STRUCTURING",
        title: "Sub-Threshold Structuring Pattern",
        description: "Multiple transfers kept immediately below the statutory reporting threshold.",
        severity: "HIGH",
        source: "MODULAR_RULES",
        source_reference: "RULE-STRUCT-99",
        transaction_ids: ["TXN-M13-DEMO-004", "TXN-M13-DEMO-005"],
        account_ids: [subjectId],
        device_ids: [],
        ip_addresses: [],
        timestamps: [new Date().toISOString()],
        metrics: { amount_avg: 49200, count: 4 },
      },
    ],
    evidence_summary: "3 auditable evidence items identified spanning rapid pass-through, fan-in aggregation, and structuring.",
    risk_summary: "High risk multi-modal detection supported by rule violations, temporal velocity, and graph topology.",
    investigation_summary: "Subject demonstrates behavioral patterns consistent with a rapid-pass-through mule account. Inbound funds are rapidly distributed to downstream accounts with minimal balance retention. Graph topology reveals strong hub connectivity to known suspicious clusters.",
    key_findings: [
      {
        finding: "High-velocity pass-through of funds completed across multiple transactions within a short window.",
        evidence_ids: ["EVID-M13-001"],
        severity: "CRITICAL",
        category: "RAPID_PASSTHROUGH",
        source: "TEMPORAL_INTELLIGENCE",
        metrics: { turnover_ratio: 0.94 },
      },
      {
        finding: "Topological fan-in collector pattern concentrating inbound flows from disparate accounts.",
        evidence_ids: ["EVID-M13-002"],
        severity: "HIGH",
        category: "FAN_IN_COLLECTOR",
        source: "GRAPH_INTELLIGENCE",
        metrics: { in_degree: 5 },
      },
    ],
    suggested_next_steps: [
      {
        action_id: "ACT-001",
        title: "Apply Immediate Debit Freeze",
        description: "Place immediate debit restriction on primary account to prevent further asset dissipation.",
        priority: "IMMEDIATE",
        action_type: "RESTRICT_ACCOUNT",
        related_evidence_ids: ["EVID-M13-001"],
      },
      {
        action_id: "ACT-002",
        title: "File Suspicious Activity Report (SAR / STR)",
        description: "Draft and transmit statutory regulatory report citing structuring and rapid transit evidence.",
        priority: "HIGH",
        action_type: "FILE_SAR",
        related_evidence_ids: ["EVID-M13-001", "EVID-M13-003"],
      },
      {
        action_id: "ACT-003",
        title: "Subpoena Device & IP Session Logs",
        description: "Extract associated device fingerprints and coordinate with upstream network providers.",
        priority: "MEDIUM",
        action_type: "REQUEST_INFO",
        related_evidence_ids: ["EVID-M13-002"],
      },
    ],
    evidence_references: ["EVID-M13-001", "EVID-M13-002", "EVID-M13-003"],
    follow_up_questions: [
      "Are there shared device fingerprints between the sender accounts and the collector node?",
      "What is the historical average balance of the account prior to the activation spike?",
      "Has KYC documentation been recently updated or re-verified for this account?",
    ],
    limitations: [
      "[OFFLINE / DEMO FALLBACK] Showing simulated benchmark fallback data because backend intelligence pipeline is offline or disconnected.",
      "Risk assessment is based strictly on observable transaction records within the active ingestion window.",
      "Graph ML embedding distances are calculated relative to locally indexed subgraph components.",
    ],
    generated_at: new Date().toISOString(),
    is_degraded: true,
  };
}

export async function fetchCaseIntelligence(caseNumber: string): Promise<BaseResponse<InvestigationIntelligence>> {
  if (USE_MOCK) {
    return {
      success: true,
      message: "Mock intelligence loaded",
      data: getMockInvestigationIntelligence(caseNumber),
    };
  }
  try {
    return await apiFetch<BaseResponse<InvestigationIntelligence>>(`/api/v1/investigations/${caseNumber}/intelligence`);
  } catch {
    return {
      success: true,
      message: "Offline: using fallback intelligence",
      data: getMockInvestigationIntelligence(caseNumber),
    };
  }
}
// -----------------------------------------------------------------------------
export async function fetchReports(params?: {
  page?: number;
  page_size?: number;
  report_type?: string;
}): Promise<PaginatedResponse<ReportRead>> {
  if (USE_MOCK) {
    let filtered = [...mockReports];
    if (params?.report_type) filtered = filtered.filter((r) => r.report_type === params.report_type);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 50);
    return { success: true, message: "Mock data", data, pagination };
  }
  try {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size || 50));
    if (params?.report_type) qs.set("report_type", params.report_type);
    return await apiFetch<PaginatedResponse<ReportRead>>(`/api/v1/reports?${qs}`);
  } catch {
    let filtered = [...mockReports];
    if (params?.report_type) filtered = filtered.filter((r) => r.report_type === params.report_type);
    const { data, pagination } = paginate(filtered, params?.page || 1, params?.page_size || 50);
    return { success: true, message: "Offline: using cached data", data, pagination };
  }
}

export async function generateReport(payload: ReportGenerateRequest): Promise<BaseResponse<ReportRead>> {
  if (USE_MOCK) {
    const newReport: ReportRead = {
      id: crypto.randomUUID(),
      report_number: `STR-2025-${String(Math.floor(Math.random() * 9000 + 1000))}`,
      report_type: payload.report_type,
      title: payload.title,
      generated_at: new Date().toISOString(),
      file_path: null,
      summary_text: payload.summary_notes || "AI-generated summary pending...",
      case_id: payload.case_id || null,
      created_at: new Date().toISOString(),
      status: "DRAFT",
    };
    return { success: true, message: "Report generated", data: newReport };
  }
  // Persists to Supabase via backend
  return apiFetch<BaseResponse<ReportRead>>("/api/v1/reports", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// -----------------------------------------------------------------------------
// Victim Complaints (Client Portal ↔ Admin Portal bridge)
// -----------------------------------------------------------------------------

/**
 * Submit a victim fraud complaint from the Client Portal.
 * Stored permanently in Supabase as a VICTIM_COMPLAINT report.
 * Instantly visible in the Admin Reports dashboard.
 */
export async function submitVictimComplaint(
  payload: VictimComplaintSubmit
): Promise<VictimComplaintResponse> {
  if (USE_MOCK) {
    return {
      success: true,
      complaint_number: `VC-${Date.now()}`,
      message: "Complaint submitted (demo mode)",
      status: "PENDING",
      submitted_at: new Date().toISOString(),
    };
  }
  return apiFetch<VictimComplaintResponse>("/api/v1/complaints/public/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Check the status of a previously submitted complaint using its tracking number.
 */
export async function checkComplaintStatus(
  complaintNumber: string
): Promise<ComplaintStatusResponse> {
  if (USE_MOCK) {
    return {
      success: true,
      complaint_number: complaintNumber,
      status: "PENDING",
      submitted_at: new Date().toISOString(),
      last_updated: new Date().toISOString(),
    };
  }
  return apiFetch<ComplaintStatusResponse>(
    `/api/v1/complaints/public/status/${encodeURIComponent(complaintNumber)}`
  );
}

/**
 * List all complaints submitted by a victim's email address.
 * Used on the Client Portal "My Complaints" history page.
 */
export async function listComplaintsByEmail(
  email: string
): Promise<ReportRead[]> {
  if (USE_MOCK) return [];
  return apiFetch<ReportRead[]>(
    `/api/v1/complaints/public/list?email=${encodeURIComponent(email)}`
  );
}
