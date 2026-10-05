# KaushalSetu

## Overview
**KaushalSetu** is an explainable vocational career guidance, recommendation, and AI counselling platform designed for learners and families exploring accredited Indian vocational qualifications under the National Qualifications Register (NQR / NCVET) and Skill India Digital Hub (SIDH).

The platform bridges the gap between learner aspirations and accredited skill courses by combining semantic course search, multi-clause eligibility verification, labor-market benchmarking (via National Career Service), and transparent evidence disclosures.

---

## Key Features
- **Explainable Hybrid Recommendation Engine:** Combines TF-IDF keyword relevance, dense semantic embeddings, and rule-based preference weighting.
- **Multi-Clause Eligibility Verification:** Transparently evaluates educational prerequisites, prior work experience, course duration limits, and budget constraints.
- **Evidence-Based Grounded Ranking:** Discloses real training provider affiliations, verified course costs, and placement claims while flagging missing data.
- **Bilingual Guidance (English & Hindi):** Generates contextual justifications in both English and Hindi for accessible family decision-making.
- **Interactive AI Career Counsellor:** Conversational assistant grounded in verified NCVET and SIDH datasets (`/api/counsellor/chat`) with speech-to-text and text-to-speech support.
- **Curated Video Learning Journeys:** Integrated career video explorer mapping skills and qualifications to verified video demonstrations.
- **Unified Full-Stack Single-Service Architecture:** Serves both static frontend assets and FastAPI backend endpoints from a single unified web process.

---

## Architecture

```text
Frontend (HTML5 / Vanilla CSS / Modern JS)
   │
   │  REST API Calls (/health, /api/recommendations, /api/careers, /api/counsellor/chat)
   ▼
FastAPI Unified Backend (backend/main.py)
   │
   ├─► Static Asset Serving (/ & /static)
   ├─► CORS & Request Middleware
   ├─► Pydantic v2 Request Validation & Schema Serialization
   │
   ▼
Recommendation & Career Intelligence System
   │
   ├─► DataLoader (Singleton In-Memory Cache)
   │     ├── Career Catalogue (107 Accredited Qualifications)
   │     ├── TF-IDF Vectorizer
   │     └── Dense Semantic Embeddings
   │
   ├─► Eligibility Rules Engine (Admission, Duration, Budget, Location)
   │
   ├─► Hybrid Scoring & Ranking Pipeline
   │
   └─► Grounded Career Counsellor (Deterministic Knowledge-Base & Fallback)
```

---

## Project Structure

```text
kaushalsetu/
├── backend/
│   ├── __init__.py               # Python package initialization
│   ├── config.py                 # Application configuration, paths, and CORS settings
│   ├── counsellor.py             # Grounded conversational career guidance engine
│   ├── data_loader.py            # Singleton cached loader for catalogue and pre-trained models
│   ├── eligibility.py            # Multi-clause eligibility and prerequisite evaluator
│   ├── main.py                   # FastAPI application, static mounting, and route handlers
│   ├── recommendation_service.py # Hybrid scoring pipeline and explanation generator
│   ├── schemas.py                # Pydantic v2 data models for requests and responses
│   ├── youtube_service.py        # Video integration and cached journey metadata
│   └── tests/
│       ├── test_api.py           # Automated REST API unit tests
│       └── test_evaluation_suite.py # Automated recommendation scenario benchmarks
├── frontend/
│   ├── index.html                # Responsive web app user interface
│   ├── app.js                    # Frontend logic, state management, and relative API client
│   └── styles.css                # Polished design system and responsive styles
├── outputs/
│   ├── models/                   # Pre-computed TF-IDF vectorizer and dense embeddings
│   ├── recommendations/          # Processed career catalogue CSV (107 qualifications)
│   └── audit/                    # Benchmark evaluations and provenance reports
├── voice_model/
│   └── kaushalsetu_voice_chatbot.html # Standalone voice-enabled counsellor interface
├── career_referral_directory.csv # Career centre referral records
├── career_videos_cache.json      # Cached video metadata for qualifications
├── counseling_concerns_evidence.csv # Counselling evidence base
├── counseling_intake_profiles.csv   # Reference learner profiles
├── labour_market_household_context.csv # Macro-economic benchmarks
├── ncs_jobs.csv                  # NCS job vacancy evidence
├── placement_earnings.csv        # Placement benchmarks
├── qualifications.csv            # Accredited qualification registry
├── training_providers.csv        # SIDH training centre records
├── requirements.txt              # Production Python dependencies
├── run_kaushalsetu.bat           # 1-click Windows launcher
└── run_kaushalsetu.sh            # Linux / macOS launcher
```

---

## Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/etishasingh/kaushalsetu.git
cd kaushalsetu
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
# Windows / Linux / macOS
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Once started, navigate to:
- **Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check, catalogue verification, and data coverage stats |
| `POST` | `/api/recommendations` | Generate ranked vocational recommendations from learner profile |
| `GET` | `/api/careers` | Browse and filter accredited qualifications by NSQF level and sector |
| `GET` | `/api/careers/{id}` | Detailed facts, competencies, eligibility reasons, and evidence |
| `GET` | `/api/careers/{id}/videos` | Verified career-journey videos and training demonstrations |
| `POST` | `/api/counsellor/chat` | Grounded AI vocational counselling and trade comparison |
| `GET` | `/` | Serves the integrated web application |
| `GET` | `/voice` | Serves the standalone voice chatbot |
| `GET` | `/youtube-explorer` | Serves the career video explorer |

---

## Deployment (Render Web Service)

KaushalSetu is designed to run as a single unified **Web Service** on Render (Python 3.10+). The FastAPI backend serves both the web frontend and all REST endpoints from the same domain.

### Render Service Settings:
- **Environment:** `Python 3`
- **Build Command:**
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```

### Production API URL Handling:
In production, the frontend dynamically uses **relative API paths** (`/api/recommendations`, `/health`, etc.) resolving against the deployed website's current origin (`window.location.origin`). No hardcoded localhost or 127.0.0.1 URLs are called.

---

## Environment Variables

The application runs completely out-of-the-box without requiring any API keys. Optional configuration variables include:

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | Auto-set by Render | `8000` | Port on which the web server listens |
| `API_HOST` | No | `127.0.0.1` | Local bind host interface |
| `CORS_ORIGINS` | No | `""` | Comma-separated list of additional cross-origin domains |
| `GEMINI_API_KEY` | No | `""` | Optional Google Gemini API key for enhanced conversational rephrasing |
| `OPENAI_API_KEY` | No | `""` | Optional OpenAI API key for conversational rephrasing |
| `YOUTUBE_API_KEY` | No | `""` | Optional YouTube Data API v3 key (application includes pre-cached videos) |

*Note: If no generative API key is provided, the conversational counsellor automatically operates in its verified deterministic knowledge-base mode without hallucinations.*

---

## Troubleshooting

### "Failed to fetch" on Deployed Site
- **Cause:** Previous versions attempted to fetch `http://127.0.0.1:8000` from the client's browser, triggering mixed-content blocks and connection failures on HTTPS deployed domains.
- **Solution:** The frontend now defaults to relative paths (`""`), resolving directly against the current website origin. If you run a custom decoupled setup, supply the API endpoint via the `?api=` query parameter (e.g. `https://your-site.onrender.com/?api=https://your-api.onrender.com`).

### Port Already in Use
- **Error:** `[Errno 10048] address ('127.0.0.1', 8000) already in use`
- **Solution:** Another Uvicorn instance is running. Terminate it via PowerShell:
  ```powershell
  Get-Process -Name python | Stop-Process -Force
  ```

### Missing Model Artifacts
- Ensure `outputs/models/tfidf_vectorizer.joblib` and `outputs/models/dense_embeddings.npy` are present in your deployment. They are tracked in git and loaded automatically at startup.
