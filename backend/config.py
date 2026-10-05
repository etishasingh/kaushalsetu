# -*- coding: utf-8 -*-
"""
Configuration settings for KaushalSetu Backend Service.
Loads paths, model artifacts, default scoring weights, and environment variables.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR
OUTPUTS_DIR = BASE_DIR / "outputs"
MODELS_DIR = OUTPUTS_DIR / "models"
RECOMMENDATIONS_DIR = OUTPUTS_DIR / "recommendations"
AUDIT_DIR = OUTPUTS_DIR / "audit"

# Dataset Files
QUALIFICATIONS_CSV = DATA_DIR / "qualifications.csv"
TRAINING_PROVIDERS_CSV = DATA_DIR / "training_providers.csv"
NCS_JOBS_CSV = DATA_DIR / "ncs_jobs.csv"
PLACEMENT_EARNINGS_CSV = DATA_DIR / "placement_earnings.csv"
CAREER_REFERRAL_CSV = DATA_DIR / "career_referral_directory.csv"
COUNSELING_PROFILES_CSV = DATA_DIR / "counseling_intake_profiles.csv"
COUNSELING_CONCERNS_CSV = DATA_DIR / "counseling_concerns_evidence.csv"
LABOUR_MARKET_CSV = DATA_DIR / "labour_market_household_context.csv"

# Pre-built Artifacts
CAREER_CATALOGUE_CSV = RECOMMENDATIONS_DIR / "career_catalogue.csv"
TFIDF_VECTORIZER_PKL = MODELS_DIR / "tfidf_vectorizer.joblib"
DENSE_EMBEDDINGS_NPY = MODELS_DIR / "dense_embeddings.npy"

# Scoring Weights
DEFAULT_WEIGHTS = {
    "text_relevance": 0.40,
    "skills_overlap": 0.25,
    "preference_match": 0.15,
    "eligibility_score": 0.10,
    "evidence_completeness": 0.10
}

# API Settings
API_TITLE = "KaushalSetu AI Recommendation Service"
API_VERSION = "2.0.0"
API_DESCRIPTION = "Explainable vocational-career recommendation and evidence retrieval API for learners and families."
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# CORS Settings
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "")
ALLOWED_ORIGINS = [
    origin.strip() for origin in CORS_ORIGINS_ENV.split(",") if origin.strip()
] or [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "null"
]

# Educational Hierarchy
EDUCATION_LEVELS = {
    'none': 0,
    'literate': 1,
    'ability to read and write': 1,
    '5th': 2,
    '8th': 3,
    '10th': 4,
    '11th': 5,
    '12th': 6,
    'iti': 6,
    'diploma': 7,
    'ug': 8,
    'graduate': 8,
    'b.tech': 9,
    'b.e.': 9,
    'post graduate': 10
}
