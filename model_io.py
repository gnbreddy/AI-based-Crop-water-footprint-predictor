"""Safe persistence and batch-inference helpers for LightGBM/scikit-learn models.

The saved object may be a bare ``lgbm.LGBMRegressor`` or a scikit-learn
``Pipeline`` containing preprocessing and a LightGBM final step. Saving the
pipeline is preferred because it preserves the preprocessing used at training.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import joblib
import pandas as pd


def _infer_feature_names(model: Any) -> list[str]:
    """Return feature names from a fitted pipeline/model when available."""
    if hasattr(model, "feature_names_in_"):
        return [str(name) for name in model.feature_names_in_]
    if hasattr(model, "named_steps"):
        estimator = model.named_steps.get("lgbm")
        if estimator is not None and hasattr(estimator, "feature_name_"):
            return [str(name) for name in estimator.feature_name_]
    if hasattr(model, "feature_name_"):
        return [str(name) for name in model.feature_name_]
    return []


def save_lgbm_regressor(
    lgbm_regressor: Any,
    model_path: str | Path,
    *,
    feature_names: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Save a fitted model and adjacent JSON manifest.

    Load joblib artifacts only when they were created by a trusted source:
    joblib uses Python pickle internally.
    """
    path = Path(model_path)
    if path.suffix != ".pkl":
        raise ValueError("model_path must end in '.pkl'")
    path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(lgbm_regressor, path)
    manifest_path = path.with_suffix(".metadata.json")
    manifest = {
        "artifact_format": "joblib",
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_class": type(lgbm_regressor).__name__,
        "feature_names": list(feature_names) if feature_names is not None else _infer_feature_names(lgbm_regressor),
        "metadata": dict(metadata or {}),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"model_path": str(path), "metadata_path": str(manifest_path)}


def load_lgbm_regressor(model_path: str | Path) -> Any:
    """Load a trusted locally-created joblib model artifact."""
    return joblib.load(Path(model_path))


def load_model_metadata(model_path: str | Path) -> dict[str, Any]:
    """Load the optional metadata manifest created by ``save_lgbm_regressor``."""
    manifest_path = Path(model_path).with_suffix(".metadata.json")
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def predict_batch(lgbm_regressor: Any, records: pd.DataFrame | Iterable[Mapping[str, Any]]) -> list[float]:
    """Validate feature columns and make batch predictions in training order."""
    frame = records.copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
    feature_names = _infer_feature_names(lgbm_regressor)
    if feature_names:
        missing = [name for name in feature_names if name not in frame.columns]
        if missing:
            raise ValueError(f"Batch is missing required model features: {', '.join(missing)}")
        frame = frame.loc[:, feature_names]
    if frame.empty:
        return []
    return [float(value) for value in lgbm_regressor.predict(frame)]
