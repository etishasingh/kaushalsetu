# -*- coding: utf-8 -*-
"""KaushalSetu YouTube career-video integration.

The heavy recommendation logic remains in the standalone root module so the
original CLI/standalone explorer continues to work. This wrapper gives the
main FastAPI application a clean service boundary.
"""
from typing import Optional

from youtube_recommendation import YouTubeRecommendationEngine


_engine: Optional[YouTubeRecommendationEngine] = None


def get_youtube_engine() -> YouTubeRecommendationEngine:
    global _engine
    if _engine is None:
        _engine = YouTubeRecommendationEngine.get_instance()
    return _engine


def get_career_videos(
    *,
    career_id: str,
    career_title: str,
    job_role: Optional[str] = None,
    skills: Optional[str] = None,
    qualification_id: Optional[str] = None,
    language: str = "English",
    force_refresh: bool = False,
):
    result = get_youtube_engine().get_career_videos(
        career_id=career_id,
        career_title=career_title,
        job_role=job_role,
        skills=skills,
        qualification_id=qualification_id,
        language=language,
        force_refresh=force_refresh,
    )
    return result.to_dict()
