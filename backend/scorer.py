import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_RADIUS_KM = 2.0
POI_CAP = 10

DEFAULT_WEIGHTS = {
    "food": 3, "transit": 3, "health": 2,
    "green": 2, "education": 2, "finance": 1, "shopping": 2,
}

PERSONA_WEIGHTS = {
    "Student": {
        "food": 3, "transit": 5, "health": 1,
        "green": 1, "education": 5, "finance": 2, "shopping": 2,
    },
    "Working Professional": {
        "food": 4, "transit": 4, "health": 2,
        "green": 2, "education": 1, "finance": 3, "shopping": 3,
    },
    "Family": {
        "food": 3, "transit": 3, "health": 5,
        "green": 4, "education": 4, "finance": 2, "shopping": 3,
    },
}

CATEGORY_KEYS = list(DEFAULT_WEIGHTS.keys())

# Vectorized haversine distance calculation 

def haversine_vectorized(
    center_lat: float,
    center_lon: float,
    lats: np.ndarray,
    lons: np.ndarray,) -> np.ndarray:
    R = 6371.0
    clat = np.radians(center_lat)
    clon = np.radians(center_lon)
    alat = np.radians(lats)
    alon = np.radians(lons)

    dlat = alat - clat
    dlon = alon - clon

    a = np.sin(dlat / 2) ** 2 + np.cos(clat) * np.cos(alat) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def count_nearby(
    center_lat: float,
    center_lon: float,
    pois_df: pd.DataFrame,
    category: str,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> int:
    subset = pois_df[pois_df["category"] == category]
    if subset.empty:
        return 0
    distances = haversine_vectorized(
        center_lat, center_lon,
        subset["lat"].to_numpy(),
        subset["lon"].to_numpy(),
    )
    return int((distances <= radius_km).sum())


# zone scoring

def score_zone(
    zone: pd.Series,
    pois_df: pd.DataFrame,
    weights: dict,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> dict:
    lat, lon = float(zone["lat"]), float(zone["lon"])

    category_counts = {
        cat: count_nearby(lat, lon, pois_df, cat, radius_km)
        for cat in CATEGORY_KEYS
    }

    clean_weights = {cat: weights.get(cat, 1) for cat in CATEGORY_KEYS}

    if sum(clean_weights.values()) == 0:
        clean_weights = DEFAULT_WEIGHTS.copy()
        logger.warning("All-zero weights detected — falling back to defaults")

    area_km2 = max(float(zone.get("zone_area_km2", 1.0)), 0.1)
    density_counts = {
        cat: round(category_counts[cat] / area_km2, 3)
        for cat in CATEGORY_KEYS
    }

    total = sum(
        min(density_counts[cat], POI_CAP) * clean_weights[cat]
        for cat in CATEGORY_KEYS
    )

    return {
        "zone_id": zone.get("zone_id", f"Zone_{zone.name}"),
        "zone_area_km2": round(area_km2, 2),
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "total_score": round(float(total), 2),
        "poi_count": int(zone.get("poi_count", 0)),
        "food_count": category_counts["food"],
        "transit_count": category_counts["transit"],
        "health_count": category_counts["health"],
        "green_count": category_counts["green"],
        "education_count": category_counts["education"],
        "finance_count": category_counts["finance"],
        "shopping_count": category_counts["shopping"],
        "food_density": density_counts["food"],
        "transit_density": density_counts["transit"],
        "health_density": density_counts["health"],
        "green_density": density_counts["green"],
        "education_density": density_counts["education"],
        "finance_density": density_counts["finance"],
        "shopping_density": density_counts["shopping"],
    }


def score_all_zones(
    zones_df: pd.DataFrame,
    pois_df: pd.DataFrame,
    weights: dict = DEFAULT_WEIGHTS,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> pd.DataFrame:
    logger.info(f"Scoring {len(zones_df)} zones using {len(pois_df)} POIs")

    results = [
        score_zone(zone, pois_df, weights, radius_km)
        for _, zone in zones_df.iterrows()
    ]

    df = pd.DataFrame(results).fillna(0)
    logger.info(
        f"Scoring complete | Score range: "
        f"{df['total_score'].min():.1f} → {df['total_score'].max():.1f}"
    )
    return df