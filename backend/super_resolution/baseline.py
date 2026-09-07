"""
PIXELNOVA - Super-resolution: classical baseline

IMPORTANT / HONESTY NOTE:
This module performs classical (Lanczos) upsampling. It is NOT a trained
super-resolution model, and every place this output is surfaced (API
response, frontend UI) must label it as a "classical baseline" — not as
"AI-enhanced" or "AI super-resolution". Labeling ordinary interpolation as
learned super-resolution would be scientifically dishonest and is exactly
the mistake this project's own positioning explicitly warns against.

This module exists so the rest of the pipeline (API contract, frontend
before/after UI, confidence overlay, export) can be built and tested end
to end now, with a real trained model (e.g. an ONNX-exported Sentinel-2
SR network) swapped in later behind the same `enhance()` function
signature — without touching any other layer of the app.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

METHOD_LABEL = "classical_baseline_lanczos"


def enhance(bands: np.ndarray, scale_factor: int = 4) -> np.ndarray:
    """
    bands: float32 array, shape (n_bands, H, W), values ~0-1.
    Returns an upsampled array of shape (n_bands, H*scale, W*scale).

    Uses per-band Lanczos resampling via PIL. This is classical
    interpolation: it makes the image visually larger/smoother, but it
    does not reconstruct genuinely new spatial information the way a
    trained super-resolution model would.
    """
    n_bands, h, w = bands.shape
    out_h, out_w = h * scale_factor, w * scale_factor
    out = np.zeros((n_bands, out_h, out_w), dtype=np.float32)

    for i in range(n_bands):
        band_u8 = np.clip(bands[i] * 255.0, 0, 255).astype(np.uint8)
        img = Image.fromarray(band_u8, mode="L")
        resized = img.resize((out_w, out_h), resample=Image.LANCZOS)
        out[i] = np.asarray(resized, dtype=np.float32) / 255.0

    return out
