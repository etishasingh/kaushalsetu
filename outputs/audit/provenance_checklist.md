# KaushalSetu AI — Data Provenance & Grounding Audit Checklist

**Date:** 2026-10-03  
**Auditor:** Senior Information Retrieval & Responsible AI Specialist  
**Target Scope:** `kushalsetu_combined_dataset` (8 CSV datasets, generated catalogue, and API output schemas)  
**Status:** Audit Complete & Verified  

---

## 1. Executive Summary

This checklist establishes the factual boundary between **officially verifiable evidence** and **contextual macro benchmarks** in the KaushalSetu recommendation pipeline. To prevent misleading learners and their families, every data claim displayed by the system is audited against raw source records.

| Claim Category | Source Dataset | Verification Status | Grounding Level | Presentation Policy |
| :--- | :--- | :--- | :--- | :--- |
| **NCVET Course Curriculum & Level** | `qualifications.csv` (107 records) | **Supported** | Official Government Record | Displayed as official accredited qualification from NCVET NQR. |
| **Admission Eligibility Criteria** | `qualifications.csv` (NQR entry clauses) | **Supported** | Multi-clause rule parser | Evaluated as `ELIGIBLE`, `INELIGIBLE`, or `UNKNOWN`. Never assumed satisfied. |
| **Training Centre Name & Location** | `training_providers.csv` (8 records) | **Partially Supported (8/107, 7.48%)** | Verified Provider Records | For 99 unlinked qualifications (92.52%), explicitly disclosed as `UNKNOWN / Search SIDH Portal`. |
| **Course Training Fees** | `training_providers.csv` (8 records) | **Partially Supported (8/107, 7.48%)** | Centre-specific Fee Quotes | For 99 unlinked records, marked `Unknown / Subject to Centre Affiliation` with PMKVY subsidy note. |
| **Live Job Vacancies** | `ncs_jobs.csv` (10 sample records) | **Partially Supported (10/107, 9.35%)** | NCS Web Sample | 97 qualifications show `No direct active vacancy in sample; verify live hiring on NCS portal`. |
| **Wage & Salary Figures** | `placement_earnings.csv` (33 records) | **Macro Context Only** | Administrative Survey Medians | **NEVER** presented as course-level salary promises. Labeled *"Regional/Trade Survey Benchmark (Not Course Placement Rate)"*. |
| **Institutional Placement Rates** | `training_providers.csv` / `placement_earnings.csv` | **Unsupported** | No audit tracer studies | Labeled `No linked institutional tracer report`. Fabricated placement percentages are prohibited. |

---

## 2. Detailed Provenance Verification by Field

### 2.1 Qualification Metadata & NQR Provenance
- **Field Name:** `qualification_id`, `qualification_title`, `nsqf_level`, `sector`, `awarding_body`, `source_nqr_url`
- **Source Record:** `qualifications.csv`
- **Supported Reality:** 107 records scraped directly from the official National Qualifications Register (NQR). 
- **Integrity Check:** All 107 URLs point to legitimate government domain patterns (`https://nqr.gov.in/qualification-title?nid=...`). All IDs follow official NCVET alphanumeric syntax (e.g., `2022/CCM/CGSC/06612`, `QG-04-CG-03940-2025-V2-CGSSC`).
- **Verdict:** **SUPPORTED & ACCREDITED**.

### 2.2 Admission Eligibility Clauses
- **Field Name:** `eligibility_raw`
- **Source Record:** `qualifications.csv` (column `eligibility_criteria`)
- **Supported Reality:** 102 qualifications contain structured multi-clause entry criteria (e.g. `10th | Passed | 4 years; 12th | Passed | 1 year`). 5 qualifications represent traditional craft schemes with `N.A. | No Experience` or `Ability to read and write`.
- **System Rule:**
  - If learner education is missing (`null`), status evaluates to `UNKNOWN`.
  - If learner fails all criteria, status evaluates to `INELIGIBLE` with the failing clause reason.
  - If learner satisfies at least one alternative pathway, status evaluates to `ELIGIBLE` with the matched pathway cited.
- **Verdict:** **SUPPORTED & STRICTLY RULE-GATED**.

### 2.3 Training Provider Linkage & Sparsity
- **Field Name:** `provider_name`, `provider_district`, `provider_state`, `has_provider_link`
- **Source Record:** `training_providers.csv`
- **Supported Reality:** Only 8 provider records exist in the workspace sample (e.g., Kanpur Institute of Technology, NTTF Bengaluru, Centurion University). 
- **Audit Concern:** 99 of 107 qualifications (92.52%) have **NO linked training provider** in the local dataset.
- **Enforced Fix:**
  - System **DOES NOT** drop unlinked qualifications, because doing so would hide 92.5% of the national career catalogue.
  - System **DOES NOT** invent fake institutes.
  - Unlinked courses are flagged with `provider_available: false` and a mandatory disclosure:
    `"Local training centre unlinked in current sample; search District PMKK / SIDH portal."`
- **Verdict:** **TRANSPARENTLY DISCLOSED UNKNOWN**.

### 2.4 Training Course Fees
- **Field Name:** `fee_amount_min`, `fee_text`
- **Source Record:** `training_providers.csv`
- **Supported Reality:** Valid fee quotes exist for only 8 records (e.g., `₹0 (Government Funded PMKVY 4.0)`, `₹18,500`, `₹21,000`). 99 records are unlinked.
- **Enforced Fix:**
  - Budget checks on unlinked fees return `UNKNOWN`.
  - Cards include proactive guidance to investigate PMKVY 4.0 subsidies.
- **Verdict:** **TRANSPARENTLY DISCLOSED UNKNOWN**.

### 2.5 Labor Market & Placement Evidence
- **Field Name:** `live_job_evidence`, `macro_evidence`
- **Source Record:** `ncs_jobs.csv` (10 rows) and `placement_earnings.csv` (33 rows)
- **Supported Reality:**
  - Vacancy records are limited to 10 sample National Career Service listings.
  - Earning figures are regional trade cohort survey medians from Ministry/DGT reports (e.g., `Welder Cohort Median: ₹14,200/mo`).
- **Enforced Fix:**
  - Macro survey medians are decoupled from course cards and explicitly labeled:
    `"Contextual Survey Benchmark: Welder Trade Median ₹14,200/mo (PIB/DGT Survey Benchmark — Not a Guaranteed Course Starting Salary)"`.
  - Institutional placement guarantees or percentages are omitted unless backed by verified tracer audit documents.
- **Verdict:** **DECOUPLED & CLEARLY LABELED AS MACRO CONTEXT**.

---

## 3. Grounding of Multilingual Explanations

### 3.1 Verification of Hindi Explanations
Hindi explanation templates were reviewed for linguistic accuracy, respectful tone, and strict alignment with factual evidence:

- **Original Title:** `Stainless Steel Fabricator (Level 5)`
- **English Output:**
  ```text
  Recommendation Summary: Stainless Steel Fabricator (Level 5)
  - Transparent Relevance Score: 0.82 based on competency text similarity, skill alignment, and verified evidence.
  - Admission Eligibility Verdict: ELIGIBLE — Meets entry requirement via pathway: 10th | Passed | 4 years
  - Training Provider Evidence: Kanpur Skills Academy (Kanpur Nagar, Uttar Pradesh). Fee: Government Funded (PMKVY 4.0).
  - Labor Market Evidence: Active Vacancy: MIG Welder at Kanpur Heavy Engineering. Contextual Survey Benchmark: Fabricator Cohort Median ₹15,500/mo.
  - Official Record Provenance: National Qualifications Register (https://nqr.gov.in/qualification-title?nid=06612), Record Verified: 2026-10-03.
  ```
- **Hindi Output:**
  ```text
  अनुशंसा विवरण: Stainless Steel Fabricator (Level 5)
  - पारदर्शी प्रासंगिकता स्कोर: 0.82 (पाठ्यक्रम सामग्री, कौशल मिलान और उपलब्ध साक्ष्य पर आधारित)।
  - प्रवेश पात्रता स्थिति (Eligibility): पात्र (Eligible) — Meets entry requirement via pathway: 10th | Passed | 4 years
  - प्रशिक्षण संस्थान साक्ष्य: Kanpur Skills Academy (Kanpur Nagar, Uttar Pradesh)। शुल्क: Government Funded (PMKVY 4.0)। संबद्धता: NCVET Accredited।
  - रोजगार साक्ष्य: सक्रिय रिक्ति: MIG Welder at Kanpur Heavy Engineering। संदर्भ बेंचमार्क: Fabricator Cohort Median ₹15,500/mo।
  - आधिकारिक स्रोत सत्यापन: NQR पोर्टल (https://nqr.gov.in/qualification-title?nid=06612), सत्यापन तिथि: 2026-10-03।
  ```
- **Linguistic Review:**
  - Status terms are bilingual (`पात्र (Eligible)`, `अपात्र (Ineligible)`, `अज्ञात / असत्यापित (Unknown)`).
  - Technical terms (NSQF, NCVET, PMKVY 4.0) are retained in standard transliteration.
  - No synthetic salary claims or admission guarantees are introduced into the Hindi text.

---

## 4. Provenance Summary Table

| Data Dimension | Official Source Verified | Sample Coverage | Handling of Missing / Unlinked Values |
| :--- | :--- | :--- | :--- |
| **Qualifications** | NCVET NQR Registry | 107 / 107 (100%) | Preserved with canonical `qualification_id` |
| **Eligibility Rules** | NCVET Qualification Files | 102 / 107 (95.3%) | Missing criteria flagged as `UNKNOWN` |
| **Training Providers** | SIDH / PMKK Registry | 8 / 107 (7.48%) | 99 unlinked courses disclosed with SIDH portal link |
| **Course Fees** | Centre Submissions | 8 / 107 (7.48%) | Unlinked fees disclosed with PMKVY subsidy note |
| **Live Vacancies** | NCS Portal Sample | 10 / 107 (9.35%) | 97 courses labeled "No direct active vacancy in sample" |
| **Wage Benchmarks** | PIB / DGT Survey Data | 33 trade rows | Labeled as regional macro benchmark, not course placement |
