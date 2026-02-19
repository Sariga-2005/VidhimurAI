const API_BASE = 'http://localhost:8000';

export interface SearchFilters {
    court?: string;
    year_start?: number;
    year_end?: number;
}

export interface CaseResult {
    kanoon_tid: number | null;
    case_name: string;
    court: string;
    year: number;
    citation_count: number;
    strength_score: number;
    authority_score: number;
    relevance_score: number;
    summary: string;
}

export interface SearchResponse {
    total_cases: number;
    top_cases: CaseResult[];
    most_influential_case: CaseResult | null;
}

export interface EmpowerResponse {
    issue_type: string;
    relevant_sections: string[];
    precedents: CaseResult[];
    legal_strength: 'Strong' | 'Moderate' | 'Weak';
    action_steps: string[];
}

export async function searchCases(query: string, filters?: SearchFilters, lang?: string): Promise<SearchResponse> {
    const body: { query: string; filters?: SearchFilters; lang?: string } = { query };
    if (filters) body.filters = filters;
    if (lang) body.lang = lang;

    const res = await fetch(`${API_BASE}/research/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Network error' }));
        throw new Error(err.detail || `Search failed (${res.status})`);
    }
    return res.json();
}

export async function analyzeEmpowerment(query: string, context?: string, lang?: string): Promise<EmpowerResponse> {
    const body: { query: string; context?: string; lang?: string } = { query };
    if (context) body.context = context;
    if (lang) body.lang = lang;

    const res = await fetch(`${API_BASE}/empower/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Network error' }));
        throw new Error(err.detail || `Analysis failed (${res.status})`);
    }
    return res.json();
}

export interface RoadmapData {
    immediate_actions: string[];
    evidence_checklist: string[];
    legal_notice_strategy: string[];
    pre_litigation_options: string[];
    litigation_strategy: string[];
    estimated_timeline: string;
    cost_considerations: string[];
    risk_assessment: string[] | string;
    escalation_path: string[];
}

export interface RoadmapResponse {
    roadmap: RoadmapData;
}

export async function generateRoadmap(analysis: {
    issue_type: string;
    relevant_sections: string[];
    legal_strength: string;
    action_steps: string[];
}): Promise<RoadmapResponse> {
    const res = await fetch(`${API_BASE}/ai/roadmap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(analysis),
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Network error' }));
        throw new Error(err.detail || `Roadmap generation failed (${res.status})`);
    }
    return res.json();
}
