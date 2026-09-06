"""
PIXELNOVA - Uncertainty: heuristic confidence proxy

HONESTY NOTE: this is a heuristic, not a calibrated model uncertainty
estimate. It should always be labeled "heuristic confidence" in the API
and UI, never plain "confidence" or "accuracy". Per the project's own
validation principles: without a trained model and a formal calibration
procedure, no uncertainty output should be presented as validated
accuracy.

Heuristic used: for classical upsampling, regions where the ORIGINAL
low-resolution signal was already highly variable (edges, texture,
built structure) are the regions the interpolation is most likely to
render sensibly. Regions that were flat/smooth in the original carry
little real information, so any fine detail that appears after
upsampling is more likely to be an interpolation artifact — flagged as
lower confidence. No-data pixels are always flagged lowest confidence.
"""
from __future__ import annotations

import numpy as np

TILE_SIZE = 16  # pixels, in the ORIGINAL (pre-upsampling) resolution


def compute_confidence(
    original_bands: np.ndarray,
    output_shape: tuple[int, int],
    nodata_mask: np.ndarray | None = None,
) -> dict:
    """
    original_bands: float32 array (n_bands, H, W), the pre-upsampling input.
    output_shape: (out_H, out_W) the enhanced image's shape, to upsample
        the confidence grid to match for overlay purposes.
    Returns a dict with a continuous 0-1 confidence map (at output_shape)
    and summary stats.
    """
    n_bands, h, w = original_bands.shape

    tiles_y = max(1, h // TILE_SIZE)
    tiles_x = max(1, w // TILE_SIZE)

    variance_grid = np.zeros((tiles_y, tiles_x), dtype=np.float32)
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            y0, y1 = ty * TILE_SIZE, min((ty + 1) * TILE_SIZE, h)
            x0, x1 = tx * TILE_SIZE, min((tx + 1) * TILE_SIZE, w)
            tile = original_bands[:, y0:y1, x0:x1]
            variance_grid[ty, tx] = float(np.mean(np.var(tile, axis=(1, 2))))

    v_min, v_max = float(variance_grid.min()), float(variance_grid.max())
    if v_max > v_min:
        confidence_grid = (variance_grid - v_min) / (v_max - v_min)
    else:
        confidence_grid = np.full_like(variance_grid, 0.5)

    confidence_map = np.kron(
        confidence_grid,
        np.ones(
            (output_shape[0] // tiles_y + 1, output_shape[1] // tiles_x + 1),
            dtype=np.float32,
        ),
    )[: output_shape[0], : output_shape[1]]

    if nodata_mask is not None and nodata_mask.shape == original_bands.shape[1:]:
        nodata_upsampled = np.kron(
            nodata_mask.astype(np.float32),
            np.ones(
                (output_shape[0] // h + 1, output_shape[1] // w + 1),
                dtype=np.float32,
            ),
        )[: output_shape[0], : output_shape[1]]
        confidence_map = np.where(nodata_upsampled > 0.5, 0.0, confidence_map)

    high = float(np.mean(confidence_map >= 0.66) * 100)
    medium = float(np.mean((confidence_map >= 0.33) & (confidence_map < 0.66)) * 100)
    low = float(np.mean(confidence_map < 0.33) * 100)

    return {
        "confidence_map": confidence_map,
        "mean_confidence": float(np.mean(confidence_map)),
        "high_confidence_pct": round(high, 1),
        "medium_confidence_pct": round(medium, 1),
        "low_confidence_pct": round(low, 1),
        "method": "heuristic_local_variance",
    }
