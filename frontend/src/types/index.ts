// ─── User & Auth ────────────────────────────────────────────────────────────
export type Role = 'citizen' | 'officer' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  phone?: string;
  department?: string;
  avatarUrl?: string;
}

// ─── Complaint ───────────────────────────────────────────────────────────────
export type ComplaintStatus =
  | 'pending'
  | 'under_review'
  | 'assigned'
  | 'in_progress'
  | 'escalated'
  | 'resolved'
  | 'closed';

export type ComplaintCategory =
  | 'roads'
  | 'water_supply'
  | 'sanitation'
  | 'electricity'
  | 'drainage'
  | 'street_lights'
  | 'garbage'
  | 'tree_fallen'
  | 'other';

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

export interface Complaint {
  id: string;
  complaintId: string; // e.g. #C1023
  title: string;
  description: string;
  category: ComplaintCategory;
  status: ComplaintStatus;
  severity: SeverityLevel;
  location: {
    address: string;
    ward?: string;
    city: string;
    pincode?: string;
    lat?: number;
    lng?: number;
  };
  submittedBy: string; // citizen user id
  citizenName: string;
  citizenPhone: string;
  assignedDepartment?: string;
  assignedOfficer?: string;
  assignedOfficerName?: string;
  slaDeadline?: string; // ISO date
  slaBreached?: boolean;
  attachments?: string[]; // URLs
  aiAnalysis?: AIAnalysis;
  timeline: TimelineEvent[];
  createdAt: string;
  updatedAt: string;
}

export interface AIAnalysis {
  category: ComplaintCategory;
  severity: SeverityLevel;
  summary: string;
  missingInfo?: string[];
  duplicateOf?: string;
  suggestedDepartment: string;
  suggestedOfficer?: string;
  suggestedSLA: number; // hours
  confidence: number; // 0-1
}

export interface TimelineEvent {
  id: string;
  type:
    | 'submitted'
    | 'analyzed'
    | 'assigned'
    | 'updated'
    | 'escalated'
    | 'resolved'
    | 'closed'
    | 'commented';
  message: string;
  actor: string;
  actorRole: Role | 'system' | 'ai';
  createdAt: string;
}

// ─── Department & Officer ────────────────────────────────────────────────────
export interface Department {
  id: string;
  name: string;
  code: string;
  head: string;
  totalComplaints: number;
  resolved: number;
  pending: number;
  escalated: number;
  avgResolutionDays: number;
}

export interface Officer {
  id: string;
  name: string;
  email: string;
  phone: string;
  department: string;
  departmentId: string;
  assignedComplaints: number;
  resolvedComplaints: number;
  pendingComplaints: number;
  slaBreaches: number;
  status: 'active' | 'inactive';
}

// ─── Analytics ───────────────────────────────────────────────────────────────
export interface DashboardStats {
  totalComplaints: number;
  pendingComplaints: number;
  resolvedComplaints: number;
  escalatedComplaints: number;
  avgResolutionDays: number;
  slaBreachRate: number;
  citizenSatisfaction: number;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

// ─── Notification ────────────────────────────────────────────────────────────
export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  complaintId?: string;
}
