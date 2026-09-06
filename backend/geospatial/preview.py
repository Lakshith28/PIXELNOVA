"""
PIXELNOVA - Preview Generation (MVP-3 support)

Generates a downsampled, browser-viewable PNG thumbnail of the uploaded
scene so the frontend can overlay it on the Leaflet map without shipping
the full GeoTIFF to the browser.

Band convention assumed for a standard 4-band Sentinel-2 stack (B02, B03,
B04, B08), 1-indexed as rasterio expects:
    band 1 = B02 (Blue)
    band 2 = B03 (Green)
    band 3 = B04 (Red)
    band 4 = B08 (Near Infrared)

This matters: true-color RGB is (B04, B03, B02) = (band 3, band 2, band 1).
An earlier version of this file used (band 4, band 3, band 2), which put
Near-Infrared in the red channel — producing an image that looks like
random noise/false color instead of a recognizable satellite photo. That
was the root cause of the "colorful static" preview reported during
testing, not (only) the synthetic test data.
"""
from __future__ import annotations

import numpy as np
import rasterio
from PIL import Image

# Sentinel-2 L1C/L2A reflectance is typically scaled 0-10000 (uint16).
# Dividing by this brings values into an approximate 0-1 reflectance range
# before contrast stretching, instead of stretching raw digital numbers
# blindly.
SENTINEL2_REFLECTANCE_SCALE = 10000.0


def generate_preview_png(
    src_path: str,
    dst_path: str,
    max_size: int = 1024,
    mode: str = "true_color",
) -> dict:
    """
    mode: "true_color" -> bands (B04, B03, B02) i.e. (3, 2, 1)
          "false_color" -> bands (B08, B04, B03) i.e. (4, 3, 2), vegetation-oriented
    Falls back gracefully if the scene doesn't have 4 bands.
    """
    with rasterio.open(src_path) as dataset:
        band_count = dataset.count
        indexes = _select_band_indexes(band_count, mode)

        scale = min(1.0, max_size / max(dataset.width, dataset.height))
        out_h = max(1, int(dataset.height * scale))
        out_w = max(1, int(dataset.width * scale))

        arr = dataset.read(indexes, out_shape=(3, out_h, out_w)).astype(np.float32)
        rgb = np.transpose(arr, (1, 2, 0))

        # Reflectance scaling: bring plausible Sentinel-2 digital numbers
        # into 0-1 before stretching, if values look like raw DN (>1.5).
        if np.nanmax(rgb) > 1.5:
            rgb = rgb / SENTINEL2_REFLECTANCE_SCALE

        normalized = _percentile_stretch(rgb)

        img = Image.fromarray(normalized, mode="RGB")
        img.save(dst_path, format="PNG")

        return {
            "preview_path": dst_path,
            "width_px": out_w,
            "height_px": out_h,
            "source_bands_used": indexes,
            "mode": mode,
        }


def _select_band_indexes(band_count: int, mode: str) -> list[int]:
    if band_count >= 4:
        if mode == "false_color":
            return [4, 3, 2]  # NIR, Red, Green
        return [3, 2, 1]  # Red, Green, Blue (true color)
    if band_count == 3:
        return [3, 2, 1] if mode != "false_color" else [3, 2, 1]
    return [1, 1, 1]  # grayscale-as-RGB fallback for single-band rasters


def _percentile_stretch(rgb: np.ndarray, low: float = 2.0, high: float = 98.0) -> np.ndarray:
    """Simple 2-98 percentile contrast stretch per-band, output as uint8."""
    out = np.zeros_like(rgb, dtype=np.uint8)
    for band_idx in range(rgb.shape[-1]):
        band = rgb[..., band_idx]
        finite = band[np.isfinite(band)]
        if finite.size == 0:
            continue
        lo, hi = np.percentile(finite, [low, high])
        if hi <= lo:
            hi = lo + 1.0
        stretched = np.clip((band - lo) / (hi - lo), 0, 1) * 255.0
        out[..., band_idx] = stretched.astype(np.uint8)
    return out

