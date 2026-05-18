import logging
import pathlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
#from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from data_pipeline import (
    fetch_all_pois,
    derive_neighborhood_centers,
    AMENITY_CATEGORIES
)

from scorer import score_all_zones, DEFAULT_WEIGHTS, PERSONA_WEIGHTS
from ml import run_clustering

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Cityello API",
    description="Neighborhood livability analytics — geospatial ML pipeline",
    version="2.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    # "https://your-app.streamlit.app",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

SUPPORTED_CITIES = list({"Pune", "Bangalore", "Mumbai"})


class ScoreRequest(BaseModel):
    city: str = Field(default="Pune", description="Target city")
    weights: Optional[dict] = Field(default=None, description="Category weights (0–5)")
    n_zones: int = Field(default=12, ge=4, le=20, description="Number of zones")

    @field_validator("city")
    @classmethod
    def validate_city(cls, v):
        city = v.strip().title()
        if city not in SUPPORTED_CITIES:
            raise ValueError(f"Unsupported city. Supported: {SUPPORTED_CITIES}")
        return city

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v):
        if v is None:
            return v
        valid_keys = set(DEFAULT_WEIGHTS.keys())
        for k, val in v.items():
            if k not in valid_keys:
                raise ValueError(f"Invalid category: '{k}'. Valid: {valid_keys}")
            if not isinstance(val, (int, float)) or not (0 <= val <= 5):
                raise ValueError(f"Weight for '{k}' must be a number between 0 and 5")
        if sum(v.values()) == 0:
            raise ValueError("At least one weight must be greater than 0")
        return v

# Endpoints

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CityPulse API", "version": "2.1.0"}


@app.get("/metadata")
def metadata():
    return {
        "supported_cities": SUPPORTED_CITIES,
        "categories": list(AMENITY_CATEGORIES.keys()),
        "default_weights": DEFAULT_WEIGHTS,
        "persona_presets": PERSONA_WEIGHTS,
    }


@app.get("/db/stats")
def db_stats():
    from database import get_db_stats
    return get_db_stats()

@app.delete("/db/clear/{city}")
def clear_city_data(city: str):
    from database import clear_city as db_clear_city
    city = city.strip().title()
    if city not in SUPPORTED_CITIES:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")
    return {"city": city, "deleted": db_clear_city(city)}


@app.post("/score")
@limiter.limit("10/minute")
def score_neighborhoods(request: Request, body: ScoreRequest):
    logger.info(f"Score request | city={body.city} | zones={body.n_zones}")

    weights = body.weights or DEFAULT_WEIGHTS

    # Fetch & clean POIs

    try:
        pois_df, cleaning_report = fetch_all_pois(body.city)
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in fetch_all_pois: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error fetching POI data.")

    if pois_df.empty:
        raise HTTPException(
            status_code=503,
            detail="No POI data returned. Check API key and network.",
        )
    if len(pois_df) < 50:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Only {len(pois_df)} POIs found for {body.city}. "
                "Dataset too sparse for meaningful clustering. "
                "Try a different city or check your API quota."
            ),
        )

    # Derive geographic zones

    try:
        zones_df = derive_neighborhood_centers(pois_df, n_zones=body.n_zones)
    except Exception as e:
        logger.error(f"Zone derivation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to derive neighborhood zones.")

    # Weighted feature engineering

    try:
        scored_df = score_all_zones(zones_df, pois_df, weights)
    except Exception as e:
        logger.error(f"Scoring failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to score neighborhoods.")

    # ML clustering
    
    try:
        results = run_clustering(scored_df)
    except Exception as e:
        logger.error(f"Clustering failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="ML clustering step failed.")

    return {
        "city": body.city,
        "weights_used": weights,
        "confidence": results.get("confidence", "unknown"),
        "confidence_warning": results.get("confidence_warning"),
        "data_summary": {
            "total_pois_fetched":       cleaning_report.get("initial_count", 0),
            "total_pois_after_cleaning": cleaning_report.get("final_count", 0),
            "retention_rate_pct":       cleaning_report.get("retention_rate", 0),
            "cleaning_steps":           cleaning_report.get("steps", {}),
            "n_zones_scored":           len(scored_df),
            "served_from_cache":        cleaning_report.get("cached", False),
        },
        "neighborhoods":  results["neighborhoods"],
        "ml_evaluation":  results["ml_evaluation"],
    }