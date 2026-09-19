// =============================================================================
// MuleTrace AI — TypeScript Type Definitions
// =============================================================================
// Mirrors backend Pydantic schemas for full type safety.
// =============================================================================

// -----------------------------------------------------------------------------
// API Response Envelopes
// -----------------------------------------------------------------------------
export interface BaseResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
}

export interface PaginationMeta {
  total_items: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  pagination: PaginationMeta;
}

// -----------------------------------------------------------------------------
// Dashboard
// -----------------------------------------------------------------------------
export interface KPIOverview {
  total_transactions_24h: number;
  flagged_mule_accounts: number;
  active_alerts_count: number;
  total_volume_at_risk_inr: number;
}

export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface PatternHitSummary {
  pattern_name: string;
  hit_count: number;
  severity: string;
}

export interface DashboardOverviewResponse {
  kpis: KPIOverview;
  risk_distribution: RiskDistribution;
  top_patterns: PatternHitSummary[];
  recent_alerts: AlertRead[];
}

// -----------------------------------------------------------------------------
// Accounts
// -----------------------------------------------------------------------------
export interface AccountRead {
  id: string;
  account_number: string;
  customer_id: string;
  customer_name: string;
  account_type: string;
  currency: string;
  balance: number;
  risk_score: number;
  risk_level: string;
  is_flagged_mule: boolean;
  branch_id: string | null;
  opened_at: string | null;
  created_at: string;
  updated_at: string;
  status: string;
}

// -----------------------------------------------------------------------------
// Transactions
// -----------------------------------------------------------------------------
export interface TransactionRead {
  id: string;
  transaction_ref: string;
  channel: string;
  amount: number;
  currency: string;
  timestamp: string;
  location_city: string | null;
  location_state: string | null;
  ip_address_str: string | null;
  device_fingerprint: string | null;
  sender_account_id: string;
  receiver_account_id: string;
  risk_score: number;
  flagged_pattern: string | null;
  narrative: string | null;
  created_at: string;
  status: string;
}

export interface TransactionFilterParams {
  channel?: string;
  min_amount?: number;
  max_amount?: number;
  start_date?: string;
  end_date?: string;
  flagged_only?: boolean;
  sender_account_id?: string;
  receiver_account_id?: string;
}

// -----------------------------------------------------------------------------
// Alerts
// -----------------------------------------------------------------------------
export interface AlertRead {
  id: string;
  alert_number: string;
  title: string;
  pattern_type: string;
  severity: string;
  risk_score: number;
  description: string | null;
  account_id: string;
  case_id: string | null;
  alert_status: string;
  triggered_at: string;
  created_at: string;
  updated_at: string;
}

export interface AlertTriageUpdate {
  alert_status: string;
  notes?: string;
  case_id?: string;
}

// -----------------------------------------------------------------------------
// Analytics
// -----------------------------------------------------------------------------
export interface ChannelVolume {
  channel: string;
  transaction_count: number;
  total_amount_inr: number;
  mule_percentage: number;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  total_volume: number;
  flagged_volume: number;
  alert_count: number;
}

export interface GeoCluster {
  city: string;
  state: string;
  latitude: number;
  longitude: number;
  active_mules_count: number;
  total_alert_count: number;
}

export interface AnalyticsOverviewResponse {
  time_series: TimeSeriesDataPoint[];
  channel_breakdown: ChannelVolume[];
  geo_clusters: GeoCluster[];
}

// -----------------------------------------------------------------------------
// Graph Intelligence
// -----------------------------------------------------------------------------
export type NodeType =
  | 'account'
  | 'victim'
  | 'device'
  | 'phone'
  | 'ip'
  | 'atm'
  | 'crypto'
  | 'merchant';

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  risk_score: number;
  account_number?: string;
  customer_name?: string;
  bank?: string;
  phone?: string;
  device?: string;
  ip?: string;
  location?: string;
  last_transaction?: string;
  total_received?: number;
  total_sent?: number;
  is_mule?: boolean;
  community_id?: string;
  fx?: number;
  fy?: number;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id?: string;
  source: string;
  target: string;
  relationship: 'TRANSFERRED_FUNDS' | 'SHARED_DEVICE' | 'SHARED_IP' | 'SHARED_PHONE' | string;
  amount?: number;
  channel?: string;
  timestamp?: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  community_id: string;
}

// -----------------------------------------------------------------------------
// Geo Intelligence
// -----------------------------------------------------------------------------
export interface ImpossibleTravelAlert {
  account_number: string;
  origin: string;
  destination: string;
  distance_km: number;
  time_gap_minutes: number;
  flagged: boolean;
}

export interface RegionalCluster {
  city: string;
  mule_count: number;
  lat: number;
  lng: number;
}

export interface GeoIntelligenceResponse {
  impossible_travel_alerts: ImpossibleTravelAlert[];
  regional_clusters: RegionalCluster[];
}

// -----------------------------------------------------------------------------
// Investigations
// -----------------------------------------------------------------------------
export interface InvestigationCase {
  id?: string;
  case_number: string;
  title: string;
  priority: string;
  case_status: string;
  assigned_investigator_id: string;
  alerts_count: number;
  created_at?: string;
  updated_at?: string;
  description?: string;
  evidence_summary?: string;
}

export interface CaseTimeline {
  id: string;
  case_id: string;
  event: string;
  date: string;
  created_by?: string;
}

export interface CaseEvidence {
  accounts: string[];
  total_volume: string;
  alerts: number;
  timeline: { date: string; event: string }[];
}

export interface ModalityContribution {
  modality: string;
  normalized_value: number;
  configured_weight: number;
  effective_weight: number;
  weighted_score: number;
  is_available: boolean;
  explanation: string;
}

export interface IntelligenceEvidenceItem {
  evidence_id: string;
  category: string;
  title: string;
  description: string;
  severity: string;
  source: string;
  source_reference?: string | null;
  transaction_ids: string[];
  account_ids: string[];
  device_ids: string[];
  ip_addresses: string[];
  timestamps: string[];
  metrics: Record<string, unknown>;
}

export interface IntelligenceKeyFinding {
  finding: string;
  evidence_ids: string[];
  severity: string;
  category: string;
  source: string;
  metrics: Record<string, unknown>;
}

export interface IntelligenceSuggestedAction {
  action_id: string;
  title: string;
  description: string;
  priority: string;
  action_type: string;
  related_evidence_ids: string[];
}

export interface InvestigationIntelligence {
  case_id: string;
  subject_id: string;
  transaction_id?: string | null;
  composite_risk_score: number;
  risk_level: string;
  risk_contributions: ModalityContribution[];
  total_evidence_count: number;
  severity_counts: Record<string, number>;
  evidence_items: IntelligenceEvidenceItem[];
  evidence_summary: string;
  risk_summary: string;
  investigation_summary: string;
  key_findings: IntelligenceKeyFinding[];
  suggested_next_steps: IntelligenceSuggestedAction[];
  evidence_references: string[];
  follow_up_questions: string[];
  limitations: string[];
  generated_at: string;
  is_degraded: boolean;
}

// -----------------------------------------------------------------------------

// Reports & Victim Complaints
// -----------------------------------------------------------------------------
export interface ReportRead {
  id: string;
  report_number: string;
  report_type: string;
  title: string;
  generated_at: string;
  file_path: string | null;
  summary_text: string | null;
  case_id: string | null;
  created_at: string;
  status: string;
}

export interface ReportGenerateRequest {
  report_type: string;
  title: string;
  case_id?: string;
  include_graph_visualization?: boolean;
  summary_notes?: string;
}

// Victim Complaint (Client Portal → Admin Portal)
export interface VictimComplaintSubmit {
  victim_name: string;
  victim_email: string;
  victim_phone?: string | null;
  transaction_id?: string | null;
  incident_type: string;
  amount_lost?: number | null;
  incident_date?: string | null;
  description: string;
}

export interface VictimComplaintResponse {
  success: boolean;
  complaint_number: string;
  message: string;
  status: string;
  submitted_at: string;
}

export interface ComplaintStatusResponse {
  success: boolean;
  complaint_number: string;
  status: string;
  submitted_at: string;
  last_updated: string;
  message?: string;
}

// -----------------------------------------------------------------------------
// Enums / Constants
// -----------------------------------------------------------------------------
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Channel = 'UPI' | 'NEFT' | 'IMPS' | 'RTGS';
export type AlertStatus = 'NEW' | 'UNDER_INVESTIGATION' | 'ESCALATED' | 'CLOSED_FALSE_POSITIVE' | 'CLOSED_CONFIRMED';
export type ReportType = 'STR' | 'CTR' | 'CYBERCRIME_SUMMARY' | 'EXECUTIVE_BRIEF' | 'VICTIM_COMPLAINT';
export type CasePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type CaseStatus = 'OPEN' | 'IN_PROGRESS' | 'CLOSED' | 'ARCHIVED';
export type IncidentType =
  | 'UPI_FRAUD'
  | 'PHISHING'
  | 'ACCOUNT_TAKEOVER'
  | 'INVESTMENT_SCAM'
  | 'LOAN_FRAUD'
  | 'KYC_FRAUD'
  | 'ROMANCE_SCAM'
  | 'CYBER_CRIME'
  | 'OTHER';
