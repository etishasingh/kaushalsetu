# KaushalSetu Vocational-Career Recommendation Engine: Engineering & Methodological Report

**Project:** KaushalSetu AI Recommender System  
**Role:** Senior Machine Learning Engineer (Recommender Systems, IR, Responsible AI)  
**Artifact:** Final Technical & Methodological Report  
**Date:** October 2026  
**License:** Open Public Dataset & Transparent Implementation  

---

## 1. Executive Summary & Problem Formulation

Vocational education and career selection in India represent high-stakes, life-altering decisions for learners and their families. Conventional e-commerce or entertainment recommender systems—which optimize for click-through rates (CTR), dwell time, or engagement—are fundamentally misaligned with this domain. In vocational counseling:
- **No ground-truth "click" signal exists:** A recommendation cannot be judged by user clicks, which often reflect prestige bias, advertising spend, or misconceptions rather than suitability.
- **Constraints are strictly binding:** Recommending a course for which a learner lacks prerequisites (e.g. demanding 10th pass + 4 years experience when the learner has 8th pass) or which requires unaffordable fees causes severe distress and attrition.
- **Data missingness is structural, not random:** The vast majority of national vocational qualifications lack direct, automated links to local private or public training providers in existing administrative databases. Silently dropping options with missing fields would disproportionately exclude valid, high-potential career pathways.
- **Hallucination is unacceptable:** Fabricating placement rates, starting salaries, course fees, or government accreditation risks leading vulnerable youth into unregulated or predatory training centers.

To address these challenges, we designed and built the **KaushalSetu Hybrid Explainable Recommendation Engine**. The engine integrates:
1. **Content-Based Information Retrieval (IR):** Transparent TF-IDF and Latent Semantic Analysis (LSA) dense concept retrieval to identify occupations matching explicitly declared learner interests.
2. **Rule-Based Eligibility & Constraint Engine:** Deterministic parsing of multi-clause National Qualifications Register (NQR) entry standards, location proximity, duration windows, and financial constraints, with an explicit **non-discarding unknown-handling policy**.
3. **Evidence-Based Hybrid Ranking:** Configurable multi-criteria scoring combining lexical match, skill overlap, preference fit, eligibility confidence, and evidence completeness.
4. **Grounded Explainability Layer:** Deterministic, evidence-bound explanation generators in English and Hindi, coupled with an optional LLM interface that strictly forbids hallucination and requires provenance citations.

---

## 2. Dataset Architecture & Record Linkage Audit

We performed a deep inspection across eight distinct CSV datasets provided in the project workspace, strictly avoiding blind merges:

| Dataset | Records | Features | Core Role in Pipeline | Linkage Key & Methodology |
| :--- | :---: | :---: | :--- | :--- |
| `qualifications.csv` | 107 | 12 | Base Career & Qualification Catalogue (NCVET/NQR) | Primary Key: `qualification_id` |
| `training_providers.csv` | 8 | 28 | Accredited Training Centres, Fees, Facilities | Foreign Key: `qualification_id` (8 exact matches) |
| `ncs_jobs.csv` | 10 | 26 | Live National Career Service Vacancies | Semantic trade overlap on `job_role` |
| `placement_earnings.csv` | 33 | 11 | Macro Tracer Study Benchmarks (DGT ITI, PMKVY, PLFS) | Cohort trade-group codes (`CTS_WELD`, `CTS_FITT`, etc.) |
| `career_referral_directory.csv` | 20 | 13 | Verified Counsellors & Model Career Centres | District/State referral routing |
| `counseling_intake_profiles.csv` | 100 | 11 | Empirical Learner Constraints & Preferences | 1-to-1 Match on `session_id` with concerns dataset |
| `counseling_concerns_evidence.csv` | 100 | 12 | Learner/Family Anxiety Drivers & Evidence Gaps | 1-to-1 Match on `session_id` with intake dataset |
| `labour_market_household_context.csv`| 12 | 30 | PLFS Microdata Labour Market Context | District & trade-level wage/contract reference |

### Record Linkage & Data Missingness Findings
1. **Provider Linkage Gap:** Only 8 of the 107 qualifications in `qualifications.csv` (7.48%) have explicit, verified training center rows in `training_providers.csv`. The remaining 99 qualifications (92.52%) represent valid national qualifications whose specific provider affiliation requires state-level Skill India Digital Hub (SIDH) queries. Silently filtering out unlinked qualifications would wipe out 92.5% of the national career catalogue!
2. **Contextual Macro Evidence:** `placement_earnings.csv` provides macro-level tracer survey evidence (from MSDE tracer studies and PIB releases). We link these as **contextual reference benchmarks** rather than attributing them as micro-level placement guarantees for specific private centers.

---

## 3. Exploratory Data Analysis & Text Preprocessing

### Data Quality & Schema Cleaning
- **NSQF Distribution:** Qualifications span NSQF Levels 2 through 6.5, with the highest concentration at Level 4.5 (24.3%), Level 4 (22.4%), and Level 3 (15.9%).
- **Duration Characteristics:** Duration ranges from 30 hours to 1,800 hours, with major peaks at 600 hours (18 courses), 1,350 hours (13 courses), and 1,200 hours (12 courses). Non-numeric ranges (e.g. `210 - 270`, `360 - 480`) were parsed into `(min_hours, max_hours, expected_hours)`.
- **Text Cleansing in Job Roles:** The `job_role` column in `qualifications.csv` contained placeholder noise such as `'- - -'`, `'---'`, and `'----'`, which were cleaned to null and substituted with parsed qualification titles during document text construction.
- **Language Coverage Assessment:** An audit of all 8 CSV files verified that the text corpus is 100% in English (using Indian vocational terminology: ITI, NTC/NAC, PMKVY, Fitter, Turner, Machinist). However, `counseling_intake_profiles.csv` reveals that 36% of learners prefer Hindi and 18% prefer Bengali or Bilingual modes. Therefore, query terms require cross-lingual term mapping, and explanations must support Hindi rendering without altering the underlying English qualification identifiers.

---

## 4. The Recommendation Architecture

```
+-------------------------------------------------------------+
|                  Learner Explicit Profile                   |
|  - Interests & Activities                                   |
|  - Education Level & Experience                             |
|  - District & Relocation Preference                         |
|  - Max Duration & Voluntarily Supplied Budget               |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|         Stage 1: Content-Based Information Retrieval        |
|  - TF-IDF Lexical Retrieval (Domain-preserving N-grams)     |
|  - Latent Semantic Analysis (TruncatedSVD Dense Concepts)   |
|  - Output: Candidate pool with cosine similarity scores     |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|         Stage 2: Rule-Based Constraint & Eligibility        |
|  - Education Ladder Verification (NCVET Multi-Clause)       |
|  - Location Proximity Check (Confirmed Centre vs Unspecified)|
|  - Duration Budget Check                                    |
|  - Course Fee Limit Check (PMKVY Free vs Paid vs Unknown)   |
|  - UNKNOWN-Field Non-Discarding Policy                      |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|         Stage 3: Transparent Hybrid Evidence Ranking        |
|  S_hybrid = w_text*S_text + w_skills*S_skills +             |
|             w_pref*S_pref + w_elig*S_elig + w_evid*S_evid   |
|  - Configurable, normalized weights                         |
|  - No placement claims used as mechanical rank boosters     |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|         Stage 4: Grounded Multilingual Explainability       |
|  - Structured Recommendation Cards with Evidence Provenance |
|  - Zero-Hallucination Explanations in English & Hindi       |
|  - Proactive Inquiry Questions for Learner & Family         |
+-------------------------------------------------------------+
```

---

## 5. Algorithmic Detail & Formulations

### 5.1 Content-Based Retrieval (TF-IDF & Latent Semantic Analysis)
For each qualification $i \in \{1, \dots, N\}$, a comprehensive document representation $D_i$ is constructed:
$$D_i = \text{Title}_i \oplus \text{Role}_i \oplus \text{Sector}_i \oplus \text{Competencies}_i \oplus \text{Progression}_i$$
Text is tokenized with sublinear term-frequency scaling and n-gram range $(1, 2)$, yielding sparse vector $\mathbf{v}_i \in \mathbb{R}^V$. For query $\mathbf{q}$ formed from learner interests and preferred activities:
$$S_{\text{text}}(q, D_i) = \frac{\mathbf{q} \cdot \mathbf{v}_i}{\|\mathbf{q}\|_2 \|\mathbf{v}_i\|_2} \in [0, 1]$$
In addition, we compute a 64-dimensional dense semantic concept representation using TruncatedSVD:
$$\mathbf{u}_i = \text{TruncatedSVD}_{k=64}(\mathbf{v}_i), \quad S_{\text{dense}}(q, D_i) = \frac{\mathbf{u}_q \cdot \mathbf{u}_i}{\|\mathbf{u}_q\|_2 \|\mathbf{u}_i\|_2}$$

### 5.2 Deterministic NCVET Multi-Clause Eligibility Engine
In the NCVET system, eligibility criteria are defined as disjunctions of conjunctions:
$$\text{Eligible}(L, Q) \iff \bigvee_{k=1}^K \left( \text{Edu}(L) \ge \text{ReqEdu}_k \land \text{Exp}(L) \ge \text{ReqExp}_k \land \text{NSQF}(L) \ge \text{ReqNSQF}_k \right)$$
Where the educational ladder is strictly ordered:
$$\text{None (0)} < \text{Literate (1)} < \text{8th (3)} < \text{10th (4)} < \text{11th (5)} < \text{12th/ITI (6)} < \text{Diploma (7)} < \text{UG/Graduate (8)} < \text{B.Tech/BE (9)}$$
- If the learner meets at least one pathway $k$, status is **`ELIGIBLE`**.
- If the learner fails all pathways $k$, status is **`INELIGIBLE`** with explicit reasons for each clause.
- If qualification eligibility is missing or the learner did not declare their education, status is **`UNKNOWN`**.

### 5.3 Unknown-Field Non-Discarding Policy
Let $\mathcal{C}$ be the set of constraints (education, location, duration, budget). For each option $i$:
$$\text{Status}(i, c) \in \{\text{ELIGIBLE}, \text{INELIGIBLE}, \text{UNKNOWN}\}$$
An option is filtered out if and only if:
$$\exists c \in \mathcal{C} \text{ s.t. } \text{Status}(i, c) = \text{INELIGIBLE} \quad \lor \quad (\text{Status}(i, c) = \text{UNKNOWN} \land \text{ExcludeUnknown}_c = \text{True})$$
By default, $\text{ExcludeUnknown}_c = \text{False}$, guaranteeing that courses lacking localized provider or fee links are never silently discarded.

### 5.4 Hybrid Ranking Formula
$$S_{\text{hybrid}} = w_1 S_{\text{text}} + w_2 S_{\text{skills}} + w_3 S_{\text{pref}} + w_4 S_{\text{elig}} + w_5 S_{\text{evid}}$$
- $w_1 = 0.40$ (Text relevance via cosine similarity)
- $w_2 = 0.25$ (Skill & competency token overlap)
- $w_3 = 0.15$ (Duration & relocation match)
- $w_4 = 0.10$ (Eligibility confidence: 1.0 for eligible, 0.5 for unknown, 0.0 for soft ineligible)
- $w_5 = 0.10$ (Evidence completeness: official NQR verification, provider link, live vacancy match)
- $\sum_{m=1}^5 w_m = 1.0$, guaranteeing $S_{\text{hybrid}} \in [0, 1]$.

---

## 6. Evaluation Framework & Responsible AI Auditing

### 6.1 Information Retrieval Metrics
Evaluated across a benchmark of representative vocational test personas with manually audited relevance judgements:
- **Mean Precision@3 (P@3):** $0.400$
- **Mean Precision@5 (P@5):** $0.240$
- **Mean Recall@5 (R@5):** $0.300$
- **Mean Reciprocal Rank (MRR):** $0.433$
- **Catalogue Coverage:** $23.36\%$ (25 unique qualifications retrieved across test queries)

### 6.2 Missingness & Bias Audit
- **Unlinked Provider Rate:** 92.52% of catalogue items have unlinked training centers.
- **Fairness Guarantee:** Under our non-discarding policy, 100% of these 99 qualifications remain discoverable based on their national occupational standards. The output explicitly flags missing local provider data and directs the learner to the district Model Career Centre or SIDH portal.
- **Zero Demographic Inference:** The learner preference schema contains zero proxies for caste, religion, gender, or parental dominance.

---

## 7. Explainability & Output Format

Every recommendation generates a complete, auditable **Recommendation Card**:
1. **Title, Role & NSQF Level:** Cleaned qualification metadata.
2. **Transparent Score Breakdown:** Individual contributions of text, skills, preference, eligibility, and evidence.
3. **Eligibility Status & Evidence:** Specific qualifying clause or explanation of missing criteria.
4. **Training Provider Details:** Center name, location, fee amount, and NCVET accreditation status.
5. **Labor Market Evidence:** Live NCS vacancies and regional DGT tracer study median earnings.
6. **Provenance:** Source NQR URL, SIDH URL, and last verification date (`2026-10-03`).
7. **Proactive Investigation Questions:** Practical questions for the family to ask training center administrators (e.g. PMKVY 4.0 subsidy eligibility, practical machine hours vs theory).

---

## 8. Artifacts Generated

The following artifacts have been generated in the project workspace:
- `outputs/eda/dataset_inventory.json`: Comprehensive schema, missingness, and shape report.
- `outputs/eda/nsqf_distribution.png`: Bar plot of NSQF qualification levels.
- `outputs/eda/duration_distribution.png`: Histogram and KDE of course durations.
- `outputs/eda/missingness_matrix.png`: Missingness percentage across catalogue features.
- `outputs/eda/counseling_concerns.png`: Distribution of empirical learner counseling concerns.
- `outputs/recommendations/career_catalogue.csv`: Enriched, unified 107-item career catalogue.
- `outputs/recommendations/sample_recommendations.json`: Sample output cards for test learner profiles.
- `outputs/recommendations/evaluation.json`: Exact IR benchmark metrics and missingness audit.
- `outputs/models/tfidf_vectorizer.joblib`: Trained scikit-learn TF-IDF model.
- `outputs/models/dense_embeddings.npy`: Cached 64-dimensional dense semantic concept vectors.
- `outputs/final_recommendation_report.md`: This comprehensive report.

---

## 9. Production Roadmap & Future Work

1. **SIDH API Direct Integration:** Connect to Skill India Digital Hub REST endpoints to dynamically query live training center batches for the 99 currently unlinked national qualifications.
2. **Multilingual Cross-Encoder Reranking:** Deploy an on-device multilingual transformer (e.g. `paraphrase-multilingual-MiniLM-L12-v2`) to enable direct queries in Devanagari script (Hindi/Marathi) and Bengali.
3. **Longitudinal Tracer Studies:** Incorporate real-time employer hiring feedback from National Career Service (NCS) API integrations to track 12-month post-training wage retention.
