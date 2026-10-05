# -*- coding: utf-8 -*-
"""
Safe Data and Artifact Loader for KaushalSetu Backend.
Loads catalogue, TF-IDF vectorizer, and dense semantic embeddings with strict validation.
Caches artifacts in memory to prevent reloading overhead on every request.
"""

import os
import re
import ast
import joblib
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional

from backend.config import (
    CAREER_CATALOGUE_CSV,
    TFIDF_VECTORIZER_PKL,
    DENSE_EMBEDDINGS_NPY,
    QUALIFICATIONS_CSV,
    TRAINING_PROVIDERS_CSV,
    NCS_JOBS_CSV,
    PLACEMENT_EARNINGS_CSV
)

logger = logging.getLogger("kaushalsetu.data_loader")

class DataLoader:
    """Manages cached access to career catalogue and pre-trained models."""
    _instance = None
    _catalogue_df: Optional[pd.DataFrame] = None
    _vectorizer = None
    _dense_embeddings: Optional[np.ndarray] = None
    _is_initialized: bool = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        """Loads and validates all assets on startup."""
        if self._is_initialized:
            return

        logger.info("Initializing KaushalSetu DataLoader...")
        
        # 1. Load or verify career catalogue
        if not CAREER_CATALOGUE_CSV.exists():
            raise FileNotFoundError(f"Career catalogue not found at {CAREER_CATALOGUE_CSV}. Build it before running backend.")

        df = pd.read_csv(CAREER_CATALOGUE_CSV)
        
        # Parse list fields if stored as string representations
        if 'provider_district_list' in df.columns:
            def safe_eval_list(val):
                if isinstance(val, list):
                    return val
                if pd.isna(val) or not str(val).strip():
                    return []
                try:
                    return ast.literal_eval(str(val))
                except:
                    return [x.strip() for x in str(val).split(',') if x.strip()]
            df['provider_district_list'] = df['provider_district_list'].apply(safe_eval_list)
            df['provider_state_list'] = df['provider_state_list'].apply(safe_eval_list)

        # Generate unambiguous display titles for duplicated names
        display_titles = []
        for _, row in df.iterrows():
            title = str(row['qualification_title'])
            nsqf = str(row.get('nsqf_level', ''))
            body = str(row.get('awarding_body', ''))
            qid = str(row.get('qualification_id', ''))
            short_body = body.split('(')[-1].replace(')', '').strip() if '(' in body else body[:15]
            # Use year from ID or verified date
            year_match = re.search(r'202[0-9]', qid)
            year_tag = year_match.group(0) if year_match else "NQR"
            display_titles.append(f"{title} ({nsqf} • {short_body} • {year_tag})")
        df['display_title'] = display_titles

        self._catalogue_df = df
        logger.info(f"Loaded career catalogue: {len(df)} qualifications.")

        # 2. Load and validate TF-IDF Vectorizer
        if not TFIDF_VECTORIZER_PKL.exists():
            raise FileNotFoundError(f"TF-IDF vectorizer artifact missing at {TFIDF_VECTORIZER_PKL}.")
        self._vectorizer = joblib.load(TFIDF_VECTORIZER_PKL)
        logger.info(f"Loaded TF-IDF vectorizer (Vocab size: {len(self._vectorizer.vocabulary_)}).")

        # 3. Load and validate Dense Semantic Embeddings
        if not DENSE_EMBEDDINGS_NPY.exists():
            raise FileNotFoundError(f"Dense embeddings artifact missing at {DENSE_EMBEDDINGS_NPY}.")
        embeddings = np.load(DENSE_EMBEDDINGS_NPY)
        
        # Verify alignment: rows must match catalogue size
        if embeddings.shape[0] != len(df):
            raise ValueError(f"Dense embeddings shape mismatch: {embeddings.shape[0]} vectors vs {len(df)} catalogue records.")
        self._dense_embeddings = embeddings
        logger.info(f"Loaded dense semantic embeddings (Shape: {embeddings.shape}).")

        self._is_initialized = True
        logger.info("DataLoader initialization complete.")

    @property
    def catalogue(self) -> pd.DataFrame:
        if self._catalogue_df is None:
            self.initialize()
        return self._catalogue_df

    @property
    def vectorizer(self):
        if self._vectorizer is None:
            self.initialize()
        return self._vectorizer

    @property
    def dense_embeddings(self) -> np.ndarray:
        if self._dense_embeddings is None:
            self.initialize()
        return self._dense_embeddings

    def get_health_stats(self) -> Dict[str, Any]:
        """Returns artifact status and data coverage metrics."""
        cat = self.catalogue
        linked_count = int(cat['has_provider_link'].sum()) if 'has_provider_link' in cat.columns else 0
        total_count = len(cat)
        missingness_pct = round(((total_count - linked_count) / total_count) * 100, 2) if total_count > 0 else 0.0

        return {
            "status": "healthy" if self._is_initialized else "uninitialized",
            "catalogue_loaded": self._catalogue_df is not None,
            "total_qualifications": total_count,
            "vectorizer_loaded": self._vectorizer is not None,
            "dense_embeddings_loaded": self._dense_embeddings is not None,
            "linked_providers_count": linked_count,
            "missingness_rate_pct": missingness_pct
        }
