# pois, zones, scores, fetch_log

import sqlite3
import logging
import time
import json
from pathlib import Path
from contextlib import contextmanager

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = Path("urbanlivability.db")
CACHE_TTL_SECONDS = 24 * 3600 

@contextmanager
def get_connection():
    """Context manager: auto-commits on success, rolls back on error."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   
    conn.execute("PRAGMA journal_mode=WAL") 
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

CREATE_POIS = """
CREATE TABLE IF NOT EXISTS pois (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id TEXT NOT NULL,
    city TEXT NOT NULL,
    name TEXT,
    amenity TEXT NOT NULL,
    category TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    fetched_at INTEGER NOT NULL,
    UNIQUE(place_id, city)
);
"""

CREATE_ZONES = """
CREATE TABLE IF NOT EXISTS zones (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    city         TEXT    NOT NULL,
    n_zones      INTEGER NOT NULL,
    zone_idx     INTEGER NOT NULL,
    zone_id      TEXT    NOT NULL,
    lat          REAL    NOT NULL,
    lon          REAL    NOT NULL,
    poi_count    INTEGER NOT NULL,
    dominant_type TEXT   NOT NULL,
    created_at   INTEGER NOT NULL,
    UNIQUE(city, n_zones, zone_idx)
);
"""

CREATE_SCORES = """
CREATE TABLE IF NOT EXISTS scores (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    city           TEXT    NOT NULL,
    n_zones        INTEGER NOT NULL,
    weights_hash   TEXT    NOT NULL,
    zone_id        TEXT    NOT NULL,
    lat            REAL    NOT NULL,
    lon            REAL    NOT NULL,
    total_score    REAL    NOT NULL,
    food_count     INTEGER NOT NULL DEFAULT 0,
    transit_count  INTEGER NOT NULL DEFAULT 0,
    health_count   INTEGER NOT NULL DEFAULT 0,
    green_count    INTEGER NOT NULL DEFAULT 0,
    education_count INTEGER NOT NULL DEFAULT 0,
    finance_count  INTEGER NOT NULL DEFAULT 0,
    shopping_count INTEGER NOT NULL DEFAULT 0,
    tier           TEXT,
    rank_num       INTEGER,
    pca_x          REAL,
    pca_y          REAL,
    created_at     INTEGER NOT NULL,
    UNIQUE(city, n_zones, weights_hash, zone_id)
);
"""

CREATE_FETCH_LOG = """
CREATE TABLE IF NOT EXISTS fetch_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    city        TEXT    NOT NULL,
    amenity     TEXT    NOT NULL,
    poi_count   INTEGER NOT NULL,
    api_source  TEXT    NOT NULL DEFAULT 'geoapify',
    fetched_at  INTEGER NOT NULL
);
"""

# Performance indexes 

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_pois_city_category ON pois(city, category);",
    "CREATE INDEX IF NOT EXISTS idx_pois_city_fetched  ON pois(city, fetched_at);",
    "CREATE INDEX IF NOT EXISTS idx_zones_city         ON zones(city, n_zones);",
    "CREATE INDEX IF NOT EXISTS idx_scores_city        ON scores(city, n_zones, weights_hash);",
]

# Create tables and indexes if they donot exist

def init_db() -> None:
    """Create tables and indexes. Safe to call multiple times (IF NOT EXISTS)."""
    with get_connection() as conn:
        conn.execute(CREATE_POIS)
        conn.execute(CREATE_ZONES)
        conn.execute(CREATE_SCORES)
        conn.execute(CREATE_FETCH_LOG)
        for idx_sql in CREATE_INDEXES:
            conn.execute(idx_sql)
    logger.info(f"Database initialized at {DB_PATH.resolve()}")


def pois_are_fresh(city: str) -> bool:
    """True if we have POI data for this city fetched within the TTL."""
    cutoff = int(time.time()) - CACHE_TTL_SECONDS
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM pois WHERE city = ? AND fetched_at > ?",
            (city, cutoff)
        ).fetchone()
    fresh = row["cnt"] > 0
    if fresh:
        logger.info(f"DB cache HIT for '{city}' — {row['cnt']} fresh POIs")
    return fresh


def load_pois_from_db(city: str) -> pd.DataFrame:
    """Load all POIs for a city from SQLite."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT place_id AS osm_id, name, amenity, category, lat, lon
            FROM pois
            WHERE city = ?
            ORDER BY category, lat
            """,
            (city,)
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    logger.info(f"Loaded {len(df)} POIs for '{city}' from database")
    return df


def save_pois_to_db(city: str, df: pd.DataFrame) -> None:
    """
    Upsert POIs into the database.
    UNIQUE(place_id, city) means re-fetching the same POI is idempotent.
    """
    now = int(time.time())
    rows = [
        (
            str(row.get("osm_id", "")),
            city,
            row.get("name"),
            row.get("amenity", ""),
            row.get("category", ""),
            float(row["lat"]),
            float(row["lon"]),
            now,
        )
        for _, row in df.iterrows()
    ]
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO pois
                (place_id, city, name, amenity, category, lat, lon, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    logger.info(f"Saved {len(rows)} POIs for '{city}' to database")


def log_fetch(city: str, amenity: str, count: int, source: str = "geoapify") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO fetch_log (city, amenity, poi_count, api_source, fetched_at) VALUES (?,?,?,?,?)",
            (city, amenity, count, source, int(time.time()))
        )


# Scores persistence 

# deterministic hash of weight dict so different weights get different cached results

def make_weights_hash(weights: dict) -> str:
    canonical = json.dumps(weights, sort_keys=True)
    import hashlib
    return hashlib.md5(canonical.encode()).hexdigest()[:8]


def scores_are_cached(city: str, n_zones: int, weights: dict) -> bool:
    wh = make_weights_hash(weights)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM scores WHERE city=? AND n_zones=? AND weights_hash=?",
            (city, n_zones, wh)
        ).fetchone()
    return row["cnt"] > 0


def load_scores_from_db(city: str, n_zones: int, weights: dict) -> pd.DataFrame:
    wh = make_weights_hash(weights)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT zone_id, lat, lon, total_score, poi_count,
                   food_count, transit_count, health_count, green_count,
                   education_count, finance_count, shopping_count,
                   tier, rank_num AS rank, pca_x, pca_y
            FROM scores
            WHERE city=? AND n_zones=? AND weights_hash=?
            ORDER BY rank_num
            """,
            (city, n_zones, wh)
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def save_scores_to_db(city: str, n_zones: int, weights: dict, df: pd.DataFrame) -> None:
    wh = make_weights_hash(weights)
    now = int(time.time())
    rows = []
    for _, r in df.iterrows():
        rows.append((
            city, n_zones, wh,
            r.get("zone_id", ""), float(r.get("lat", 0)), float(r.get("lon", 0)),
            float(r.get("total_score", 0)),
            int(r.get("food_count", 0)), int(r.get("transit_count", 0)),
            int(r.get("health_count", 0)), int(r.get("green_count", 0)),
            int(r.get("education_count", 0)), int(r.get("finance_count", 0)),
            int(r.get("shopping_count", 0)),
            r.get("tier"), r.get("rank"),
            r.get("pca_x"), r.get("pca_y"),
            now,
        ))
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO scores
            (city, n_zones, weights_hash, zone_id, lat, lon, total_score,
             food_count, transit_count, health_count, green_count,
             education_count, finance_count, shopping_count,
             tier, rank_num, pca_x, pca_y, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
    logger.info(f"Saved {len(rows)} scored zones for '{city}' to database")


# Analytics queries

# return stats about what's in the database, useful for the pipeline tab in Streamlit
def get_db_stats() -> dict:
    with get_connection() as conn:
        total_pois = conn.execute("SELECT COUNT(*) FROM pois").fetchone()[0]
        cities = conn.execute(
            "SELECT city, COUNT(*) as cnt FROM pois GROUP BY city"
        ).fetchall()
        fetch_calls = conn.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0]
        cached_scores = conn.execute("SELECT COUNT(DISTINCT city||n_zones||weights_hash) FROM scores").fetchone()[0]
    return {
        "total_pois_stored": total_pois,
        "pois_by_city": {r["city"]: r["cnt"] for r in cities},
        "total_api_calls_logged": fetch_calls,
        "cached_score_configs": cached_scores,
    }

# remove all data for a city (useful for dev resets)

def clear_city(city: str) -> dict:
    with get_connection() as conn:
        pois_del = conn.execute("DELETE FROM pois WHERE city=?", (city,)).rowcount
        zones_del = conn.execute("DELETE FROM zones WHERE city=?", (city,)).rowcount
        scores_del = conn.execute("DELETE FROM scores WHERE city=?", (city,)).rowcount
    return {"pois_deleted": pois_del, "zones_deleted": zones_del, "scores_deleted": scores_del}