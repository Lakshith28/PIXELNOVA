"""
PIXELNOVA - Shared color stretching logic.

Both the "Original" preview and the "Enhanced" render need to turn raw
band values into a displayable 8-bit RGB image. If each computes its own
percentile stretch independently, they land on different brightness/color
balances even though they're the same underlying scene - "Enhanced" ends
up looking color-shifted rather than simply sharper, which is misleading.

The fix: compute the stretch bounds ONCE from the original data, and reuse
those exact bounds everywhere that scene is rendered.
"""
from __future__ import annotations

import numpy as np


def compute_stretch_bounds(rgb: np.ndarray, low: float = 2.0, high: float = 98.0) -> list[tuple[float, float]]:
    """
    rgb: array shaped (..., 3) or (3, H, W) - works with either since we
    just need per-channel percentiles.
    Returns [(lo, hi), (lo, hi), (lo, hi)] for R, G, B.
    """
    bounds = []
    if rgb.shape[0] == 3:
        channels = [rgb[i] for i in range(3)]
    else:
        channels = [rgb[..., i] for i in range(3)]

    for band in channels:
        finite = band[np.isfinite(band)]
        if finite.size == 0:
            bounds.append((0.0, 1.0))
            continue
        lo, hi = np.percentile(finite, [low, high])
        if hi <= lo:
            hi = lo + 1e-6
        bounds.append((float(lo), float(hi)))
    return bounds


def apply_stretch(rgb: np.ndarray, bounds: list[tuple[float, float]]) -> np.ndarray:
    """
    rgb: (H, W, 3). Applies the given per-channel (lo, hi) bounds and
    returns a uint8 (H, W, 3) array. Values outside the original bounds
    (e.g. a sharper/upsampled version reaching slightly higher peaks)
    are simply clipped, not re-stretched - that's what keeps the color
    calibration identical to the source it was computed from.
    """
    out = np.zeros_like(rgb, dtype=np.uint8)
    for ch in range(3):
        lo, hi = bounds[ch]
        band = rgb[..., ch]
        stretched = np.clip((band - lo) / (hi - lo), 0, 1) * 255.0
        out[..., ch] = stretched.astype(np.uint8)
    return out
