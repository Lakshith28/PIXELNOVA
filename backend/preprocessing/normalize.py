"""
PIXELNOVA - Preprocessing: reflectance normalization

Converts raw Sentinel-2 digital numbers into a normalized float32 array
suitable as model input, and reports basic scene-quality signals used to
gate whether processing should proceed.
"""
from __future__ import annotations

import numpy as np
import rasterio

from geospatial.validation import EXPECTED_RESOLUTIONS_M

SENTINEL2_REFLECTANCE_SCALE = 10000.0


def load_normalized_bands(path: str, band_order: tuple[int, ...] = (1, 2, 3, 4)) -> dict:
    """
    Reads the requested bands, scales digital numbers to approximate
    surface reflectance (0-1), and clips outliers. Returns the array plus
    basic scene stats used by the (future) model and by the confidence
    heuristic.
    """
    with rasterio.open(path) as dataset:
        available = tuple(b for b in band_order if b <= dataset.count)
        arr = dataset.read(available).astype(np.float32)

        if np.nanmax(arr) > 1.5:
            arr = arr / SENTINEL2_REFLECTANCE_SCALE

        arr = np.clip(arr, 0.0, 1.0)

        nodata_mask = None
        if dataset.nodata is not None:
            raw = dataset.read(available)
            nodata_mask = np.all(raw == dataset.nodata, axis=0)

        pixel_res = (abs(dataset.transform.a) + abs(dataset.transform.e)) / 2.0

        return {
            "bands": arr,  # shape (n_bands, H, W), float32, ~0-1
            "band_indexes_used": available,
            "nodata_mask": nodata_mask,
            "pixel_resolution_m": pixel_res,
            "resolution_is_standard": any(
                abs(pixel_res - r) <= 1.0 for r in EXPECTED_RESOLUTIONS_M
            ),
            "transform": dataset.transform,
            "crs": dataset.crs,
            "width": dataset.width,
            "height": dataset.height,
        }
