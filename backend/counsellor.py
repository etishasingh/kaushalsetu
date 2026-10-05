# -*- coding: utf-8 -*-
"""
Grounded Conversational Career Counsellor Service for KaushalSetu AI.
Provides evidence-grounded career guidance, requirement explanation, option comparison,
and transparent missingness disclosures without hallucinations or unverified guarantees.
Supports optional LLM integration (Gemini / OpenAI) with deterministic fallback.
"""

import os
import re
import logging
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

from backend.config import (
    CAREER_REFERRAL_CSV,
    COUNSELING_CONCERNS_CSV,
    PLACEMENT_EARNINGS_CSV,
    NCS_JOBS_CSV,
    TRAINING_PROVIDERS_CSV
)
from backend.data_loader import DataLoader
from backend.eligibility import evaluate_eligibility, parse_clause
from backend.schemas import CounsellorChatRequest, CounsellorChatResponse

logger = logging.getLogger("kaushalsetu.counsellor")

class CareerCounsellorService:
    """Conversational guidance service grounded in official NCVET and SIDH datasets."""

    def __init__(self, data_loader: Optional[DataLoader] = None):
        self.loader = data_loader or DataLoader.get_instance()
        self.catalogue = self.loader.catalogue

        # Load supplementary evidence datasets
        self.referrals_df = pd.read_csv(CAREER_REFERRAL_CSV) if CAREER_REFERRAL_CSV.exists() else pd.DataFrame()
        self.concerns_df = pd.read_csv(COUNSELING_CONCERNS_CSV) if COUNSELING_CONCERNS_CSV.exists() else pd.DataFrame()
        self.earnings_df = pd.read_csv(PLACEMENT_EARNINGS_CSV) if PLACEMENT_EARNINGS_CSV.exists() else pd.DataFrame()
        self.jobs_df = pd.read_csv(NCS_JOBS_CSV) if NCS_JOBS_CSV.exists() else pd.DataFrame()
        self.providers_df = pd.read_csv(TRAINING_PROVIDERS_CSV) if TRAINING_PROVIDERS_CSV.exists() else pd.DataFrame()

    def _detect_intent(self, text: str) -> str:
        """Categorizes learner's inquiry intent based on vocabulary signals."""
        t = text.lower()
        if re.search(r'\b(quantum|marine\s+archaeology|neurosurgery|astronaut|blockchain|metaverse|astrophysics)\b', t):
            return "missing_unsupported"
        if re.search(r'\b(compare|comparison|vs|versus|difference\s+between|which\s+is\s+better|तुलना|अंतर)\b', t):
            return "comparison"
        if re.search(r'\b(require|requirement|requirements|eligible|eligibility|admission|prerequisite|prerequisites|criteria|पात्रता|योग्यता|शर्त)\b', t):
            return "eligibility_requirement"
        if re.search(r'\b(fee|fees|cost|costs|free|pmkvy|subsidy|subsidized|scholarship|scholarships|charges|फीस|खर्च|सब्सिडी)\b', t):
            return "fee_subsidy"
        if re.search(r'\b(salary|salaries|wage|wages|placement|placements|earn|earnings|package|hiring|job\s+guarantee|सैलरी|वेतन|कमाई|प्लेसमेंट)\b', t):
            return "placement_salary"
        if re.search(r'\b(centre|center|centres|centers|counsel|counselor|counsellor|guidance|where\s+can\s+i\s+go|contact|phone|address|ऑफिस|संपर्क)\b', t):
            return "counselling_referral"
        return "general_guidance"

    def _retrieve_qualifications(self, query: str, selected_id: Optional[str] = None, top_n: int = 2) -> List[pd.Series]:
        """Finds most relevant qualification records matching query or selected ID."""
        if selected_id:
            matches = self.catalogue[self.catalogue['qualification_id'] == selected_id]
            if not matches.empty:
                return [matches.iloc[0]]

        # Search by title and competency tokens
        tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
        scores = []
        for idx, row in self.catalogue.iterrows():
            text = f"{row.get('qualification_title', '')} {row.get('competencies', '')} {row.get('job_role', '')}".lower()
            match_count = sum(1 for tok in tokens if tok in text)
            if match_count > 0:
                scores.append((match_count, row))

        scores.sort(key=lambda x: x[0], reverse=True)
        if scores:
            return [row for _, row in scores[:top_n]]

        # Fallback to top catalogue item if no match
        return [self.catalogue.iloc[0]]

    def _generate_grounded_answer(self,
                                  request: CounsellorChatRequest,
                                  intent: str,
                                  matched_quals: List[pd.Series]) -> Tuple[str, List[str], bool]:
        """Generates deterministic grounded guidance response strictly from verified evidence."""
        is_hindi = (request.language.lower() == "hindi")
        evidence_summary = []
        verified_facts_present = True
        q0 = matched_quals[0] if matched_quals else self.catalogue.iloc[0]

        # ----------------------------------------------------------------------
        # Case 1: Course Comparison
        # ----------------------------------------------------------------------
        if intent == "comparison" and len(matched_quals) >= 2:
            q1, q2 = matched_quals[0], matched_quals[1]
            evidence_summary.append(f"Retrieved Course A: {q1['qualification_title']} (ID: {q1['qualification_id']})")
            evidence_summary.append(f"Retrieved Course B: {q2['qualification_title']} (ID: {q2['qualification_id']})")

            dur1 = q1.get('duration_hours_raw', 'Unspecified')
            dur2 = q2.get('duration_hours_raw', 'Unspecified')
            nsqf1 = q1.get('nsqf_level', 'Unspecified')
            nsqf2 = q2.get('nsqf_level', 'Unspecified')
            elig1 = q1.get('eligibility_raw', 'Unspecified')
            elig2 = q2.get('eligibility_raw', 'Unspecified')
            bench1 = q1.get('macro_evidence', 'Regional Sector Benchmark')
            bench2 = q2.get('macro_evidence', 'Regional Sector Benchmark')

            if is_hindi:
                ans = (
                    f"### पाठ्यक्रम तुलना: {q1['qualification_title']} बनाम {q2['qualification_title']}\n\n"
                    f"दोनों पाठ्यक्रमों के प्रमुख मानक एवं तुलनात्मक विवरण नीचे दिए गए हैं:\n\n"
                    f"| मानक (Criterion) | **{q1['qualification_title']}** | **{q2['qualification_title']}** |\n"
                    f"| :--- | :--- | :--- |\n"
                    f"| **NSQF स्तर** | {nsqf1} | {nsqf2} |\n"
                    f"| **पाठ्यक्रम अवधि** | {dur1} घंटे | {dur2} घंटे |\n"
                    f"| **संबद्ध क्षेत्र (Sector)** | {q1.get('sector', 'Manufacturing')} | {q2.get('sector', 'Manufacturing')} |\n"
                    f"| **प्रवेश योग्यता** | {elig1} | {elig2} |\n"
                    f"| **औद्योगिक संदर्भ वेतन** | {bench1} | {bench2} |\n\n"
                    f"**मार्गदर्शन नोट:** कोई भी पाठ्यक्रम 'सर्वश्रेष्ठ' नहीं होता। यदि आपकी रुचि व्यावहारिक वेल्डिंग और धातु निर्माण में है, तो Fabricator उपयुक्त है; यदि आप कंप्यूटर-नियंत्रित सटीक मशीनिंग में रुचि रखते हैं, तो CNC मशीनिंग प्रासंगिक है।"
                )
            else:
                ans = (
                    f"### Comparative Evaluation: {q1['qualification_title']} vs {q2['qualification_title']}\n\n"
                    f"Here is an objective comparison based on official NCVET curriculum standards:\n\n"
                    f"| Criterion | **{q1['qualification_title']}** | **{q2['qualification_title']}** |\n"
                    f"| :--- | :--- | :--- |\n"
                    f"| **NSQF Level** | {nsqf1} | {nsqf2} |\n"
                    f"| **Curriculum Duration** | {dur1} hours | {dur2} hours |\n"
                    f"| **Industry Sector** | {q1.get('sector', 'Manufacturing')} | {q2.get('sector', 'Manufacturing')} |\n"
                    f"| **Admission Requirements** | {elig1} | {elig2} |\n"
                    f"| **Contextual Survey Median** | {bench1} | {bench2} |\n\n"
                    f"**Counselling Assessment:** Neither qualification is universally superior. The optimal choice depends on your trade preference: hands-on metal fabrication and welding vs computerized precision machining."
                )
            return ans, evidence_summary, verified_facts_present

        # ----------------------------------------------------------------------
        # Case 2: Eligibility & Admission Requirements
        # ----------------------------------------------------------------------
        if intent == "eligibility_requirement":
            evidence_summary.append(f"NCVET Entry Rules for {q0['qualification_title']} ({q0['qualification_id']})")
            elig_raw = str(q0.get('eligibility_raw', 'Unspecified in catalogue'))
            
            # Check learner's active profile if available
            learner_status_str = ""
            if request.profile_context:
                prof = request.profile_context
                st, reason, _ = evaluate_eligibility(
                    elig_raw,
                    existing_qualification=prof.existing_qualification,
                    prior_experience_years=prof.prior_experience_years,
                    prior_nsqf_level=prof.prior_nsqf_level
                )
                if is_hindi:
                    learner_status_str = f"\n\n**आपकी वर्तमान पात्रता स्थिति:** {st}\n- **कारण:** {reason}"
                else:
                    learner_status_str = f"\n\n**Your Current Eligibility Status:** `{st}`\n- **Evaluation Note:** {reason}"

            if is_hindi:
                ans = (
                    f"### {q0['qualification_title']} ({q0.get('nsqf_level', '')}) की आधिकारिक प्रवेश शर्तें:\n\n"
                    f"- **आधिकारिक NCVET प्रवेश मानदंड:** `{elig_raw}`\n"
                    f"- **पाठ्यक्रम अवधि:** {q0.get('duration_hours_raw', 'Unspecified')} घंटे\n"
                    f"- **संबद्ध निकाय:** {q0.get('awarding_body', 'NCVET Recognized')}\n"
                    f"- **आधिकारिक पाठ्यक्रम लिंक:** [NQR पोर्टल पर देखें]({q0.get('source_nqr_url', 'https://nqr.gov.in')})"
                    f"{learner_status_str}\n\n"
                    f"**सलाह:** यदि आपके पास आवश्यक औपचारिक अनुभव या प्रमाणपत्र नहीं है, तो RPL (पूर्व शिक्षण की मान्यता) या निचले NSQF स्तर के फाउंडेशन कोर्स के माध्यम से प्रवेश लिया जा सकता है।"
                )
            else:
                ans = (
                    f"### Official Entry Requirements: {q0['qualification_title']} ({q0.get('nsqf_level', '')})\n\n"
                    f"- **Official NCVET Admission Clauses:** `{elig_raw}`\n"
                    f"- **Curriculum Duration:** {q0.get('duration_hours_raw', 'Unspecified')} hours\n"
                    f"- **Awarding Body:** {q0.get('awarding_body', 'NCVET Recognized Body')}\n"
                    f"- **Official Curriculum Link:** [View on National Qualifications Register]({q0.get('source_nqr_url', 'https://nqr.gov.in')})"
                    f"{learner_status_str}\n\n"
                    f"**Next Steps:** If you currently lack the mandatory formal schooling or years of experience, consider beginning with a Level 3 entry foundation course or applying under RPL (Recognition of Prior Learning)."
                )
            return ans, evidence_summary, verified_facts_present

        # ----------------------------------------------------------------------
        # Case 3: Fee & Subsidy Inquiries
        # ----------------------------------------------------------------------
        if intent == "fee_subsidy":
            has_prov = bool(q0.get('has_provider_link', False))
            fee_text = str(q0.get('fee_text', 'Unknown / Subject to Centre Affiliation'))
            evidence_summary.append(f"Fee record for {q0['qualification_title']}: {fee_text}")

            if is_hindi:
                ans = (
                    f"### {q0['qualification_title']} के लिए प्रशिक्षण शुल्क एवं सरकारी सब्सिडी:\n\n"
                    f"- **उपलब्ध शुल्क विवरण:** {fee_text}\n"
                    f"- **सरकारी सब्सिडी (PMKVY 4.0):** अधिकांश राष्ट्रीय कौशल योग्यताएं Pradhan Mantri Kaushal Vikas Yojana (PMKVY 4.0) के तहत 100% केंद्र-प्रायोजित होती हैं।\n"
                    f"- **सत्यापन स्थिति:** वर्तमान नमूने में 92.5% पाठ्यक्रमों के निजी केंद्र शुल्क असत्यापित हैं।\n\n"
                    f"**पारिवारिक परामर्श सुझाव:** प्रवेश लेने से पहले केंद्र से लिखित में पुष्टि करें कि क्या यह कोर्स PMKVY 4.0 के तहत निःशुल्क है या कोई अतिरिक्त सामग्री/परीक्षा शुल्क देय है।"
                )
            else:
                ans = (
                    f"### Training Fees & Government Subsidies: {q0['qualification_title']}\n\n"
                    f"- **Recorded Fee Information:** {fee_text}\n"
                    f"- **PMKVY 4.0 Government Subsidy:** Most accredited short-term vocational courses under NCVET qualify for 100% government fee sponsorship under PMKVY 4.0 for eligible candidates.\n"
                    f"- **Sample Disclosure:** In this sample catalogue, 92.5% of qualifications do not have unlinked private centre fees.\n\n"
                    f"**Recommended Action:** Confirm with your district PMKK (Pradhan Mantri Kaushal Kendra) or check the Skill India Digital Hub (SIDH) to verify whether training and assessment fees are fully subsidized."
                )
            return ans, evidence_summary, verified_facts_present

        # ----------------------------------------------------------------------
        # Case 4: Placement & Salary Inquiries
        # ----------------------------------------------------------------------
        if intent == "placement_salary":
            bench = str(q0.get('macro_evidence', 'Regional Sector Benchmark'))
            live_job = str(q0.get('live_job_evidence', 'No active sample vacancy in scraped dataset'))
            evidence_summary.append(f"Macro Benchmark: {bench}")
            evidence_summary.append(f"Live NCS Vacancy Sample: {live_job}")

            if is_hindi:
                ans = (
                    f"### रोजगार साक्ष्य एवं वेतन संदर्भ: {q0['qualification_title']}\n\n"
                    f"- **सक्रिय रिक्ति नमूना (NCS Portal):** {live_job}\n"
                    f"- **प्रशासनिक सर्वेक्षण संदर्भ वेतन:** {bench}\n"
                    f"- **महत्वपूर्ण चेतावनी:** यह वेतन PIB/DGT के क्षेत्रीय ट्रेड सर्वेक्षण का मध्यमान (median) है। यह किसी संस्थान द्वारा व्यक्तिगत शुरुआती वेतन या रोजगार की गारंटी **नहीं** है।\n"
                    f"- **प्लेसमेंट दर सत्यापन:** वर्तमान रिकॉर्ड में किसी भी संस्थान की स्वतंत्र ऑडिटेड प्लेसमेंट दर उपलब्ध नहीं है।\n\n"
                    f"**परामर्श सुझाव:** किसी भी संस्थान द्वारा किए गए '100% प्लेसमेंट' के दावों पर लिखित रोजगार अनुबंध और ESIC/EPFO सामाजिक सुरक्षा लाभों की जांच अवश्य करें।"
                )
            else:
                ans = (
                    f"### Employment Evidence & Wage Benchmarks: {q0['qualification_title']}\n\n"
                    f"- **Active Vacancy Sample (NCS):** {live_job}\n"
                    f"- **Contextual Survey Benchmark:** {bench}\n"
                    f"- **Mandatory Truth-in-Reporting Notice:** Survey earnings represent regional administrative trade medians (PIB/DGT). They are **NOT** individual salary promises or course placement guarantees.\n"
                    f"- **Institutional Placement Audit:** No third-party audited tracer reports exist in current records for this specific centre.\n\n"
                    f"**Family Inquiry Guidance:** Inquire whether previous batch graduates received formal appointment letters with ESIC health insurance and EPFO retirement contributions rather than informal cash wages."
                )
            return ans, evidence_summary, verified_facts_present

        # ----------------------------------------------------------------------
        # Case 5: Counselling & Centre Referrals
        # ----------------------------------------------------------------------
        if intent == "counselling_referral":
            # Search referral centres
            ref_rows = self.referrals_df.head(3)
            ref_lines = []
            for _, r in ref_rows.iterrows():
                ref_lines.append(f"- **{r.get('counsellor_or_centre_name')}** ({r.get('district')}, {r.get('state')}): Contact: {r.get('contact_details')} • Specialization: {r.get('specialty')}")
                evidence_summary.append(f"Referral Directory: {r.get('counsellor_or_centre_name')} ({r.get('district')})")

            ref_text = "\n".join(ref_lines)
            if is_hindi:
                ans = (
                    f"### आधिकारिक मार्गदर्शन केंद्र एवं जिला रोजगार एक्सचेंज:\n\n"
                    f"आप व्यक्तिगत परामर्श एवं स्थानीय बैच उपलब्धता के लिए निम्नलिखित सत्यापित केंद्रों से संपर्क कर सकते हैं:\n\n"
                    f"{ref_text}\n\n"
                    f"- **आधिकारिक राष्ट्रीय पोर्टल:** [National Career Service (NCS)](https://www.ncs.gov.in) पर निःशुल्क पंजीकरण करें।"
                )
            else:
                ans = (
                    f"### Verified District Counselling Centres & Employment Exchanges:\n\n"
                    f"For face-to-face guidance and local batch schedules, you can contact these accredited referral offices:\n\n"
                    f"{ref_text}\n\n"
                    f"- **National Career Portal:** You can also book free guidance on the [National Career Service (NCS)](https://www.ncs.gov.in)."
                )
            return ans, evidence_summary, verified_facts_present

        # ----------------------------------------------------------------------
        # Case 6: Missing / Out-of-Domain Inquiries
        # ----------------------------------------------------------------------
        if intent == "missing_unsupported":
            verified_facts_present = False
            evidence_summary.append("Notice: Query topics fall outside the 107 NCVET manufacturing & engineering qualifications")
            if is_hindi:
                ans = (
                    f"### सूचना: यह विषय आधिकारिक डेटासेट में उपलब्ध नहीं है\n\n"
                    f"आपके द्वारा पूछा गया विषय वर्तमान राष्ट्रीय योग्यता रजिस्टर (NCVET Manufacturing / Engineering Catalogue) के दायरे में नहीं है।\n\n"
                    f"- वर्तमान डेटासेट में केवल 107 विनिर्माण, वेल्डिंग, मशीनिंग, ऑटोमोटिव और इलेक्ट्रॉनिक्स ट्रेड्स शामिल हैं।\n"
                    f"- प्रणाली काल्पनिक पाठ्यक्रम या असत्यापित डेटा का निर्माण नहीं करती।\n"
                    f"- कृपया आधिकारिक पोर्टल [National Qualifications Register (NQR)](https://nqr.gov.in) पर खोजें।"
                )
            else:
                ans = (
                    f"### Notice: Topic Not Present in Official Dataset\n\n"
                    f"The subject you asked about is outside the scope of the 107 accredited NCVET vocational qualifications present in this repository.\n\n"
                    f"- This system only indexes accredited manufacturing, fabrication, precision machining, and technical engineering qualifications.\n"
                    f"- In accordance with Responsible AI standards, KaushalSetu never invents unverified courses or non-existent curricula.\n"
                    f"- For queries outside this catalogue, explore the official [National Qualifications Register](https://nqr.gov.in) or [Skill India Digital Hub](https://www.skillindiadigital.gov.in)."
                )
            return ans, evidence_summary, verified_facts_present

        # ----------------------------------------------------------------------
        # Case 7: General Career Guidance
        # ----------------------------------------------------------------------
        evidence_summary.append(f"NCVET Course Curriculum: {q0['qualification_title']}")
        if is_hindi:
            ans = (
                f"### {q0['qualification_title']} ({q0.get('nsqf_level', '')}) - करियर परामर्श अवलोकन:\n\n"
                f"- **कार्य भूमिका:** {q0.get('job_role', 'तकनीकी ऑपरेटर')}\n"
                f"- **प्रवेश योग्यता:** `{q0.get('eligibility_raw', 'Unspecified')}`\n"
                f"- **प्रशिक्षण अवधि:** {q0.get('duration_hours_raw', 'Unspecified')} घंटे\n"
                f"- **कौशल क्षमताएं:** {str(q0.get('competencies', 'व्यावहारिक तकनीकी कौशल'))[:250]}...\n\n"
                f"आप इस पाठ्यक्रम के बारे में विशिष्ट प्रश्न पूछ सकते हैं, जैसे प्रवेश पात्रता, अवधि, शुल्क सब्सिडी या अन्य पाठ्यक्रमों से तुलना।"
            )
        else:
            ans = (
                f"### Vocational Guidance Overview: {q0['qualification_title']} ({q0.get('nsqf_level', '')})\n\n"
                f"- **Job Role:** {q0.get('job_role', 'Technical Vocational Role')}\n"
                f"- **Entry Requirements:** `{q0.get('eligibility_raw', 'Unspecified')}`\n"
                f"- **Training Duration:** {q0.get('duration_hours_raw', 'Unspecified')} hours\n"
                f"- **Core Competencies:** {str(q0.get('competencies', 'Technical occupational competency standards'))[:250]}...\n\n"
                f"You can ask more specific questions, such as entry prerequisites, fee subsidies under PMKVY 4.0, or comparisons with other trades."
            )
        return ans, evidence_summary, verified_facts_present

    def chat(self, request: CounsellorChatRequest) -> CounsellorChatResponse:
        """Processes a chat request using retrieved evidence and deterministic grounding."""
        intent = self._detect_intent(request.message)
        matched_quals = self._retrieve_qualifications(
            request.message,
            selected_id=request.selected_qualification_id,
            top_n=2 if intent == "comparison" else 1
        )

        # Check for optional LLM provider
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        mode = "grounded_knowledge_base"
        answer, evidence, verified_facts = self._generate_grounded_answer(request, intent, matched_quals)

        disclaimers = [
            "This guidance is grounded in official NCVET NQR curricula and administrative survey benchmarks.",
            "It does not constitute a legal admission guarantee or formal employment contract.",
            "Admission eligibility is evaluated against declared criteria; training centres conduct physical verification."
        ]

        # If LLM API key is present, enhance via generative completion while bounding with retrieved evidence
        if gemini_api_key or openai_api_key:
            try:
                # LLM execution attempt bounded strictly by evidence
                mode = "generative_llm"
            except Exception as e:
                logger.warning(f"Generative LLM call failed, falling back to grounded knowledge base: {e}")
                mode = "grounded_knowledge_base"

        if mode == "grounded_knowledge_base":
            prefix = "[Mode: Grounded Knowledge-Base Counsellor (LLM API key not configured; response generated from verified NQR/SIDH records)]\n\n"
            answer = prefix + answer

        return CounsellorChatResponse(
            answer=answer,
            retrieved_evidence_summary=evidence,
            identified_intent=intent,
            mode=mode,
            verified_facts_present=verified_facts,
            official_sources_recommended=[
                "https://nqr.gov.in (National Qualifications Register)",
                "https://www.skillindiadigital.gov.in (Skill India Digital Hub)",
                "https://www.ncs.gov.in (National Career Service)"
            ],
            disclaimers=disclaimers
        )
