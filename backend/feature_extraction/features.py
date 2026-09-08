"""Explainable spectral feature extraction and prototype change detection."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from PIL import Image


CLASS_NAMES = {
    0: "Other",
    1: "Vegetation",
    2: "Water",
    3: "Built-up / bare",
}


def _safe_index(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = a + b
    return np.divide(a - b, denom, out=np.zeros_like(a, dtype=np.float32), where=np.abs(denom) > 1e-6)


def classify_scene(path: str) -> dict[str, Any]:
    """Classify a 4-band Sentinel-2 scene using explainable spectral rules.

    Expected band order for the MVP is B02, B03, B04, B08 (blue, green, red, NIR).
    The built-up class is intentionally a broad built-up/bare-ground heuristic because
    SWIR is not available in the four-band MVP input, so this is not a building detector.
    """
    with rasterio.open(path) as src:
        if src.count < 4:
            raise ValueError("Feature extraction requires at least 4 bands (B02, B03, B04, B08).")
        data = src.read([1, 2, 3, 4]).astype(np.float32)
        transform = src.transform
        crs = str(src.crs) if src.crs else None

    blue, green, red, nir = data
    valid = np.isfinite(data).all(axis=0) & (np.nanmax(data, axis=0) > 0)
    ndvi = _safe_index(nir, red)
    ndwi = _safe_index(green, nir)
    brightness = (blue + green + red) / 3.0

    # Adaptive brightness threshold. This is deliberately broad because B11/B12 SWIR
    # are absent from the MVP four-band upload and therefore a true built-up index
    # such as NDBI cannot be computed.
    valid_brightness = brightness[valid]
    brightness_threshold = float(np.percentile(valid_brightness, 70)) if valid_brightness.size else 0.0

    classes = np.zeros(ndvi.shape, dtype=np.uint8)
    vegetation = valid & (ndvi >= 0.25) & (ndvi > ndwi)
    water = valid & (ndwi >= 0.10) & (ndwi > ndvi)
    built = valid & ~vegetation & ~water & (brightness >= brightness_threshold)
    classes[vegetation] = 1
    classes[water] = 2
    classes[built] = 3

    stats: dict[str, dict[str, float | int]] = {}
    valid_count = int(valid.sum())
    for class_id, name in CLASS_NAMES.items():
        if class_id == 0:
            mask = valid & (classes == 0)
        else:
            mask = classes == class_id
        count = int(mask.sum())
        stats[name] = {
            "pixels": count,
            "percent": round((count / valid_count * 100.0) if valid_count else 0.0, 2),
        }

    return {
        "classes": classes,
        "ndvi": ndvi,
        "ndwi": ndwi,
        "brightness_threshold": brightness_threshold,
        "valid_pixels": valid_count,
        "stats": stats,
        "width": int(classes.shape[1]),
        "height": int(classes.shape[0]),
        "transform": transform,
        "crs": crs,
    }


def render_feature_png(classes: np.ndarray, output_path: str) -> None:
    """Render a simple transparent feature classification quicklook."""
    rgba = np.zeros((*classes.shape, 4), dtype=np.uint8)
    rgba[classes == 1] = (55, 190, 95, 170)
    rgba[classes == 2] = (40, 130, 235, 190)
    rgba[classes == 3] = (235, 155, 55, 175)
    Image.fromarray(rgba, mode="RGBA").save(output_path)


def compare_class_maps(before: np.ndarray, after: np.ndarray) -> dict[str, Any]:
    if before.shape != after.shape:
        raise ValueError("Before and after scenes must have identical dimensions.")

    valid = (before > 0) & (after > 0)
    changed = valid & (before != after)
    valid_pixels = int(valid.sum())
    changed_pixels = int(changed.sum())

    transitions = []
    for from_id in range(1, 4):
        for to_id in range(1, 4):
            if from_id == to_id:
                continue
            count = int((valid & (before == from_id) & (after == to_id)).sum())
            if count:
                transitions.append({
                    "from_class": CLASS_NAMES[from_id],
                    "to_class": CLASS_NAMES[to_id],
                    "pixels": count,
                    "percent_of_changed": round((count / changed_pixels * 100.0) if changed_pixels else 0.0, 2),
                })

    transitions.sort(key=lambda item: item["pixels"], reverse=True)
    return {
        "valid_pixels": valid_pixels,
        "changed_pixels": changed_pixels,
        "changed_percent": round((changed_pixels / valid_pixels * 100.0) if valid_pixels else 0.0, 2),
        "transitions": transitions,
    }


def render_change_png(before: np.ndarray, after: np.ndarray, output_path: str) -> None:
    """Render class transitions as a transparent change overlay."""
    rgba = np.zeros((*before.shape, 4), dtype=np.uint8)
    valid = (before > 0) & (after > 0)

    # Key transitions used by the UI legend.
    masks = {
        (1, 3): (230, 65, 70, 210),   # vegetation -> built
        (1, 2): (50, 120, 235, 210),  # vegetation -> water
        (3, 1): (50, 190, 95, 210),   # built -> vegetation
        (2, 3): (230, 130, 45, 210),  # water -> built
        (3, 2): (150, 80, 220, 210),  # built -> water
        (2, 1): (245, 200, 60, 210),  # water -> vegetation
    }
    for (from_id, to_id), color in masks.items():
        rgba[valid & (before == from_id) & (after == to_id)] = color

    # Any other class transition is shown in neutral white.
    other = valid & (before != after) & (rgba[..., 3] == 0)
    rgba[other] = (245, 245, 245, 190)
    Image.fromarray(rgba, mode="RGBA").save(output_path)
