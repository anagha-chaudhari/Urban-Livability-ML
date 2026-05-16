# receive the scored neighboorhood data
# validate data quality
# build a feature matrix
# normalize features
# determine optimal number of clusters
# train kmeans clustering
# evaluate cluster quality
# labels tier labels
# reduce dimensions using PCA
# return the interpreation and ML results

import logging
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "food_count", "transit_count", "health_count", "green_count",
    "education_count", "finance_count", "shopping_count",
]

TIER_LABELS = {
    2: ["Budget Friendly", "Premium"],
    3: ["Budget Friendly", "Balanced", "Premium"],
    4: ["Budget Friendly", "Economy", "Balanced", "Premium"],
    5: ["Budget Friendly", "Economy", "Balanced", "Good", "Premium"],
}


def _find_optimal_k(X: np.ndarray, k_range: range) -> dict:
    inertias, sil_scores, db_scores = [], [], []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)

        # silhouette requires at least 2 distinct labels

        unique_labels = len(set(labels))
        if unique_labels < 2:
            sil_scores.append(-1.0)
            db_scores.append(999.0)
        else:
            sil_scores.append(round(float(silhouette_score(X, labels)), 4))
            db_scores.append(round(float(davies_bouldin_score(X, labels)), 4))

        inertias.append(round(float(km.inertia_), 2))

    best_idx = sil_scores.index(max(sil_scores))
    optimal_k = list(k_range)[best_idx]

    logger.info(
        f"K selection: optimal K={optimal_k}, "
        f"best silhouette={sil_scores[best_idx]:.4f}"
    )
    return {
        "k_range": list(k_range),
        "inertias": inertias,
        "silhouette_scores": sil_scores,
        "db_scores": db_scores,
        "optimal_k": optimal_k,
        "best_silhouette": sil_scores[best_idx],
    }


def _confidence_label(silhouette: float) -> str:
    if silhouette >= 0.5:
        return "high"
    if silhouette >= 0.25:
        return "moderate"
    return "low"


def _interpret_silhouette(score: float) -> str:
    if score >= 0.7:
        return "Strong — clusters are well-separated"
    if score >= 0.5:
        return "Reasonable — clusters are meaningful"
    if score >= 0.25:
        return "Weak — some overlap between clusters"
    return "Poor — clusters are not well-defined"


def run_clustering(scored_df: pd.DataFrame) -> dict:
    if len(scored_df) < 4:
        logger.warning("Too few neighborhoods to cluster meaningfully")
        scored_df = scored_df.copy()
        scored_df["tier"] = "Unclustered"
        scored_df["rank"] = range(1, len(scored_df) + 1)
        scored_df["pca_x"] = 0.0
        scored_df["pca_y"] = 0.0
        return {
            "neighborhoods": scored_df.to_dict(orient="records"),
            "ml_evaluation": {},
            "confidence": "low",
            "confidence_warning": "Too few neighborhoods for reliable clustering.",
        }

    # 1. Feature matrix

    X_raw = scored_df[FEATURE_COLS].fillna(0).values

    # if all rows are identical, clustering is meaningless

    if np.std(X_raw) < 1e-6:
        logger.warning("Feature variance is near-zero — all zones look the same")
        scored_df = scored_df.copy()
        scored_df["tier"] = "Uniform"
        scored_df["rank"] = range(1, len(scored_df) + 1)
        scored_df["pca_x"] = 0.0
        scored_df["pca_y"] = 0.0
        return {
            "neighborhoods": scored_df.to_dict(orient="records"),
            "ml_evaluation": {},
            "confidence": "low",
            "confidence_warning": (
                "All neighborhoods have nearly identical scores. "
                "The dataset may be too sparse to differentiate zones."
            ),
        }

    scaler = MinMaxScaler()
    X = scaler.fit_transform(X_raw)

    # 2. Find optimal K

    max_k = min(6, len(scored_df) - 1)
    k_range = range(2, max_k + 1)
    k_analysis = _find_optimal_k(X, k_range)
    optimal_k = k_analysis["optimal_k"]

    # 3. Final KMeans

    km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    scored_df = scored_df.copy()
    scored_df["cluster"] = km.fit_predict(X)

    # 4. Evaluate

    final_silhouette = float(silhouette_score(X, scored_df["cluster"]))
    final_db = float(davies_bouldin_score(X, scored_df["cluster"]))

    logger.info(
        f"Clustering done | K={optimal_k} | "
        f"Silhouette={final_silhouette:.4f} | DB={final_db:.4f}"
    )

    # 5. Assign tier labels 

    cluster_means = (
        scored_df.groupby("cluster")["total_score"].mean().sort_values()
    )
    tier_names = TIER_LABELS.get(
        optimal_k,
        [f"Tier {i+1}" for i in range(optimal_k)],
    )
    label_map = {int(idx): tier_names[i] for i, idx in enumerate(cluster_means.index)}
    scored_df["tier"] = scored_df["cluster"].map(label_map)
    scored_df["rank"] = scored_df["total_score"].rank(ascending=False).astype(int)

    # 6. PCA for visualization
    
    n_components = min(2, X.shape[1], X.shape[0])
    pca = PCA(n_components=n_components, random_state=42)
    pca_coords = pca.fit_transform(X)
    scored_df["pca_x"] = pca_coords[:, 0].round(4)
    scored_df["pca_y"] = (pca_coords[:, 1].round(4) if n_components > 1 else 0.0)
    variance_explained = [round(float(v), 4) for v in pca.explained_variance_ratio_]

    confidence = _confidence_label(final_silhouette)
    confidence_warning = None
    if confidence == "low":
        confidence_warning = (
            "Clustering confidence is low (silhouette < 0.25). "
            "Neighborhoods may not be clearly differentiated — "
            "try increasing the number of zones or switching cities."
        )
    elif confidence == "moderate":
        confidence_warning = (
            "Clustering confidence is moderate. Results are directionally "
            "useful but treat tier boundaries as approximate."
        )

    return {
        "neighborhoods": scored_df.sort_values("rank").to_dict(orient="records"),
        "confidence": confidence,
        "confidence_warning": confidence_warning,
        "ml_evaluation": {
            "optimal_k": optimal_k,
            "final_silhouette": round(final_silhouette, 4),
            "final_davies_bouldin": round(final_db, 4),
            "silhouette_interpretation": _interpret_silhouette(final_silhouette),
            "k_selection_analysis": k_analysis,
            "pca_variance_explained": variance_explained,
            "features_used": FEATURE_COLS,
            "total_variance_explained": round(sum(variance_explained) * 100, 1),
            "n_neighborhoods_clustered": len(scored_df),
            "confidence": confidence,
        },
    }