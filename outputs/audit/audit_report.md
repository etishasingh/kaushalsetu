# KaushalSetu AI: Implementation Audit & Technical Risk Report

**Auditor:** Senior Machine Learning Engineer (Recommender Systems, Information Retrieval, Responsible AI)  
**Date:** October 2026  
**Artifact Inspected:** `kaushalsetu_recommendation_engine.ipynb`, `outputs/recommendations/career_catalogue.csv`, `outputs/models/`  
**Status:** Audit Completed — Critical Findings & Remediation Plan Documented  

---

## 1. Executive Summary

An exhaustive technical, architectural, and data-integrity audit was conducted on the existing prototype implementation of the **KaushalSetu Recommendation Engine**. 

While the existing system established an explainable hybrid architecture (combining TF-IDF lexical search, LSA semantic concepts, rule-based constraint checks, and evidence scoring), the audit revealed **critical methodological, alignment, and data-integrity risks** that must be resolved before production backend deployment:

1. **Unvalidated Benchmark Claims:** The reported five-query evaluation metrics ($P@3=0.40, R@5=0.30, \text{MRR}=0.433$) relied on heuristic, author-assigned integer array indices rather than independent relevance labels. They were evaluated against the same catalogue used during tuning.
2. **Brittle Row-Index Linking:** Test queries and evaluations linked catalogue items using positional integer array indices (`0, 4, 33, 40`) rather than persistent `qualification_id` strings. Any sorting, filtering, or catalogue refresh corrupts these associations.
3. **Risk of Macro Evidence Misattribution:** Macro-level tracer survey benchmarks from `placement_earnings.csv` (e.g. DGT ITI CTS welder survey) were loosely matched to individual qualifications via keyword heuristics, posing a severe risk that learners interpret macro survey averages as guaranteed placement outcomes for specific short courses.
4. **Structural Missingness Bias:** 92.52% of national qualifications in `qualifications.csv` lack training provider, fee, or centre records in `training_providers.csv`. While the non-discarding policy correctly avoids dropping them, downstream APIs must explicitly separate verified institutional data from state-wide search requirements.
5. **Title Ambiguity in Versioned Qualifications:** Multiple qualification revisions share identical titles (e.g., `Stainless Steel Fabricator` Level 5 2022 vs 2025; `Locksmith` Level 2.5 vs Level 3). Without version or awarding body qualifiers, API consumers receive ambiguous records.

---

## 2. Detailed Findings, Severity, Evidence & Remediation

| ID | Issue Description | Severity | Evidence | Recommended Remediation |
| :--- | :--- | :---: | :--- | :--- |
| **AUD-01** | **Evaluation Benchmark Lacks Independent Relevance Labels** | **HIGH** | The 5 benchmark queries in `test_engine.py` / notebook use hardcoded integer lists assigned by inspection. No double-blind or multi-annotator protocol was conducted. | Formally document these queries as **synthetic heuristic unit-test cases**. Report metrics with explicit sample size disclosures. Do not present them as empirical real-world accuracy. |
| **AUD-02** | **Positional Integer Index Dependency** | **HIGH** | Queries reference items as `[0, 4, 33, 40]` rather than persistent `qualification_id` strings (e.g. `2022/CCM/CGSC/06612`). Re-sorting or updating the catalogue invalidates all labels. | Refactor all benchmarks and evaluation suites to use immutable `qualification_id` keys. |
| **AUD-03** | **Macro-Level Survey Evidence Misattribution** | **MEDIUM-HIGH** | Keyword matching links DGT ITI survey salaries to unrelated private or short-term training options. | Decouple macro survey benchmarks into a separate `contextual_benchmark` field explicitly labeled as *"Regional/Trade Benchmark (Not Course Placement Rate)"*. |
| **AUD-04** | **Severe Training Provider Sparsity (92.5% Missing)** | **MEDIUM** | Only 8 of 107 qualifications in `qualifications.csv` exist in `training_providers.csv`. | Provide structured boolean flags (`provider_linked: false`) so the backend and frontend can guide learners to district PMKK / SIDH locators. |
| **AUD-05** | **Duplicate Qualification Titles** | **MEDIUM** | `Stainless Steel Fabricator` appears twice; `Locksmith` appears twice across different NSQF levels. | Mandate unambiguous display names combining Title, NSQF Level, and Awarding Body in API responses. |
| **AUD-06** | **Artifact-Catalogue Alignment & Versioning Gap** | **MEDIUM** | `dense_embeddings.npy` contains raw vectors with no manifest linking row indices to `qualification_id`s. | Create an artifact manifest (`model_manifest.json`) verifying hash, vector shape, scikit-learn version, and `qualification_id` sequence. Validate on startup. |
| **AUD-07** | **Incomplete Educational Ladder Edge Cases** | **LOW-MEDIUM** | Clauses such as `3-year UG in relevant field or 4-years UG` or `2nd Year of 3 Year Diploma` can fail standard parsing. | Expand clause parsing rules with regex fallbacks and ensure unparseable clauses fail safely to `UNKNOWN`. |

---

## 3. Data & Verification Integrity Audit

We audited all claims of "verified" or "official" data across the 8 CSV datasets:

1. **`qualifications.csv`:** Data sourced from NCVET National Qualifications Register. Provenance URLs are valid format (`https://nqr.gov.in/qualifications/...`). However, `last_verified` is a uniform snapshot date (`2026-10-03`). The status reflects curriculum registration, NOT current batch availability.
2. **`training_providers.csv`:** Providers list `Accredited & Affiliated` or `PMKK Accredited Partner`. Source links point to Skill India Digital Hub (`https://www.skillindiadigital.gov.in/...`). These 8 records are confirmed authentic institutional listings, but represent a limited regional sample.
3. **`ncs_jobs.csv`:** 10 real job vacancies from the National Career Service. Verified employers (e.g. Lohia Aerospace, NTPC Alstom, Bharat Electronics). However, vacancies have expiry dates in late 2026; live status must be checked via NCS API in production.
4. **`placement_earnings.csv`:** Administrative benchmarks from PIB releases (PRID 2226505) and DGT State Tracer Studies. Figures (e.g. median wage ₹14,500 - ₹22,500) represent macro cohort medians, not guarantees.

**Conclusion:** Source URLs and provenance metadata must be preserved and rendered with explicit qualifying text. The system must never claim a provider is "verified" unless corroborated by the source record.

---

## 4. Remediation Architecture

The audited issues will be resolved in Phase 2 through Phase 6:
- Dedicated, decoupled `backend/` architecture with Pydantic validation.
- Persistent `qualification_id`-based evaluation and recommendation routing.
- Contextual separation of micro course facts from macro labour benchmarks.
- Automated 12-scenario unit and integration test suite.
- Clean frontend integration preserving existing UI conventions.
