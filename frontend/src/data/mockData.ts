import {
  Complaint,
  ComplaintCategory,
  ComplaintStatus,
  Department,
  DashboardStats,
  Officer,
  Notification,
  SeverityLevel,
} from '../types';

// ─── Helpers ─────────────────────────────────────────────────────────────────
const randomId = () => Math.random().toString(36).slice(2, 9).toUpperCase();
const daysAgo = (d: number) =>
  new Date(Date.now() - d * 86_400_000).toISOString();

// ─── Mock Complaints ──────────────────────────────────────────────────────────
export const mockComplaints: Complaint[] = [
  {
    id: '1',
    complaintId: '#C1023',
    title: 'Pothole causing accidents near St. Xavier School',
    description:
      'There is a large pothole near St. Xavier School on MG Road that has been causing accidents for the past two weeks. Multiple vehicles have been damaged. Immediate attention is required.',
    category: 'roads',
    status: 'in_progress',
    severity: 'high',
    location: { address: 'MG Road, near St. Xavier School', ward: 'Ward 12', city: 'Bhopal', pincode: '462001' },
    submittedBy: 'citizen-1',
    citizenName: 'Ramesh Sharma',
    citizenPhone: '+91 98765 43210',
    assignedDepartment: 'Roads & Infrastructure',
    assignedOfficer: 'officer-1',
    assignedOfficerName: 'Vikram Singh',
    slaDeadline: daysAgo(-2),
    slaBreached: false,
    aiAnalysis: {
      category: 'roads',
      severity: 'high',
      summary: 'Large road pothole near a school causing vehicle damage. High priority due to safety risk near school zone.',
      suggestedDepartment: 'Roads & Infrastructure',
      suggestedSLA: 48,
      confidence: 0.94,
    },
    timeline: [
      { id: 't1', type: 'submitted', message: 'Complaint submitted by citizen', actor: 'Ramesh Sharma', actorRole: 'citizen', createdAt: daysAgo(5) },
      { id: 't2', type: 'analyzed', message: 'AI Agent analyzed complaint — High severity road issue near school zone', actor: 'Complaint Analyst AI', actorRole: 'ai', createdAt: daysAgo(5) },
      { id: 't3', type: 'assigned', message: 'Assigned to Roads & Infrastructure Dept. — Officer Vikram Singh', actor: 'Resolution & Routing AI', actorRole: 'ai', createdAt: daysAgo(4) },
      { id: 't4', type: 'updated', message: 'Officer on-site inspection scheduled for tomorrow', actor: 'Vikram Singh', actorRole: 'officer', createdAt: daysAgo(2) },
    ],
    createdAt: daysAgo(5),
    updatedAt: daysAgo(2),
  },
  {
    id: '2',
    complaintId: '#C1024',
    title: 'Garbage not collected for 5 days near the school',
    description:
      'Garbage has not been collected for 5 days near the school on Arera Colony. Foul smell and risk of disease outbreak.',
    category: 'garbage',
    status: 'assigned',
    severity: 'medium',
    location: { address: 'Arera Colony, E-7 Sector', ward: 'Ward 8', city: 'Bhopal', pincode: '462016' },
    submittedBy: 'citizen-2',
    citizenName: 'Sunita Patel',
    citizenPhone: '+91 87654 32109',
    assignedDepartment: 'Sanitation',
    assignedOfficer: 'officer-2',
    assignedOfficerName: 'Priya Mehta',
    slaDeadline: daysAgo(-1),
    slaBreached: false,
    aiAnalysis: {
      category: 'garbage',
      severity: 'medium',
      summary: 'Garbage collection failure in residential area. Health risk if not addressed within 24 hours.',
      suggestedDepartment: 'Sanitation',
      suggestedSLA: 24,
      confidence: 0.91,
    },
    timeline: [
      { id: 't1', type: 'submitted', message: 'Complaint submitted by citizen', actor: 'Sunita Patel', actorRole: 'citizen', createdAt: daysAgo(3) },
      { id: 't2', type: 'analyzed', message: 'AI analysis complete — Sanitation issue, medium priority', actor: 'Complaint Analyst AI', actorRole: 'ai', createdAt: daysAgo(3) },
      { id: 't3', type: 'assigned', message: 'Assigned to Sanitation Department — Officer Priya Mehta', actor: 'Resolution & Routing AI', actorRole: 'ai', createdAt: daysAgo(2) },
    ],
    createdAt: daysAgo(3),
    updatedAt: daysAgo(2),
  },
  {
    id: '3',
    complaintId: '#C1025',
    title: 'Street light not working for 3 weeks on Shyamla Hills',
    description:
      'The street lights on Shyamla Hills Road have not been working for almost 3 weeks. It is very dark and unsafe at night.',
    category: 'street_lights',
    status: 'escalated',
    severity: 'high',
    location: { address: 'Shyamla Hills Road', ward: 'Ward 15', city: 'Bhopal', pincode: '462013' },
    submittedBy: 'citizen-3',
    citizenName: 'Arun Kumar',
    citizenPhone: '+91 76543 21098',
    assignedDepartment: 'Electricity',
    assignedOfficer: 'officer-3',
    assignedOfficerName: 'Deepak Yadav',
    slaDeadline: daysAgo(2),
    slaBreached: true,
    timeline: [
      { id: 't1', type: 'submitted', message: 'Complaint submitted', actor: 'Arun Kumar', actorRole: 'citizen', createdAt: daysAgo(10) },
      { id: 't2', type: 'analyzed', message: 'AI analysis — street light outage, high priority due to safety', actor: 'Complaint Analyst AI', actorRole: 'ai', createdAt: daysAgo(10) },
      { id: 't3', type: 'assigned', message: 'Assigned to Electricity Dept.', actor: 'Resolution & Routing AI', actorRole: 'ai', createdAt: daysAgo(9) },
      { id: 't4', type: 'escalated', message: 'SLA breached — escalated to Senior Officer by Monitoring Agent', actor: 'Monitoring & Escalation AI', actorRole: 'ai', createdAt: daysAgo(1) },
    ],
    createdAt: daysAgo(10),
    updatedAt: daysAgo(1),
  },
  {
    id: '4',
    complaintId: '#C1020',
    title: 'Pipeline leakage causing road damage',
    description:
      'Water is leaking from the main pipeline near Habibganj Circle causing waterlogging and road damage.',
    category: 'water_supply',
    status: 'resolved',
    severity: 'critical',
    location: { address: 'Habibganj Circle', ward: 'Ward 5', city: 'Bhopal', pincode: '462023' },
    submittedBy: 'citizen-4',
    citizenName: 'Meena Gupta',
    citizenPhone: '+91 65432 10987',
    assignedDepartment: 'Water Supply',
    assignedOfficer: 'officer-4',
    assignedOfficerName: 'Suresh Verma',
    slaDeadline: daysAgo(7),
    slaBreached: false,
    timeline: [
      { id: 't1', type: 'submitted', message: 'Complaint submitted', actor: 'Meena Gupta', actorRole: 'citizen', createdAt: daysAgo(15) },
      { id: 't2', type: 'analyzed', message: 'Critical — pipeline burst, immediate repair needed', actor: 'Complaint Analyst AI', actorRole: 'ai', createdAt: daysAgo(15) },
      { id: 't3', type: 'assigned', message: 'Assigned to Water Supply Dept.', actor: 'Resolution & Routing AI', actorRole: 'ai', createdAt: daysAgo(14) },
      { id: 't4', type: 'updated', message: 'Repair team dispatched', actor: 'Suresh Verma', actorRole: 'officer', createdAt: daysAgo(13) },
      { id: 't5', type: 'resolved', message: 'Pipeline repaired. Road restored.', actor: 'Suresh Verma', actorRole: 'officer', createdAt: daysAgo(10) },
    ],
    createdAt: daysAgo(15),
    updatedAt: daysAgo(10),
  },
  {
    id: '5',
    complaintId: '#C1026',
    title: 'Blocked drainage causing waterlogging',
    description:
      'Drainage is blocked near DB City Mall area. Every time it rains, the whole road gets flooded.',
    category: 'drainage',
    status: 'pending',
    severity: 'medium',
    location: { address: 'Near DB City Mall, Maharana Pratap Nagar', ward: 'Ward 20', city: 'Bhopal', pincode: '462011' },
    submittedBy: 'citizen-1',
    citizenName: 'Ramesh Sharma',
    citizenPhone: '+91 98765 43210',
    slaDeadline: daysAgo(-3),
    timeline: [
      { id: 't1', type: 'submitted', message: 'Complaint submitted', actor: 'Ramesh Sharma', actorRole: 'citizen', createdAt: daysAgo(1) },
      { id: 't2', type: 'analyzed', message: 'AI analysis — drainage blockage, medium priority', actor: 'Complaint Analyst AI', actorRole: 'ai', createdAt: daysAgo(1) },
    ],
    createdAt: daysAgo(1),
    updatedAt: daysAgo(1),
  },
  {
    id: '6',
    complaintId: '#C1019',
    title: 'Fallen tree blocking main road',
    description:
      'A large tree has fallen across Hoshangabad Road blocking traffic completely.',
    category: 'tree_fallen',
    status: 'closed',
    severity: 'critical',
    location: { address: 'Hoshangabad Road', ward: 'Ward 3', city: 'Bhopal', pincode: '462026' },
    submittedBy: 'citizen-5',
    citizenName: 'Kavita Joshi',
    citizenPhone: '+91 54321 09876',
    assignedDepartment: 'Parks & Horticulture',
    assignedOfficer: 'officer-5',
    assignedOfficerName: 'Anita Sharma',
    slaDeadline: daysAgo(12),
    slaBreached: false,
    timeline: [
      { id: 't1', type: 'submitted', message: 'Emergency complaint submitted', actor: 'Kavita Joshi', actorRole: 'citizen', createdAt: daysAgo(20) },
      { id: 't2', type: 'analyzed', message: 'Critical — road blocked, immediate action', actor: 'Complaint Analyst AI', actorRole: 'ai', createdAt: daysAgo(20) },
      { id: 't3', type: 'assigned', message: 'Emergency team dispatched', actor: 'Resolution & Routing AI', actorRole: 'ai', createdAt: daysAgo(20) },
      { id: 't4', type: 'resolved', message: 'Tree removed, road clear', actor: 'Anita Sharma', actorRole: 'officer', createdAt: daysAgo(19) },
      { id: 't5', type: 'closed', message: 'Complaint closed. Citizen notified.', actor: 'System', actorRole: 'system', createdAt: daysAgo(19) },
    ],
    createdAt: daysAgo(20),
    updatedAt: daysAgo(19),
  },
];

// ─── Mock Departments ─────────────────────────────────────────────────────────
export const mockDepartments: Department[] = [
  { id: 'd1', name: 'Roads & Infrastructure', code: 'ROADS', head: 'Ashok Kumar', totalComplaints: 145, resolved: 98, pending: 32, escalated: 15, avgResolutionDays: 4.2 },
  { id: 'd2', name: 'Water Supply', code: 'WATER', head: 'Ravi Shankar', totalComplaints: 89, resolved: 71, pending: 13, escalated: 5, avgResolutionDays: 3.1 },
  { id: 'd3', name: 'Sanitation', code: 'SANIT', head: 'Rekha Verma', totalComplaints: 203, resolved: 178, pending: 20, escalated: 5, avgResolutionDays: 1.8 },
  { id: 'd4', name: 'Electricity', code: 'ELEC', head: 'Sunil Mishra', totalComplaints: 112, resolved: 78, pending: 22, escalated: 12, avgResolutionDays: 5.7 },
  { id: 'd5', name: 'Drainage', code: 'DRAIN', head: 'Neha Gupta', totalComplaints: 67, resolved: 45, pending: 18, escalated: 4, avgResolutionDays: 6.3 },
  { id: 'd6', name: 'Parks & Horticulture', code: 'PARKS', head: 'Manoj Tiwari', totalComplaints: 34, resolved: 28, pending: 5, escalated: 1, avgResolutionDays: 2.9 },
];

// ─── Mock Officers ────────────────────────────────────────────────────────────
export const mockOfficers: Officer[] = [
  { id: 'officer-1', name: 'Vikram Singh', email: 'vikram.singh@bhopal.gov.in', phone: '+91 98001 23456', department: 'Roads & Infrastructure', departmentId: 'd1', assignedComplaints: 18, resolvedComplaints: 14, pendingComplaints: 4, slaBreaches: 2, status: 'active' },
  { id: 'officer-2', name: 'Priya Mehta', email: 'priya.mehta@bhopal.gov.in', phone: '+91 98001 34567', department: 'Sanitation', departmentId: 'd3', assignedComplaints: 25, resolvedComplaints: 22, pendingComplaints: 3, slaBreaches: 0, status: 'active' },
  { id: 'officer-3', name: 'Deepak Yadav', email: 'deepak.yadav@bhopal.gov.in', phone: '+91 98001 45678', department: 'Electricity', departmentId: 'd4', assignedComplaints: 12, resolvedComplaints: 8, pendingComplaints: 4, slaBreaches: 3, status: 'active' },
  { id: 'officer-4', name: 'Suresh Verma', email: 'suresh.verma@bhopal.gov.in', phone: '+91 98001 56789', department: 'Water Supply', departmentId: 'd2', assignedComplaints: 9, resolvedComplaints: 9, pendingComplaints: 0, slaBreaches: 0, status: 'active' },
  { id: 'officer-5', name: 'Anita Sharma', email: 'anita.sharma@bhopal.gov.in', phone: '+91 98001 67890', department: 'Parks & Horticulture', departmentId: 'd6', assignedComplaints: 5, resolvedComplaints: 5, pendingComplaints: 0, slaBreaches: 0, status: 'active' },
];

// ─── Dashboard Stats ──────────────────────────────────────────────────────────
export const adminDashboardStats: DashboardStats = {
  totalComplaints: 650,
  pendingComplaints: 110,
  resolvedComplaints: 498,
  escalatedComplaints: 42,
  avgResolutionDays: 3.8,
  slaBreachRate: 8.5,
  citizenSatisfaction: 82,
};

// ─── Mock Notifications ───────────────────────────────────────────────────────
export const mockNotifications: Notification[] = [
  { id: 'n1', type: 'success', title: 'Complaint Resolved', message: 'Your complaint #C1020 (Pipeline leakage) has been resolved.', read: false, createdAt: daysAgo(5), complaintId: '#C1020' },
  { id: 'n2', type: 'info', title: 'Status Update', message: 'Your complaint #C1023 is now In Progress. Officer Vikram Singh has been assigned.', read: false, createdAt: daysAgo(2), complaintId: '#C1023' },
  { id: 'n3', type: 'warning', title: 'SLA Breach Alert', message: 'Complaint #C1025 has breached SLA. Escalated to senior authority.', read: true, createdAt: daysAgo(1), complaintId: '#C1025' },
  { id: 'n4', type: 'info', title: 'New Complaint Assigned', message: 'Complaint #C1024 has been assigned to you.', read: false, createdAt: daysAgo(2), complaintId: '#C1024' },
];

// ─── Chart data ───────────────────────────────────────────────────────────────
export const complaintsByCategory = [
  { label: 'Roads', value: 145, color: '#3b82f6' },
  { label: 'Sanitation', value: 203, color: '#22c55e' },
  { label: 'Water', value: 89, color: '#06b6d4' },
  { label: 'Electricity', value: 112, color: '#f59e0b' },
  { label: 'Drainage', value: 67, color: '#8b5cf6' },
  { label: 'Parks', value: 34, color: '#ec4899' },
];

export const complaintsByStatus = [
  { label: 'Pending', value: 110, color: '#f59e0b' },
  { label: 'In Progress', value: 165, color: '#3b82f6' },
  { label: 'Escalated', value: 42, color: '#ef4444' },
  { label: 'Resolved', value: 333, color: '#22c55e' },
];

export const weeklyTrend = [
  { label: 'Mon', submitted: 28, resolved: 22 },
  { label: 'Tue', submitted: 35, resolved: 30 },
  { label: 'Wed', submitted: 22, resolved: 25 },
  { label: 'Thu', submitted: 41, resolved: 35 },
  { label: 'Fri', submitted: 38, resolved: 40 },
  { label: 'Sat', submitted: 19, resolved: 15 },
  { label: 'Sun', submitted: 12, resolved: 10 },
];

// ─── Status + severity helpers ────────────────────────────────────────────────
export const statusConfig: Record<ComplaintStatus, { label: string; color: string; bg: string }> = {
  pending:      { label: 'Pending',      color: 'text-amber-700',  bg: 'bg-amber-50 border border-amber-200' },
  under_review: { label: 'Under Review', color: 'text-blue-700',   bg: 'bg-blue-50 border border-blue-200' },
  assigned:     { label: 'Assigned',     color: 'text-indigo-700', bg: 'bg-indigo-50 border border-indigo-200' },
  in_progress:  { label: 'In Progress',  color: 'text-violet-700', bg: 'bg-violet-50 border border-violet-200' },
  escalated:    { label: 'Escalated',    color: 'text-red-700',    bg: 'bg-red-50 border border-red-200' },
  resolved:     { label: 'Resolved',     color: 'text-green-700',  bg: 'bg-green-50 border border-green-200' },
  closed:       { label: 'Closed',       color: 'text-slate-600',  bg: 'bg-slate-100 border border-slate-200' },
};

export const severityConfig: Record<SeverityLevel, { label: string; color: string; bg: string }> = {
  low:      { label: 'Low',      color: 'text-green-700',  bg: 'bg-green-50 border border-green-200' },
  medium:   { label: 'Medium',   color: 'text-amber-700',  bg: 'bg-amber-50 border border-amber-200' },
  high:     { label: 'High',     color: 'text-orange-700', bg: 'bg-orange-50 border border-orange-200' },
  critical: { label: 'Critical', color: 'text-red-700',    bg: 'bg-red-50 border border-red-200' },
};

export const categoryLabels: Record<ComplaintCategory, string> = {
  roads: 'Roads',
  water_supply: 'Water Supply',
  sanitation: 'Sanitation',
  electricity: 'Electricity',
  drainage: 'Drainage',
  street_lights: 'Street Lights',
  garbage: 'Garbage',
  tree_fallen: 'Tree Fallen',
  other: 'Other',
};
