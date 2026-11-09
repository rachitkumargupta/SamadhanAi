import type { 
  ComplaintRead, 
  ComplaintAnalysisStatusRead, 
  ComplaintEventRead,
  ComplaintAnalysisReviewItem 
} from '../types';

export const MOCK_COMPLAINTS: ComplaintRead[] = [
  {
    public_reference: 'CMP/2026/08912',
    description: 'A severe crater pothole has opened up on the main road opposite City Hospital Gate 2. Stagnant rainwater causes two-wheeler skids.',
    location_text: 'Ring Road, Near City Hospital Gate 2, Ward 12 [GPS: 28.6139° N, 77.2090° E]',
    status: 'IN_PROGRESS',
    created_at: new Date(Date.now() - 3600 * 1000 * 4).toISOString(),
  },
  {
    public_reference: 'CMP/2026/07431',
    description: 'Overflowing community garbage bin obstructing pedestrian footpath.',
    location_text: 'Sector 14 Market Corner, Ward 8 [GPS: 28.5821° N, 77.3124° E]',
    status: 'SUBMITTED',
    created_at: new Date(Date.now() - 3600 * 1000 * 24).toISOString(),
  },
  {
    public_reference: 'CMP/2026/06120',
    description: 'Broken street light pole dangling dangerously after high winds.',
    location_text: 'Main Boulevard, Pillar 88, Ward 4',
    status: 'RESOLVED',
    created_at: new Date(Date.now() - 3600 * 1000 * 48).toISOString(),
  }
];

export const MOCK_ANALYSIS_MAP: Record<string, ComplaintAnalysisStatusRead> = {
  'CMP/2026/08912': {
    public_reference: 'CMP/2026/08912',
    status: 'completed',
    run_id: 'run_agent1_08912',
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
      visible_evidence: [
        'Deep crater pothole in asphalt road measuring approx 2.5 feet diameter',
        'Rainwater accumulation obscuring pothole depth',
        'Hospital gate and public road traffic visible in background'
      ],
      facts: [
        'Pothole on two-lane paved road',
        'Wet surface and exposed gravel'
      ],
      inferences: [
        'Risk of two-wheeler accidents and sudden vehicular swerving'
      ],
      uncertainty: [],
      missing_information: [],
      contradictory_information: [],
      priority_factors: [
        {
          criterion: 'safety_hazard_near_hospital',
          evidence: 'Immediate approach road to hospital emergency gate',
          evidence_source: 'image_evidence'
        }
      ],
      priority_score: 85,
      priority_criteria: ['HIGH_TRAFFIC_CORRIDOR', 'EMERGENCY_ACCESS_ROUTE'],
      priority_explanation: ['High pedestrian & vehicular density near medical facility.']
    }
  }
};

export const MOCK_EVENTS: Record<string, ComplaintEventRead[]> = {
  'CMP/2026/08912': [
    {
      event_type: 'Grievance registered with photograph and coordinates.',
      occurred_at: new Date(Date.now() - 3600 * 1000 * 4).toISOString(),
    },
    {
      event_type: 'Automated AI classification: Roads & Potholes (High Priority).',
      occurred_at: new Date(Date.now() - 3600 * 1000 * 3.8).toISOString(),
    },
    {
      event_type: 'Work order dispatched to Executive Engineer, Road Maintenance Unit #3.',
      occurred_at: new Date(Date.now() - 3600 * 1000 * 3.5).toISOString(),
    },
    {
      event_type: 'Repair team acknowledged dispatch and reached site.',
      occurred_at: new Date(Date.now() - 3600 * 1000 * 1.2).toISOString(),
    }
  ]
};

export const MOCK_REVIEWS: ComplaintAnalysisReviewItem[] = [
  {
    public_reference: 'CMP/2026/09104',
    description: 'Collapsed drainage manhole cover in middle of school zone crossing.',
    location_text: 'Central Road, Near Model School, Ward 15',
    submitted_at: new Date(Date.now() - 3600 * 1000 * 2).toISOString(),
    analysis_status: 'needs_review',
    image_url: '',
    result: {
      schema_version: '1.1',
      outcome: 'needs_review',
      category: 'drainage_sewage',
      severity_recommendation: 'critical',
      priority_recommendation: 'critical',
      confidence_level: 'medium',
      possible_multi_department: true,
      human_review_recommended: true,
      human_review_reasons: [
        'Possible multi-department responsibility (Drainage Board vs Public Works)',
        'Critical pedestrian safety hazard in school zone'
      ],
      visible_evidence: [
        'Broken concrete manhole cover with open sewer cavity',
        'Temporary stick barrier placed by citizens'
      ],
      facts: ['Open storm water drain in active roadway'],
      inferences: ['Severe fall hazard for children'],
      uncertainty: ['Uncertain whether sewer pipe or road foundation collapsed first'],
      missing_information: [],
      contradictory_information: [],
      priority_factors: []
    }
  }
];
