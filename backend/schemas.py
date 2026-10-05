
# -*- coding: utf-8 -*-
"""
Pydantic Request and Response Schemas for KaushalSetu API.
Enforces strict type validation, field constraints, and prevents leaking sensitive data.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class LearnerProfileRequest(BaseModel):
    """Schema for incoming learner recommendation requests."""
    interests: Optional[List[str]] = Field(default_factory=list, description="List of self-declared vocational interests.")
    preferred_activities: Optional[List[str]] = Field(default_factory=list, description="Self-declared preferred practical activities.")
    existing_qualification: Optional[str] = Field(None, description="Current highest education level (e.g. 8th, 10th, 12th, ITI, Diploma, Graduate).")
    prior_experience_years: float = Field(default=0.0, ge=0.0, le=50.0, description="Years of formal or informal work experience.")
    prior_nsqf_level: Optional[float] = Field(None, ge=1.0, le=10.0, description="Highest previously earned NSQF qualification level.")
    
    current_district: Optional[str] = Field(None, description="Learner's current home district.")
    current_state: Optional[str] = Field(None, description="Learner's current home state.")
    willingness_to_relocate: str = Field(default="within_district", description="'near_home', 'within_district', 'state_capital', or 'nationally'.")
    
    max_duration_hours: Optional[float] = Field(None, gt=0, le=5000, description="Maximum training duration willing to commit.")
    max_budget_inr: Optional[float] = Field(None, ge=0.0, description="Maximum voluntary course fee budget.")
    earning_timeline: Optional[str] = Field(None, description="Target timeline to begin earning (e.g. immediate, within 6 months).")
    language_preference: str = Field(default="English", description="Preferred output language: 'English' or 'Hindi'.")
    
    # Flags for handling incomplete, unlinked, or ineligible information
    exclude_ineligible: bool = Field(default=False, description="Whether to exclude options where entry prerequisites are not met.")
    exclude_unknown_eligibility: bool = Field(default=False, description="Whether to exclude options where entry prerequisites are unverified.")
    exclude_unknown_location: bool = Field(default=False, description="Whether to exclude options where local centre location is unlinked.")
    exclude_unknown_fees: bool = Field(default=False, description="Whether to exclude options where course fee is unlinked.")
    
    top_k: int = Field(default=5, ge=1, le=50, description="Number of recommendations to return.")
    weights: Optional[Dict[str, float]] = Field(None, description="Custom scoring weights.")
    use_semantic: bool = Field(default=False, description="Whether to use 64-d LSA dense semantic retrieval alongside lexical search.")

    @field_validator('interests', 'preferred_activities', mode='before')
    @classmethod
    def clean_text_lists(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item and str(item).strip()]
        return []

    @field_validator('existing_qualification', 'current_district', 'current_state', mode='before')
    @classmethod
    def clean_optional_strings(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        v_str = str(v).strip()
        return v_str if v_str else None

class ScoreBreakdown(BaseModel):
    text_relevance: float = Field(..., ge=0.0, le=1.0)
    skills_overlap: float = Field(..., ge=0.0, le=1.0)
    preference_match: float = Field(..., ge=0.0, le=1.0)
    eligibility_score: float = Field(..., ge=0.0, le=1.0)
    evidence_completeness: float = Field(..., ge=0.0, le=1.0)

class TrainingProviderEvidence(BaseModel):
    provider_available: bool
    provider_name: str
    location: str
    fee_details: str
    affiliation_status: str
    placement_claims: str
    placement_audit_evidence: str
    source_sidh_url: Optional[str] = None

class EmploymentEvidence(BaseModel):
    live_ncs_job: str
    macro_benchmark: str

class RecommendationCard(BaseModel):
    qualification_id: str
    qualification_title: str
    display_title: str
    job_role: str
    sector: str
    nsqf_level: str
    awarding_body: str
    duration_hours: str
    hybrid_score: float = Field(..., ge=0.0, le=1.0)
    score_breakdown: ScoreBreakdown
    eligibility_status: str = Field(..., description="'ELIGIBLE', 'INELIGIBLE', or 'UNKNOWN'")
    eligibility_reason: str
    location_status: str
    location_reason: str
    duration_status: str
    duration_reason: str
    fee_status: str
    fee_reason: str
    matched_skills_or_interests: str
    missing_information: List[str]
    training_provider_evidence: TrainingProviderEvidence
    employment_evidence: EmploymentEvidence
    source_nqr_url: str
    last_verified: str
    trade_offs_and_investigation_questions: List[str]
    explanation_english: str
    explanation_hindi: str

class RecommendationResponse(BaseModel):
    total_candidates_evaluated: int
    results_returned: int
    recommendations: List[RecommendationCard]
    learner_query_summary: Dict[str, Any]
    scoring_weights_used: Dict[str, float]
    system_limitations: List[str]

class CareerSummary(BaseModel):
    qualification_id: str
    qualification_title: str
    display_title: str
    nsqf_level: str
    sector: str
    awarding_body: str
    duration_hours: str
    has_provider_link: bool
    source_nqr_url: str

class CareerListResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    items: List[CareerSummary]

class HealthResponse(BaseModel):
    status: str
    api_version: str
    catalogue_loaded: bool
    total_qualifications: int
    vectorizer_loaded: bool
    dense_embeddings_loaded: bool
    linked_providers_count: int
    missingness_rate_pct: float

class CounsellorChatRequest(BaseModel):
    """Request model for conversational career counselling endpoint."""
    message: str = Field(..., min_length=1, max_length=1000, description="Learner's guidance question or vocational query.")
    profile_context: Optional[LearnerProfileRequest] = Field(None, description="Optional active learner profile context.")
    selected_qualification_id: Optional[str] = Field(None, description="Optional specific qualification ID under inquiry.")
    language: str = Field(default="English", description="'English' or 'Hindi'.")

class CounsellorChatResponse(BaseModel):
    """Response model for conversational career counselling endpoint."""
    answer: str
    retrieved_evidence_summary: List[str]
    identified_intent: str
    mode: str = Field(..., description="'generative_llm' or 'grounded_knowledge_base'")
    verified_facts_present: bool
    official_sources_recommended: List[str]
    disclaimers: List[str]

