# KaushalSetu AI: Validation & Backend Integration Summary

**Project:** KaushalSetu AI Recommender System  
**Phase:** Validation, Test Automation, Backend API & Frontend Integration  
**Date:** October 2026  
**Auditor / Engineer:** Senior Machine Learning Engineer  
**Status:** All 6 Phases Completed & Verified  

---

## 1. Summary of Changes & Preserved Assets

### Original Assets Preserved 100% Unaltered
- `career_referral_directory.csv` (8,538 bytes)
- `counseling_concerns_evidence.csv` (65,095 bytes)
- `counseling_intake_profiles.csv` (14,159 bytes)
- `labour_market_household_context.csv` (5,668 bytes)
- `ncs_jobs.csv` (6,347 bytes)
- `placement_earnings.csv` (5,916 bytes)
- `qualifications.csv` (155,419 bytes)
- `training_providers.csv` (8,782 bytes)
- `kaushalsetu_recommendation_engine.ipynb` (Original prototype notebook preserved)

### New Files Created
- **`outputs/audit/audit_report.md`:** Comprehensive audit documenting risks AUD-01 through AUD-07.
- **`outputs/audit/evaluation_benchmark_results.json`:** Transparent IR benchmark and 12-scenario unit metrics.
- **`backend/config.py`:** Centralized paths, scoring weights, educational hierarchies, and environment variables.
- **`backend/schemas.py`:** Pydantic request/response schemas with input validation.
- **`backend/eligibility.py`:** Multi-clause NCVET admission parser, location, duration, and budget evaluators.
- **`backend/data_loader.py`:** Cached catalogue and pre-trained artifact manager with startup health check.
- **`backend/recommendation_service.py`:** Production hybrid recommendation engine with zero-hallucination explainability.
- **`backend/main.py`:** FastAPI REST application exposing `/health`, `/api/careers`, `POST /api/recommendations`, and `/api/careers/{qualification_id}`.
- **`backend/tests/test_evaluation_suite.py`:** Automated 12-scenario test runner and persistent-ID benchmark.
- **`backend/tests/test_api.py`:** FastAPI integration test suite using `TestClient`.
- **`frontend/index.html`:** Accessible learner profile exploration interface with dynamic status indicators.
- **`frontend/styles.css`:** Clean modern styling with responsive layout and color-coded status badges.
- **`frontend/app.js`:** Vanilla JavaScript client connecting to FastAPI backend with full state handling.
- **`outputs/audit/integration_summary.md`:** This summary report.

---

## 2. Data & Provenance Findings

1. **Benchmark Grounding:** Previous evaluation metrics ($P@3=0.40$) relied on heuristic array indices (`[0, 4, 33, 40]`). We refactored the evaluation protocol to use persistent, immutable `qualification_id` strings, documenting the benchmark as an **expert-annotated heuristic reference** rather than claiming unverified real-world accuracy.
2. **Provider Sparsity:** 92.52% of national qualifications in `qualifications.csv` lack training center records in `training_providers.csv`. The backend maintains the **non-discarding policy**, labeling unlinked qualifications with `UNKNOWN` location/fee status and adding clear missingness disclosures.
3. **Macro Benchmark Disambiguation:** Macro-level survey salaries (from PIB and DGT ITI surveys) are explicitly separated into `macro_benchmark` to prevent learners from mistaking state cohort averages for guaranteed course placement wages.
4. **Duplicate Title Disambiguation:** Duplicate titles (e.g. `Stainless Steel Fabricator` Level 5 in 2022 vs 2025) are disambiguated in the API and UI via `display_title` (e.g. `Stainless Steel Fabricator (Level 5 • CGSSC • 2022)`).

---

## 3. API Endpoints & Request/Response Examples

### 1. Health Check
- **Endpoint:** `GET /health`
- **Response:**
```json
{
  "status": "healthy",
  "api_version": "2.0.0",
  "catalogue_loaded": true,
  "total_qualifications": 107,
  "vectorizer_loaded": true,
  "dense_embeddings_loaded": true,
  "linked_providers_count": 8,
  "missingness_rate_pct": 92.52
}
```

### 2. Browse Careers
- **Endpoint:** `GET /api/careers?page=1&page_size=2`
- **Response:**
```json
{
  "total_count": 107,
  "page": 1,
  "page_size": 2,
  "items": [
    {
      "qualification_id": "2022/CCM/CGSC/06612",
      "qualification_title": "Stainless Steel Fabricator",
      "display_title": "Stainless Steel Fabricator (Level 5 • CGSSC • 2022)",
      "nsqf_level": "Level 5",
      "sector": "Capital Goods & Manufacturing",
      "awarding_body": "Capital Goods and Strategic Skill Council (CGSSC)",
      "duration_hours": "600",
      "has_provider_link": true,
      "source_nqr_url": "https://nqr.gov.in/qualifications/3607"
    }
  ]
}
```

### 3. Generate Recommendations
- **Endpoint:** `POST /api/recommendations`
- **Request Payload:**
```json
{
  "interests": ["welding", "sheet metal fabrication"],
  "preferred_activities": ["operating cutting tools", "manual arc welding"],
  "existing_qualification": "10th",
  "prior_experience_years": 4.0,
  "current_district": "Kanpur Nagar",
  "current_state": "Uttar Pradesh",
  "willingness_to_relocate": "within_district",
  "max_duration_hours": 600.0,
  "max_budget_inr": 0.0,
  "top_k": 3
}
```
- **Response Structure:** Returns ranked `recommendations` with:
  - `hybrid_score` and `score_breakdown` (text, skills, preference, eligibility, evidence).
  - `eligibility_status` (`ELIGIBLE`), `eligibility_reason`.
  - `training_provider_evidence` (Centum WorkSkills, Kanpur Nagar, Government Funded PMKVY 4.0).
  - `employment_evidence` (Live NCS job: Stainless Steel Fabricator at Lohia Aerospace).
  - `missing_information` disclosures.
  - Grounded multilingual explanations (`explanation_english` and `explanation_hindi`).

---

## 4. Test Commands & Actual Execution Results

### 12-Scenario Independent Evaluation Suite
- **Command:** `python -X utf8 backend/tests/test_evaluation_suite.py`
- **Result:** `Ran 12 tests in 0.374s. OK.`
- **Coverage:**
  1. Missing learner profile fields: PASSED
  2. No matching qualifications (gibberish query): PASSED
  3. Ineligible learner: PASSED
  4. Unknown eligibility requirements: PASSED
  5. Alternative eligibility routes: PASSED
  6. Missing/stale source information: PASSED
  7. Duplicate qualifications disambiguation: PASSED
  8. Empty skill lists: PASSED
  9. Invalid/unknown qualification IDs: PASSED
  10. Ranking consistency and determinism: PASSED
  11. Malformed API requests (validation error): PASSED
  12. No eligible results (strict filtering): PASSED

### Persistent ID Benchmark Metrics (`outputs/audit/evaluation_benchmark_results.json`)
- **Mean Precision@3:** `0.8889`
- **Mean Precision@5:** `0.5333`
- **Mean Recall@5:** `0.7167`
- **Mean Reciprocal Rank (MRR):** `1.000`
- **Catalogue Coverage:** `14 qualifications (13.08%)`
- **Eligibility Engine Unit Accuracy:** `1.000 (100%)`

### FastAPI REST API Test Suite
- **Command:** `python -X utf8 backend/tests/test_api.py`
- **Result:** `Ran 6 tests in 0.216s. OK.`
- **Verified:** `/health` (200), `/api/careers` (200), `/api/careers/{id}` (200 & 404), `POST /api/recommendations` (200 & 422).

---

## 5. Frontend Integration Status

- **Architecture:** Pure HTML5, CSS3, and Vanilla JavaScript with zero external runtime dependencies.
- **Location:** `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`.
- **Form Mapping:**
  - `interests` $\to$ `profile.interests`
  - `preferredActivities` $\to$ `profile.preferred_activities`
  - `education` $\to$ `profile.existing_qualification`
  - `experience` $\to$ `profile.prior_experience_years`
  - `district` / `state` $\to$ `profile.current_district` / `profile.current_state`
  - `relocation` $\to$ `profile.willingness_to_relocate`
  - `maxDuration` $\to$ `profile.max_duration_hours`
  - `maxBudget` $\to$ `profile.max_budget_inr`
  - `excludeUnknownLocation` $\to$ `profile.exclude_unknown_location`
  - `excludeUnknownFees` $\to$ `profile.exclude_unknown_fees`
  - `languagePref` $\to$ renders English or Hindi explanation card
- **State Handling:** Loading spinner, error banner with retry button, empty state card when 0 results qualify, and rich result cards with color-coded eligibility badges.
- **Configurability:** API base URL defaults to `http://127.0.0.1:8000`, overridable via query parameter `?api=http://...` or `window.API_BASE_URL`.

---

## 6. How to Run Locally

### 1. Run All Tests
```bash
# Run 12-scenario evaluation suite
python -X utf8 backend/tests/test_evaluation_suite.py

# Run FastAPI integration tests
python -X utf8 backend/tests/test_api.py
```

### 2. Start the Backend API
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger documentation is available at: `http://127.0.0.1:8000/docs`

### 3. Open the Frontend
Open `frontend/index.html` directly in any modern browser, or serve it with Python:
```bash
python -m http.server 3000 --directory frontend
```
Navigate to: `http://localhost:3000`
