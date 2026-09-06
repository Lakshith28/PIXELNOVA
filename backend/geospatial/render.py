"""
PIXELNOVA - Rendering helpers: turn in-memory arrays into PNGs the
frontend can display, for both the enhanced image and the confidence
overlay, plus exporting the enhanced raster as a proper georeferenced
GeoTIFF.
"""
from __future__ import annotations

import numpy as np
import rasterio
from rasterio.transform import Affine
from PIL import Image


def render_true_color_png(bands_01: np.ndarray, dst_path: str) -> None:
    """
    bands_01: float32 array (n_bands, H, W) in 0-1 range, band order
    (B02, B03, B04, B08) i.e. index 0=Blue, 1=Green, 2=Red, 3=NIR.
    Writes a true-color (Red, Green, Blue) PNG.
    """
    n_bands = bands_01.shape[0]
    if n_bands >= 3:
        r, g, b = bands_01[2], bands_01[1], bands_01[0]
    else:
        r = g = b = bands_01[0]

    rgb = np.stack([r, g, b], axis=-1)
    stretched = _percentile_stretch(rgb)
    Image.fromarray(stretched, mode="RGB").save(dst_path, format="PNG")


def render_confidence_png(confidence_map: np.ndarray, dst_path: str) -> None:
    """
    confidence_map: float32 array (H, W), 0-1.
    Renders a red -> yellow -> green heatmap (low -> high confidence).
    """
    h, w = confidence_map.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    # 0.0 -> red (200,60,60), 0.5 -> amber (240,190,80), 1.0 -> green (90,190,110)
    c = np.clip(confidence_map, 0, 1)
    low_color = np.array([200, 60, 60])
    mid_color = np.array([240, 190, 80])
    high_color = np.array([90, 190, 110])

    lower_half = c < 0.5
    t_lower = np.clip(c / 0.5, 0, 1)
    t_upper = np.clip((c - 0.5) / 0.5, 0, 1)

    for ch in range(3):
        lower_blend = low_color[ch] + (mid_color[ch] - low_color[ch]) * t_lower
        upper_blend = mid_color[ch] + (high_color[ch] - mid_color[ch]) * t_upper
        rgb[..., ch] = np.where(lower_half, lower_blend, upper_blend).astype(np.uint8)

    Image.fromarray(rgb, mode="RGB").save(dst_path, format="PNG")


def write_enhanced_geotiff(
    bands_01: np.ndarray,
    src_transform: Affine,
    crs,
    dst_path: str,
    scale_factor: int,
) -> None:
    """
    bands_01: float32 array (n_bands, H, W), 0-1 range.
    Writes a real georeferenced GeoTIFF at the enhanced resolution: the
    pixel size shrinks by scale_factor while the scene's real-world
    extent stays identical, which is what "10m -> 2.5m" actually means
    in georeferencing terms.
    """
    n_bands, h, w = bands_01.shape
    new_transform = src_transform * Affine.scale(1.0 / scale_factor)

    data_u16 = np.clip(bands_01 * 10000.0, 0, 10000).astype(np.uint16)

    with rasterio.open(
        dst_path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=n_bands,
        dtype=data_u16.dtype,
        crs=crs,
        transform=new_transform,
    ) as dst:
        dst.write(data_u16)


def _percentile_stretch(rgb: np.ndarray, low: float = 2.0, high: float = 98.0) -> np.ndarray:
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
