import type { 
  ComplaintRead, 
  ComplaintSubmissionRead, 
  ComplaintListPage, 
  ComplaintEventPage, 
  ComplaintAnalysisStatusRead, 
  ComplaintAnalysisReviewPage 
} from '../types';
import { MOCK_COMPLAINTS, MOCK_ANALYSIS_MAP, MOCK_EVENTS, MOCK_REVIEWS } from './mockData';

class ApiClient {
  private token: string = '';
  private useMock: boolean = false;

  setToken(token: string) {
    this.token = token;
  }

  setMockMode(enabled: boolean) {
    this.useMock = enabled;
  }

  isMockMode(): boolean {
    return this.useMock;
  }

  private getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = {
      'X-Correlation-ID': crypto.randomUUID(),
      ...extraHeaders,
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch('/health/live');
      return res.ok;
    } catch {
      return false;
    }
  }

  async submitComplaint(
    image: File,
    description?: string,
    locationText?: string
  ): Promise<ComplaintSubmissionRead> {
    if (this.useMock) {
      const mockRef = `CMP/2026/${Math.floor(10000 + Math.random() * 90000)}`;
      const newComplaint: ComplaintSubmissionRead = {
        public_reference: mockRef,
        description: description || null,
        location_text: locationText || null,
        status: 'SUBMITTED',
        analysis_status: 'pending',
        created_at: new Date().toISOString(),
      };
      MOCK_COMPLAINTS.unshift({
        public_reference: mockRef,
        description: description || null,
        location_text: locationText || null,
        status: 'SUBMITTED',
        created_at: new Date().toISOString(),
      });
      return newComplaint;
    }

    const formData = new FormData();
    formData.append('image', image);
    if (description && description.trim()) {
      formData.append('description', description.trim());
    }
    if (locationText && locationText.trim()) {
      formData.append('location_text', locationText.trim());
    }

    const res = await fetch('/api/v1/complaints', {
      method: 'POST',
      headers: this.getHeaders(),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to submit complaint' }));
      throw new Error(err.detail?.message || err.detail || 'Upload failed');
    }

    return await res.json();
  }

  async getComplaints(limit: number = 20, offset: number = 0): Promise<ComplaintListPage> {
    if (this.useMock) {
      return {
        items: MOCK_COMPLAINTS.slice(offset, offset + limit),
        limit,
        offset,
        next_offset: offset + limit < MOCK_COMPLAINTS.length ? offset + limit : null,
      };
    }

    const res = await fetch(`/api/v1/complaints?limit=${limit}&offset=${offset}`, {
      headers: this.getHeaders(),
    });

    if (!res.ok) {
      throw new Error('Failed to fetch complaints list');
    }
    return await res.json();
  }

  async getComplaint(publicReference: string): Promise<ComplaintRead> {
    if (this.useMock) {
      const found = MOCK_COMPLAINTS.find(c => c.public_reference === publicReference);
      if (found) return found;
      return {
        public_reference: publicReference,
        description: 'Civic issue recorded by citizen',
        location_text: 'Ward 12, Municipal Zone',
        status: 'IN_PROGRESS',
        created_at: new Date().toISOString(),
      };
    }

    const res = await fetch(`/api/v1/complaints/${encodeURIComponent(publicReference)}`, {
      headers: this.getHeaders(),
    });

    if (!res.ok) {
      throw new Error(`Complaint ${publicReference} not found`);
    }
    return await res.json();
  }

  async getAnalysis(publicReference: string): Promise<ComplaintAnalysisStatusRead> {
    if (this.useMock) {
      const existing = MOCK_ANALYSIS_MAP[publicReference];
      if (existing) return existing;
      return {
        public_reference: publicReference,
        status: 'completed',
        run_id: 'mock_run_1',
        human_review_required: false,
        result: {
          schema_version: '1.1',
          outcome: 'completed',
          category: 'roads_potholes',
          severity_recommendation: 'high',
          priority_recommendation: 'high',
          confidence_level: 'high',
          possible_multi_department: false,
          human_review_recommended: false,
          human_review_reasons: [],
          visible_evidence: ['Severe road crater with water logging and gravel erosion'],
          facts: ['Asphalt deterioration in active lane'],
          inferences: ['Accident hazard for two-wheelers'],
          uncertainty: [],
          missing_information: [],
          contradictory_information: [],
          priority_factors: []
        }
      };
    }

    const res = await fetch(`/api/v1/complaints/${encodeURIComponent(publicReference)}/analysis`, {
      headers: this.getHeaders(),
    });

    if (!res.ok) {
      throw new Error('Analysis not ready or not found');
    }
    return await res.json();
  }

  async getEvents(publicReference: string): Promise<ComplaintEventPage> {
    if (this.useMock) {
      const events = MOCK_EVENTS[publicReference] || [
        {
          event_type: 'Grievance submitted by citizen',
          occurred_at: new Date(Date.now() - 3600 * 1000 * 2).toISOString(),
        },
        {
          event_type: 'Agent 1 AI Analysis finished',
          occurred_at: new Date(Date.now() - 3600 * 1000 * 1.9).toISOString(),
        }
      ];
      return { items: events, limit: 50, offset: 0, next_offset: null };
    }

    const res = await fetch(`/api/v1/complaints/${encodeURIComponent(publicReference)}/events`, {
      headers: this.getHeaders(),
    });

    if (!res.ok) {
      throw new Error('Failed to fetch events');
    }
    return await res.json();
  }

  async getReviewQueue(limit: number = 20, offset: number = 0): Promise<ComplaintAnalysisReviewPage> {
    if (this.useMock) {
      return {
        items: MOCK_REVIEWS,
        limit,
        offset,
        next_offset: null,
      };
    }

    const res = await fetch(`/api/v1/staff/complaint-analysis/reviews?limit=${limit}&offset=${offset}`, {
      headers: this.getHeaders(),
    });

    if (!res.ok) {
      throw new Error('Failed to fetch review queue');
    }
    return await res.json();
  }

  async getReviewImageUrl(publicReference: string): Promise<string | null> {
    if (this.useMock) {
      return null;
    }
    try {
      const res = await fetch(`/api/v1/staff/complaint-analysis/reviews/${encodeURIComponent(publicReference)}/image`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) return null;
      const blob = await res.blob();
      return URL.createObjectURL(blob);
    } catch {
      return null;
    }
  }
}

export const api = new ApiClient();
