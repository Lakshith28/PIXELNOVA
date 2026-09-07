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
        # Resample directly in float32 ("F" mode), NOT via an 8-bit uint8
        # cast first. Reflectance values typically only span a narrow
        # slice of 0-1 (e.g. 0.02-0.3 for land), so quantizing to 256
        # levels before resampling threw away almost all real tonal
        # detail and let Lanczos's negative lobes ring on the resulting
        # blocky data — that was the source of the dark/orange blotch
        # artifacts, not genuine enhancement.
        img = Image.fromarray(bands[i], mode="F")
        resized = img.resize((out_w, out_h), resample=Image.LANCZOS)
        resized_arr = np.asarray(resized, dtype=np.float32)
        # Lanczos has negative lobes even on clean float data (mild
        # ringing at sharp edges is mathematically expected) — clip at
        # the very end, once, rather than truncating precision early.
        out[i] = np.clip(resized_arr, 0.0, 1.0)

    return out
