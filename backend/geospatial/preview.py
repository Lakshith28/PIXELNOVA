"""
PIXELNOVEL - Preview Generation (MVP-3 support)

Generates a downsampled, browser-viewable PNG thumbnail of the uploaded
scene so the frontend can overlay it on the Leaflet map without shipping
the full GeoTIFF to the browser.
"""
from __future__ import annotations

import numpy as np
import rasterio
from PIL import Image


def generate_preview_png(src_path: str, dst_path: str, max_size: int = 1024) -> dict:
    """
    Reads up to 3 bands (assumes band order roughly matches RGB-ish for a
    quicklook; true Sentinel-2 band mapping is refined in Phase 2), downsamples,
    normalizes to 8-bit, and writes a PNG. Returns basic info about what was written.
    """
    with rasterio.open(src_path) as dataset:
        band_count = dataset.count
        # Prefer bands 4,3,2 (R,G,B) if this looks like a standard Sentinel-2
        # stack with >=4 bands (B2,B3,B4,B8...); otherwise fall back gracefully.
        if band_count >= 3:
            indexes = [min(4, band_count), min(3, band_count), min(2, band_count)]
        else:
            indexes = [1] * 3  # grayscale-as-RGB fallback

        scale = min(1.0, max_size / max(dataset.width, dataset.height))
        out_h = max(1, int(dataset.height * scale))
        out_w = max(1, int(dataset.width * scale))

        arr = dataset.read(indexes, out_shape=(3, out_h, out_w)).astype(np.float32)

        rgb = np.transpose(arr, (1, 2, 0))
        normalized = _percentile_stretch(rgb)

        img = Image.fromarray(normalized, mode="RGB")
        img.save(dst_path, format="PNG")

        return {
            "preview_path": dst_path,
            "width_px": out_w,
            "height_px": out_h,
            "source_bands_used": indexes,
        }


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
