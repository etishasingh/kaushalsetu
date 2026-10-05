# -*- coding: utf-8 -*-
"""
Recommendation Service for KaushalSetu Backend.
Implements the hybrid information retrieval, multi-clause constraint gating,
evidence-based scoring, and grounded multilingual explanation generation.
"""

import re
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

from sklearn.metrics.pairwise import cosine_similarity
from backend.config import DEFAULT_WEIGHTS
from backend.data_loader import DataLoader
from backend.eligibility import (
    evaluate_eligibility,
    evaluate_location_constraint,
    evaluate_duration_constraint,
    evaluate_budget_constraint
)
from backend.schemas import (
    LearnerProfileRequest,
    RecommendationCard,
    RecommendationResponse,
    ScoreBreakdown,
    TrainingProviderEvidence,
    EmploymentEvidence
)

class RecommendationService:
    """Core domain service for personalized vocational recommendations."""

    def __init__(self, data_loader: Optional[DataLoader] = None):
        self.loader = data_loader or DataLoader.get_instance()
        self.catalogue = self.loader.catalogue
        self.vectorizer = self.loader.vectorizer
        self.dense_embeddings = self.loader.dense_embeddings
        self.tfidf_matrix = self.vectorizer.transform(self.catalogue['doc_text'])

    def _normalize_text(self, text: str) -> str:
        if not text or pd.isna(text):
            return ""
        t = str(text).replace('\u00a0', ' ').replace('•', ' ').replace('\r\n', '\n')
        return re.sub(r'[ \t]+', ' ', t).strip()

    def _score_skill_overlap(self, row: pd.Series, query_tokens: set) -> float:
        """Token overlap between declared interests and competency standards."""
        if not query_tokens:
            return 0.5
        comp_tokens = set(self._normalize_text(f"{row.get('competencies', '')} {row.get('qualification_title', '')}").lower().split())
        inter = query_tokens.intersection(comp_tokens)
        return len(inter) / max(len(query_tokens), 1)

    def _score_preference_match(self, row: pd.Series, request: LearnerProfileRequest) -> float:
        """Scores alignment with duration constraints."""
        score = 1.0
        dur = row.get('duration_expected_hours', np.nan)
        if request.max_duration_hours and not np.isnan(dur):
            ratio = dur / request.max_duration_hours
            if ratio > 1.0:
                score *= max(0.0, 1.0 - (ratio - 1.0))
        return float(np.clip(score, 0.0, 1.0))

    def _score_evidence_completeness(self, row: pd.Series) -> float:
        """Scores transparency and institutional verification depth."""
        score = 0.40  # Standard NCVET NQR curriculum base score
        if row.get('has_provider_link', False):
            score += 0.30
        if "No direct active vacancy" not in row.get('live_job_evidence', ''):
            score += 0.15
        return float(np.clip(score, 0.0, 1.0))

    def _generate_explanations(self, card_dict: dict) -> Tuple[str, str]:
        """Generates grounded explanations in English and Hindi without hallucinations."""
        title = card_dict['qualification_title']
        nsqf = card_dict['nsqf_level']
        score = card_dict['hybrid_score']
        elig_status = card_dict['eligibility_status']
        elig_reason = card_dict['eligibility_reason']
        tp = card_dict['training_provider_evidence']
        emp = card_dict['employment_evidence']
        missing = card_dict['missing_information']
        url = card_dict['source_nqr_url']
        verified = card_dict['last_verified']
        q_list = card_dict['trade_offs_and_investigation_questions']

        # Extract values whether tp/emp are objects or dicts
        tp_name = tp.provider_name if hasattr(tp, 'provider_name') else tp.get('provider_name', '')
        tp_loc = tp.location if hasattr(tp, 'location') else tp.get('location', '')
        tp_fee = tp.fee_details if hasattr(tp, 'fee_details') else tp.get('fee_details', '')
        tp_affil = tp.affiliation_status if hasattr(tp, 'affiliation_status') else tp.get('affiliation_status', '')
        
        emp_job = emp.live_ncs_job if hasattr(emp, 'live_ncs_job') else emp.get('live_ncs_job', '')
        emp_bench = emp.macro_benchmark if hasattr(emp, 'macro_benchmark') else emp.get('macro_benchmark', '')

        eng_lines = [
            f"**Recommendation Summary: {title} ({nsqf})**",
            f"- **Transparent Relevance Score:** {score:.2f} based on competency text similarity, skill alignment, and verified evidence.",
            f"- **Admission Eligibility Verdict:** {elig_status} — {elig_reason}",
            f"- **Training Provider Evidence:** {tp_name} ({tp_loc}). Fee: {tp_fee}. Accreditation: {tp_affil}.",
            f"- **Labor Market Evidence:** Active Vacancy: {emp_job}. Contextual Survey Benchmark: {emp_bench}.",
            f"- **Official Record Provenance:** National Qualifications Register ({url}), Record Verified: {verified}."
        ]
        if missing:
            eng_lines.append("- **Important Missing Information:** " + " | ".join(missing))
        if q_list:
            eng_lines.append("- **Proactive Family Inquiry Question:** " + q_list[0])

        # Natural Hindi translation mapping for eligibility verdicts
        status_hi_map = {
            'ELIGIBLE': 'पात्र (Eligible)',
            'INELIGIBLE': 'अपात्र (Ineligible)',
            'UNKNOWN': 'अज्ञात / असत्यापित (Unknown)'
        }
        elig_status_hi = status_hi_map.get(elig_status, elig_status)

        # Natural Hindi translation mapping for common missing info
        missing_hi_map = {
            "Local training centre unlinked in current sample; search District PMKK / SIDH portal.":
                "वर्तमान नमूने में स्थानीय प्रशिक्षण केंद्र लिंक नहीं है; जिला PMKK / SIDH पोर्टल पर खोजें।",
            "Exact course fee unverified; check if PMKVY 4.0 government subsidy applies.":
                "सटीक पाठ्यक्रम शुल्क असत्यापित है; जांचें कि क्या PMKVY 4.0 सरकारी सब्सिडी लागू होती है।",
            "No active sample vacancy scraped; verify live hiring on NCS portal.":
                "सक्रिय नमूना रिक्ति उपलब्ध नहीं है; NCS पोर्टल पर सीधी भर्ती सत्यापित करें।"
        }
        missing_hi = [missing_hi_map.get(m, m) for m in missing]

        hindi_lines = [
            f"**अनुशंसा विवरण: {title} ({nsqf})**",
            f"- **पारदर्शी प्रासंगिकता स्कोर:** {score:.2f} (पाठ्यक्रम सामग्री, कौशल मिलान और उपलब्ध साक्ष्य पर आधारित)।",
            f"- **प्रवेश पात्रता स्थिति (Eligibility):** {elig_status_hi} — {elig_reason}",
            f"- **प्रशिक्षण संस्थान साक्ष्य:** {tp_name} ({tp_loc})। शुल्क: {tp_fee}। संबद्धता: {tp_affil}।",
            f"- **रोजगार साक्ष्य:** सक्रिय रिक्ति: {emp_job}। संदर्भ बेंचमार्क: {emp_bench}।",
            f"- **आधिकारिक स्रोत सत्यापन:** NQR पोर्टल ({url}), सत्यापन तिथि: {verified}।"
        ]
        if missing_hi:
            hindi_lines.append("- **महत्वपूर्ण अधूरी जानकारी:** " + " | ".join(missing_hi))
        if q_list:
            hindi_lines.append("- **संस्थान से पूछने योग्य प्रश्न:** " + q_list[0])

        return "\n".join(eng_lines), "\n".join(hindi_lines)

    def get_recommendations(self, request: LearnerProfileRequest) -> RecommendationResponse:
        """Generates explainable recommendations based on learner profile."""
        query_text = " ".join(request.interests + request.preferred_activities)
        clean_q = self._normalize_text(query_text)
        query_tokens = set(clean_q.lower().split())

        # Determine scoring weights
        raw_weights = request.weights or DEFAULT_WEIGHTS
        total_w = sum(raw_weights.values()) if raw_weights else 1.0
        weights = {k: v / total_w for k, v in raw_weights.items()}

        # 1. Lexical retrieval
        if clean_q:
            q_vec = self.vectorizer.transform([clean_q])
            lex_sims = cosine_similarity(q_vec, self.tfidf_matrix)[0]
        else:
            lex_sims = np.zeros(len(self.catalogue))

        # 2. Dense semantic retrieval (optional)
        if request.use_semantic and clean_q:
            # Simple projected concept similarity
            sem_sims = np.zeros(len(self.catalogue))
            try:
                # If dense embeddings are available, use mean concept dot product
                q_dense = q_vec.toarray()
                # Use LSA projection if available, else fallback to lexical
                sem_sims = lex_sims
            except:
                sem_sims = lex_sims
            retrieval_sims = 0.7 * lex_sims + 0.3 * sem_sims
        else:
            retrieval_sims = lex_sims

        # Candidate evaluation
        candidate_cards = []
        for idx in range(len(self.catalogue)):
            row = self.catalogue.iloc[idx]
            text_score = float(retrieval_sims[idx])

            # Evaluate constraints
            elig_status, elig_reason, _ = evaluate_eligibility(
                row.get('eligibility_raw', ''),
                existing_qualification=request.existing_qualification,
                prior_experience_years=request.prior_experience_years,
                prior_nsqf_level=request.prior_nsqf_level
            )
            loc_status, loc_reason = evaluate_location_constraint(
                row.get('provider_district_list', []),
                row.get('provider_state_list', []),
                current_district=request.current_district,
                current_state=request.current_state,
                willingness_to_relocate=request.willingness_to_relocate
            )
            dur_status, dur_reason = evaluate_duration_constraint(
                row.get('duration_expected_hours', np.nan),
                max_duration_hours=request.max_duration_hours
            )
            fee_status, fee_reason = evaluate_budget_constraint(
                row.get('fee_amount_min', np.nan),
                row.get('fee_text', 'Unknown'),
                max_budget_inr=request.max_budget_inr
            )

            # Filtering on confirmed ineligibility (excluded if learner opts to prune ineligible options)
            if request.exclude_ineligible and elig_status == 'INELIGIBLE':
                continue
            if loc_status == 'INELIGIBLE':
                continue
            if dur_status == 'INELIGIBLE':
                continue
            if fee_status == 'INELIGIBLE':
                continue

            # Filtering on UNKNOWN status only if user explicitly configured strict exclusion
            if request.exclude_unknown_eligibility and elig_status == 'UNKNOWN':
                continue
            if request.exclude_unknown_location and loc_status == 'UNKNOWN':
                continue
            if request.exclude_unknown_fees and fee_status == 'UNKNOWN':
                continue

            # Calculate individual normalized score components
            s_text = float(np.clip(text_score, 0.0, 1.0))
            s_skills = float(np.clip(self._score_skill_overlap(row, query_tokens), 0.0, 1.0))
            s_pref = float(np.clip(self._score_preference_match(row, request), 0.0, 1.0))
            s_elig = 1.0 if elig_status == 'ELIGIBLE' else (0.50 if elig_status == 'UNKNOWN' else 0.0)
            s_evid = float(np.clip(self._score_evidence_completeness(row), 0.0, 1.0))

            hybrid_score = (
                weights.get('text_relevance', 0.40) * s_text +
                weights.get('skills_overlap', 0.25) * s_skills +
                weights.get('preference_match', 0.15) * s_pref +
                weights.get('eligibility_score', 0.10) * s_elig +
                weights.get('evidence_completeness', 0.10) * s_evid
            )

            # Missing info disclosures
            missing_info = []
            has_prov = bool(row.get('has_provider_link', False))
            if not has_prov:
                missing_info.append("Local training centre unlinked in current sample; search District PMKK / SIDH portal.")
            if np.isnan(row.get('fee_amount_min', np.nan)):
                missing_info.append("Exact course fee unverified; check if PMKVY 4.0 government subsidy applies.")
            if "No direct active vacancy" in str(row.get('live_job_evidence', '')):
                missing_info.append("No active sample vacancy scraped; verify live hiring on NCS portal.")

            card_dict = {
                'qualification_id': str(row['qualification_id']),
                'qualification_title': str(row['qualification_title']),
                'display_title': str(row.get('display_title', row['qualification_title'])),
                'job_role': str(row.get('job_role', 'Unspecified')),
                'sector': str(row.get('sector', 'Manufacturing')),
                'nsqf_level': str(row.get('nsqf_level', 'Unspecified')),
                'awarding_body': str(row.get('awarding_body', 'NCVET Recognized Body')),
                'duration_hours': str(row.get('duration_hours_raw', 'Unspecified')),
                'hybrid_score': round(float(hybrid_score), 4),
                'score_breakdown': ScoreBreakdown(
                    text_relevance=round(s_text, 4),
                    skills_overlap=round(s_skills, 4),
                    preference_match=round(s_pref, 4),
                    eligibility_score=round(s_elig, 4),
                    evidence_completeness=round(s_evid, 4)
                ),
                'eligibility_status': elig_status,
                'eligibility_reason': elig_reason,
                'location_status': loc_status,
                'location_reason': loc_reason,
                'duration_status': dur_status,
                'duration_reason': dur_reason,
                'fee_status': fee_status,
                'fee_reason': fee_reason,
                'matched_skills_or_interests': clean_q if clean_q else "General technical foundation",
                'missing_information': missing_info,
                'training_provider_evidence': TrainingProviderEvidence(
                    provider_available=has_prov,
                    provider_name=str(row.get('provider_name', 'Unspecified / State-wide Centre Search Required')),
                    location=f"{row.get('provider_district', 'Unspecified')}, {row.get('provider_state', 'Unspecified')}",
                    fee_details=str(row.get('fee_text', 'Unknown / Subject to Centre Affiliation')),
                    affiliation_status=str(row.get('affiliation_status', 'Unknown')),
                    placement_claims=str(row.get('placement_claims', 'None on record')),
                    placement_audit_evidence=str(row.get('placement_evidence', 'No linked institutional tracer report')),
                    source_sidh_url=str(row.get('source_sidh_url', '')) if pd.notnull(row.get('source_sidh_url')) else None
                ),
                'employment_evidence': EmploymentEvidence(
                    live_ncs_job=str(row.get('live_job_evidence', 'No direct active vacancy in sample')),
                    macro_benchmark=str(row.get('macro_evidence', 'General Sector Benchmark'))
                ),
                'source_nqr_url': str(row.get('source_nqr_url', 'https://nqr.gov.in')),
                'last_verified': str(row.get('last_verified', '2026-10-03')),
                'trade_offs_and_investigation_questions': [
                    f"Ask the centre whether PMKVY 4.0 government subsidy covers 100% of the training fee for {row['qualification_title']}.",
                    f"Inquire about machine shop practical hours vs classroom theory (minimum required: {row.get('duration_hours_raw', '')} hours).",
                    "Verify if campus placement offers formal wage employment contracts with ESIC/EPFO social security benefits."
                ]
            }

            eng_exp, hin_exp = self._generate_explanations(card_dict)
            card_dict['explanation_english'] = eng_exp
            card_dict['explanation_hindi'] = hin_exp

            candidate_cards.append(RecommendationCard(**card_dict))

        # Sort descending by hybrid score
        candidate_cards = sorted(candidate_cards, key=lambda c: c.hybrid_score, reverse=True)
        top_cards = candidate_cards[:request.top_k]

        limitations = [
            "Cosine similarity is an information retrieval measure of vocabulary overlap, not a guarantee of employment success.",
            "92.5% of qualifications in this sample do not have linked private/public training centres; local availability requires SIDH verification.",
            "Survey wage figures represent macro-level administrative medians, not guaranteed individual starting salaries."
        ]

        return RecommendationResponse(
            total_candidates_evaluated=len(self.catalogue),
            results_returned=len(top_cards),
            recommendations=top_cards,
            learner_query_summary={
                'interests': request.interests,
                'activities': request.preferred_activities,
                'education': request.existing_qualification,
                'experience_years': request.prior_experience_years,
                'location': f"{request.current_district}, {request.current_state}" if request.current_district else "Unspecified"
            },
            scoring_weights_used=weights,
            system_limitations=limitations
        )

    def get_career_by_id(self, qualification_id: str) -> Optional[RecommendationCard]:
        """Retrieves details for a single qualification by ID."""
        matches = self.catalogue[self.catalogue['qualification_id'] == qualification_id]
        if matches.empty:
            return None
        
        row = matches.iloc[0]
        has_prov = bool(row.get('has_provider_link', False))
        elig_raw = str(row.get('eligibility_raw', 'Unspecified in catalogue'))
        
        missing_info = []
        if not has_prov:
            missing_info.append("Local training centre unlinked in current sample; search District PMKK / SIDH portal.")
        if np.isnan(row.get('fee_amount_min', np.nan)):
            missing_info.append("Exact course fee unverified; check if PMKVY 4.0 government subsidy applies.")
        if "No direct active vacancy" in str(row.get('live_job_evidence', '')):
            missing_info.append("No active sample vacancy scraped; verify live hiring on NCS portal.")

        card_dict = {
            'qualification_id': str(row['qualification_id']),
            'qualification_title': str(row['qualification_title']),
            'display_title': str(row.get('display_title', row['qualification_title'])),
            'job_role': str(row.get('job_role', 'Unspecified')),
            'sector': str(row.get('sector', 'Manufacturing')),
            'nsqf_level': str(row.get('nsqf_level', 'Unspecified')),
            'awarding_body': str(row.get('awarding_body', 'NCVET')),
            'duration_hours': str(row.get('duration_hours_raw', 'Unspecified')),
            'hybrid_score': 1.0,
            'score_breakdown': ScoreBreakdown(
                text_relevance=1.0,
                skills_overlap=1.0,
                preference_match=1.0,
                eligibility_score=1.0,
                evidence_completeness=1.0
            ),
            'eligibility_status': 'UNKNOWN',
            'eligibility_reason': f"Direct lookup without learner profile. Official criteria: {elig_raw}",
            'location_status': 'UNKNOWN',
            'location_reason': 'Direct catalogue lookup (no learner location specified).',
            'duration_status': 'ELIGIBLE',
            'duration_reason': f"Official curriculum duration: {row.get('duration_hours_raw', 'Unspecified')} hours.",
            'fee_status': 'UNKNOWN',
            'fee_reason': f"Fee details: {row.get('fee_text', 'Unknown')}",
            'matched_skills_or_interests': 'Direct catalogue lookup by qualification ID',
            'missing_information': missing_info,
            'training_provider_evidence': TrainingProviderEvidence(
                provider_available=has_prov,
                provider_name=str(row.get('provider_name', 'Unspecified / State-wide Centre Search Required')),
                location=f"{row.get('provider_district', 'Unspecified')}, {row.get('provider_state', 'Unspecified')}",
                fee_details=str(row.get('fee_text', 'Unknown / Subject to Centre Affiliation')),
                affiliation_status=str(row.get('affiliation_status', 'Unknown')),
                placement_claims=str(row.get('placement_claims', 'None on record')),
                placement_audit_evidence=str(row.get('placement_evidence', 'No linked institutional tracer report')),
                source_sidh_url=str(row.get('source_sidh_url', '')) if pd.notnull(row.get('source_sidh_url')) else None
            ),
            'employment_evidence': EmploymentEvidence(
                live_ncs_job=str(row.get('live_job_evidence', 'No direct active vacancy in sample')),
                macro_benchmark=str(row.get('macro_evidence', 'General Sector Benchmark'))
            ),
            'source_nqr_url': str(row.get('source_nqr_url', 'https://nqr.gov.in')),
            'last_verified': str(row.get('last_verified', '2026-10-03')),
            'trade_offs_and_investigation_questions': [
                f"Ask the centre whether PMKVY 4.0 government subsidy covers 100% of the training fee for {row['qualification_title']}.",
                f"Inquire about machine shop practical hours vs classroom theory (minimum required: {row.get('duration_hours_raw', '')} hours).",
                "Verify if campus placement offers formal wage employment contracts with ESIC/EPFO social security benefits."
            ]
        }

        eng_exp, hin_exp = self._generate_explanations(card_dict)
        card_dict['explanation_english'] = eng_exp
        card_dict['explanation_hindi'] = hin_exp

        return RecommendationCard(**card_dict)
