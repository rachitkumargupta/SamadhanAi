export interface ComplaintRead {
  public_reference: string;
  description: string | null;
  location_text: string | null;
  status: string;
  created_at: string;
}

export interface ComplaintSubmissionRead {
  public_reference: string;
  description: string | null;
  location_text: string | null;
  status: string;
  analysis_status: string;
  created_at: string;
}

export interface ComplaintListPage {
  items: ComplaintRead[];
  limit: number;
  offset: number;
  next_offset: number | null;
}

export interface ComplaintEventRead {
  event_type: string;
  occurred_at: string;
}

export interface ComplaintEventPage {
  items: ComplaintEventRead[];
  limit: number;
  offset: number;
  next_offset: number | null;
}

export interface PriorityFactor {
  criterion: string;
  evidence: string;
  evidence_source: 'image_evidence' | 'citizen_description';
}

export interface ComplaintAnalysis {
  schema_version: string;
  outcome: 'completed' | 'needs_review' | 'insufficient_context';
  generated_description?: string | null;
  visible_evidence: string[];
  facts: string[];
  inferences: string[];
  category: string | null;
  severity_recommendation: 'low' | 'medium' | 'high' | 'critical' | null;
  priority_recommendation: 'low' | 'medium' | 'high' | 'critical' | null;
  uncertainty: string[];
  missing_information: string[];
  contradictory_information: string[];
  possible_multi_department: boolean;
  confidence_level: 'low' | 'medium' | 'high';
  priority_factors: PriorityFactor[];
  human_review_recommended: boolean;
  human_review_reasons: string[];
  missing_information_codes?: string[];
  priority_score?: number | null;
  priority_criteria?: string[];
  priority_explanation?: string[];
  policy_id?: string;
  policy_version?: string;
}

export interface ComplaintAnalysisStatusRead {
  public_reference: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  run_id?: string | null;
  result?: ComplaintAnalysis | null;
  human_review_required: boolean;
  message?: string | null;
}

export interface ComplaintAnalysisReviewItem {
  public_reference: string;
  description: string | null;
  location_text: string | null;
  submitted_at: string;
  analysis_status: string;
  image_url: string;
  result?: ComplaintAnalysis | null;
}

export interface ComplaintAnalysisReviewPage {
  items: ComplaintAnalysisReviewItem[];
  limit: number;
  offset: number;
  next_offset: number | null;
}
