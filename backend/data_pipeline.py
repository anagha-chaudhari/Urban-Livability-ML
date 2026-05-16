import os
import json
import numpy as np
import pandas as pd
import requests
import logging
import hashlib
import pathlib
import time
from dotenv import load_dotenv
from sklearn.cluster import KMeans

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEOAPIFY_API_KEY", "")

CACHE_DIR = pathlib.Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_SECONDS = 24 * 3600 

CITY_BBOXES = {
    "Pune": {
        "lat_min": 18.40, "lat_max": 18.65,
        "lon_min": 73.72, "lon_max": 74.05,
    },
    "Bangalore": {
        "lat_min": 12.83, "lat_max": 13.14,
        "lon_min": 77.46, "lon_max": 77.78,
    },
    "Mumbai": {
        "lat_min": 18.89, "lat_max": 19.27,
        "lon_min": 72.77, "lon_max": 72.99,
    },
}

AMENITY_CATEGORIES = {
    "food":      ["restaurant", "cafe", "fast_food"],
    "transit":   ["bus_station"],
    "health":    ["hospital", "clinic", "pharmacy"],
    "green":     ["park"],
    "education": ["college", "university", "school"],
    "finance":   ["bank", "atm"],
    "shopping":  ["supermarket", "convenience"],
}

GEOAPIFY_CATEGORY_MAP = {
    "restaurant":  "catering.restaurant",
    "cafe":        "catering.cafe",
    "fast_food":   "catering.fast_food",
    "bus_station": "public_transport",
    "hospital":    "healthcare.hospital",
    "clinic":      "healthcare.clinic",
    "pharmacy":    "healthcare.pharmacy",
    "park":        "leisure.park",
    "college":     "education.college",
    "university":  "education.university",
    "school":      "education.school",
    "bank":        "service.financial.bank",
    "atm":         "service.financial.atm",
    "supermarket": "commercial.supermarket",
    "convenience": "commercial.convenience",
}

# adding cache helper layer to avoid unnecessary api calls

def _cache_key(city: str) -> pathlib.Path:
    slug = hashlib.md5(city.lower().encode()).hexdigest()
    return CACHE_DIR / f"pois_{slug}.json"


def _load_cache(city: str) -> pd.DataFrame | None:
    path = _cache_key(city)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        age = time.time() - data.get("timestamp", 0)
        if age > CACHE_TTL_SECONDS:
            logger.info(f"Cache expired for '{city}' ({age/3600:.1f}h old)")
            return None
        df = pd.DataFrame(data["rows"])
        logger.info(f"Cache HIT for '{city}' — {len(df)} POIs loaded")
        return df
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None


def _save_cache(city: str, df: pd.DataFrame) -> None:
    path = _cache_key(city)
    try:
        payload = {
            "timestamp": time.time(),
            "city": city,
            "rows": df.to_dict(orient="records"),
        }
        path.write_text(json.dumps(payload))
        logger.info(f"Cache SAVED for '{city}' — {len(df)} POIs")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")

# fetch data

def fetch_raw_pois(city: str, amenity: str, bbox: dict) -> pd.DataFrame:
    geoapify_cat = GEOAPIFY_CATEGORY_MAP.get(amenity)
    if not geoapify_cat:
        return pd.DataFrame()

    bbox_str = (
        f"{bbox['lon_min']},{bbox['lat_min']},"
        f"{bbox['lon_max']},{bbox['lat_max']}"
    )
    url = (
        f"https://api.geoapify.com/v2/places"
        f"?categories={geoapify_cat}"
        f"&filter=rect:{bbox_str}"
        f"&limit=500"
        f"&apiKey={API_KEY}"
    )

    try:
        resp = requests.get(url, headers={"User-Agent": "CityPulse/2.0"}, timeout=30)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        logger.info(f"  Fetched {len(features):>4d} POIs  amenity='{amenity}'")

        rows = []
        for f in features:
            p = f.get("properties", {})
            rows.append({
                "osm_id":   p.get("place_id", ""),
                "name":     p.get("name"),
                "amenity":  amenity,
                "category": _amenity_to_category(amenity),
                "lat":      p.get("lat"),
                "lon":      p.get("lon"),
            })
        return pd.DataFrame(rows)

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout on amenity='{amenity}'")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error on amenity='{amenity}': {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error on amenity='{amenity}': {e}")
        return pd.DataFrame()


def _amenity_to_category(amenity: str) -> str:
    for cat, amenities in AMENITY_CATEGORIES.items():
        if amenity in amenities:
            return cat
    return "other"

# cleaning


def clean_pois(df: pd.DataFrame, bbox: dict) -> tuple[pd.DataFrame, dict]:
    report = {"initial_count": len(df), "steps": {}}

    before = len(df)
    df = df.dropna(subset=["lat", "lon"])
    report["steps"]["dropped_null_coords"] = before - len(df)

    before = len(df)
    df = df[df["osm_id"].astype(str).str.strip() != ""]
    df = df.drop_duplicates(subset=["osm_id"])
    report["steps"]["dropped_duplicate_osm_ids"] = before - len(df)

    before = len(df)
    df = df[
        df["lat"].between(bbox["lat_min"], bbox["lat_max"]) &
        df["lon"].between(bbox["lon_min"], bbox["lon_max"])
    ]
    report["steps"]["dropped_outside_bbox"] = before - len(df)

    null_names = df["name"].isnull().sum()
    df = df.copy()
    df["name"] = df["name"].fillna(df["amenity"].str.title() + " (Unnamed)")
    report["steps"]["filled_missing_names"] = int(null_names)

    df["lat"] = df["lat"].astype(float).round(6)
    df["lon"] = df["lon"].astype(float).round(6)
    df["osm_id"] = df["osm_id"].astype(str)

    report["final_count"] = len(df)
    report["retention_rate"] = (
        round(len(df) / report["initial_count"] * 100, 1)
        if report["initial_count"] > 0 else 0.0
    )

    logger.info(
        f"Cleaning: {report['initial_count']} → {report['final_count']} "
        f"({report['retention_rate']}% retained)"
    )
    return df.reset_index(drop=True), report

def fetch_all_pois(city: str = "Pune") -> tuple[pd.DataFrame, dict]:
    logger.info(f"=== POI fetch for '{city}' ===")

    if not API_KEY:
        raise EnvironmentError("GEOAPIFY_API_KEY is not set in your .env file.")

    bbox = CITY_BBOXES.get(city)
    if bbox is None:
        raise ValueError(f"City '{city}' not supported. Add its bbox to CITY_BBOXES.")

    # Check cache first
    cached = _load_cache(city)
    if cached is not None:
        report = {
            "initial_count": len(cached),
            "final_count": len(cached),
            "retention_rate": 100.0,
            "steps": {"source": "cache"},
            "cached": True,
        }
        return cached, report

    # Live fetch
    all_amenities = [a for group in AMENITY_CATEGORIES.values() for a in group]
    raw_dfs = []
    for amenity in all_amenities:
        df = fetch_raw_pois(city, amenity, bbox)
        if not df.empty:
            raw_dfs.append(df)

    if not raw_dfs:
        raise RuntimeError(
            "No POI data fetched. Check your GEOAPIFY_API_KEY, "
            "internet connection, or daily API limits."
        )

    combined = pd.concat(raw_dfs, ignore_index=True)
    clean_df, report = clean_pois(combined, bbox)
    report["cached"] = False

    if len(clean_df) >= 20:
        _save_cache(city, clean_df)

    return clean_df, report

# ml clustering layer

def derive_neighborhood_centers(
    pois_df: pd.DataFrame,
    n_zones: int = 12,
) -> pd.DataFrame:
    if len(pois_df) < n_zones:
        n_zones = max(3, len(pois_df) // 10)
        logger.warning(f"Reduced zones to {n_zones} due to sparse data")

    coords = pois_df[["lat", "lon"]].values
    km = KMeans(n_clusters=n_zones, random_state=42, n_init=10)
    pois_df = pois_df.copy()
    pois_df["geo_zone"] = km.fit_predict(coords)

    centers = (
        pois_df.groupby("geo_zone")
        .agg(lat=("lat", "mean"), lon=("lon", "mean"), poi_count=("osm_id", "count"))
        .reset_index()
    )

    dominant = (
        pois_df.groupby("geo_zone")["category"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
        .rename(columns={"category": "dominant_type"})
    )
    centers = centers.merge(dominant, on="geo_zone")
    centers["zone_id"] = centers.apply(
        lambda r: f"Zone {int(r['geo_zone']) + 1} ({r['dominant_type'].title()})",
        axis=1,
    )

    logger.info(f"Derived {n_zones} neighborhood zones from {len(pois_df)} POIs")
    return centers