# -*- coding: utf-8 -*-
"""
FastAPI Application for KaushalSetu AI Recommendation Engine.
Exposes REST endpoints for health checks, career exploration, and personalized recommendations.
"""

import logging
from typing import Optional
from fastapi import FastAPI , HTTPException, Query, status
from fastapi.staticfiles import StaticFiles 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from backend.config import API_TITLE, API_VERSION, API_DESCRIPTION, ALLOWED_ORIGINS
from backend.data_loader import DataLoader
from backend.recommendation_service import RecommendationService
from backend.counsellor import CareerCounsellorService
from backend.youtube_service import get_career_videos
from backend.schemas import (
    LearnerProfileRequest,
    RecommendationResponse,
    RecommendationCard,
    CareerListResponse,
    CareerSummary,
    HealthResponse,
    CounsellorChatRequest,
    CounsellorChatResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kaushalsetu.api")

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Enable CORS for local and web frontends with explicit origins and localhost regex (avoiding wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Lazy service getters
service: Optional[RecommendationService] = None
counsellor_service: Optional[CareerCounsellorService] = None

def get_service() -> RecommendationService:
    """Returns singleton RecommendationService instance, initializing if needed."""
    global service
    if service is None:
        loader = DataLoader.get_instance()
        service = RecommendationService(data_loader=loader)
    return service

def get_counsellor_service() -> CareerCounsellorService:
    """Returns singleton CareerCounsellorService instance, initializing if needed."""
    global counsellor_service
    if counsellor_service is None:
        loader = DataLoader.get_instance()
        counsellor_service = CareerCounsellorService(data_loader=loader)
    return counsellor_service

@app.on_event("startup")
def startup_event():
    """Initializes data loader, recommendation service, and counsellor service at startup."""
    try:
        get_service()
        get_counsellor_service()
        logger.info("KaushalSetu Backend API started successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize services on startup: {e}")
        raise e

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Returns backend status, loaded catalogue count, and artifact verification stats."""
    try:
        loader = DataLoader.get_instance()
        stats = loader.get_health_stats()
        return HealthResponse(
            status=stats["status"],
            api_version=API_VERSION,
            catalogue_loaded=stats["catalogue_loaded"],
            total_qualifications=stats["total_qualifications"],
            vectorizer_loaded=stats["vectorizer_loaded"],
            dense_embeddings_loaded=stats["dense_embeddings_loaded"],
            linked_providers_count=stats["linked_providers_count"],
            missingness_rate_pct=stats["missingness_rate_pct"]
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation backend service is uninitialized or data files are missing."
        )

@app.get("/api/careers", response_model=CareerListResponse, tags=["Careers"])
def list_careers(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    nsqf_level: Optional[str] = Query(default=None, description="Filter by NSQF level (e.g. 'Level 4')"),
    sector: Optional[str] = Query(default=None, description="Filter by sector")
):
    """Browses all accredited qualifications in the career catalogue with optional filters."""
    srv = get_service()
    cat = srv.catalogue
    if nsqf_level:
        cat = cat[cat['nsqf_level'].str.lower() == nsqf_level.lower().strip()]
    if sector:
        cat = cat[cat['sector'].str.lower().str.contains(sector.lower().strip())]

    total_count = len(cat)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_rows = cat.iloc[start_idx:end_idx]

    items = []
    for _, row in page_rows.iterrows():
        items.append(CareerSummary(
            qualification_id=str(row['qualification_id']),
            qualification_title=str(row['qualification_title']),
            display_title=str(row.get('display_title', row['qualification_title'])),
            nsqf_level=str(row.get('nsqf_level', 'Unspecified')),
            sector=str(row.get('sector', 'Manufacturing')),
            awarding_body=str(row.get('awarding_body', 'NCVET')),
            duration_hours=str(row.get('duration_hours_raw', 'Unspecified')),
            has_provider_link=bool(row.get('has_provider_link', False)),
            source_nqr_url=str(row.get('source_nqr_url', 'https://nqr.gov.in'))
        ))

    return CareerListResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        items=items
    )

@app.get("/api/careers/{qualification_id:path}/videos", tags=["Career Videos"])
def get_career_videos_endpoint(
    qualification_id: str,
    language: str = Query(default="English", description="Video language preference"),
    category: Optional[str] = Query(default=None, description="Optional video category filter"),
    force_refresh: bool = Query(default=False, description="Refresh from YouTube Data API when configured"),
):
    """Returns cached/live career-journey videos associated with a qualification."""
    srv = get_service()
    card = srv.get_career_by_id(qualification_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Qualification ID '{qualification_id}' not found.")

    try:
        data = get_career_videos(
            career_id=card.qualification_id,
            career_title=card.qualification_title,
            job_role=card.job_role,
            skills=card.matched_skills_or_interests,
            qualification_id=card.qualification_id,
            language=language,
            force_refresh=force_refresh,
        )
        if category and data.get("categories"):
            wanted = data["categories"].get(category, [])
            data["categories"] = {category: wanted}
            data["total_videos"] = len(wanted)
        return data
    except Exception as e:
        logger.exception("YouTube career video lookup failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Career video service failed.") from e


@app.get("/api/careers/{qualification_id:path}", response_model=RecommendationCard, tags=["Careers"])
def get_career_details(qualification_id: str):
    """Retrieves detailed evidence, competencies, and provider data for one qualification."""
    srv = get_service()
    card = srv.get_career_by_id(qualification_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Qualification ID '{qualification_id}' not found in official catalogue."
        )
    return card

@app.post("/api/recommendations", response_model=RecommendationResponse, tags=["Recommendations"])
def get_recommendations(profile: LearnerProfileRequest):
    """
    Generates explainable vocational career recommendations based on declared learner preferences,
    evaluating multi-clause eligibility and preserving transparent missingness disclosures.
    """
    srv = get_service()
    try:
        response = srv.get_recommendations(profile)
        return response
    except Exception as e:
        logger.error(f"Error computing recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating personalized recommendations. Please verify profile parameters."
        )

@app.post("/api/counsellor/chat", response_model=CounsellorChatResponse, tags=["Counsellor"])
def chat_with_counsellor(request: CounsellorChatRequest):
    """
    Conversational vocational counselling endpoint grounded strictly in verified NCVET and SIDH datasets.
    Explains qualification requirements, compares trade options, discloses missing facts,
    and falls back safely without ungrounded generative hallucinations.
    """
    cs = get_counsellor_service()
    try:
        response = cs.chat(request)
        return response
    except Exception as e:
        logger.error(f"Error in counsellor chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating grounded career guidance. Please verify request parameters."
        )

@app.get("/", include_in_schema=False)
def serve_frontend():
    """Serves the integrated KaushalSetu frontend from the same FastAPI process."""
    return FileResponse(str((__import__('pathlib').Path(__file__).resolve().parent.parent / "frontend" / "index.html")))


@app.get("/voice", include_in_schema=False)
def serve_voice_tool():
    """Optional standalone voice compatibility page from the bundled voice package."""
    return FileResponse(str((__import__('pathlib').Path(__file__).resolve().parent.parent / "voice_model" / "kaushalsetu_voice_chatbot.html")))


@app.get("/youtube-explorer", include_in_schema=False)
def serve_youtube_explorer():
    """Serves the original standalone YouTube explorer for direct/manual browsing."""
    return FileResponse(str((__import__('pathlib').Path(__file__).resolve().parent.parent / "youtube_career_videos.html")))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
