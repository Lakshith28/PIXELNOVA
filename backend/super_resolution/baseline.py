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

METHOD_LABEL = "classical_baseline_lanczos_sharpened"


def _gaussian_kernel_1d(sigma: float) -> np.ndarray:
    radius = max(1, int(3 * sigma))
    x = np.arange(-radius, radius + 1)
    k = np.exp(-(x**2) / (2 * sigma**2))
    return (k / k.sum()).astype(np.float32)


def _gaussian_blur(arr: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Pure numpy separable Gaussian blur (no extra dependency needed)."""
    k = _gaussian_kernel_1d(sigma)
    pad = len(k) // 2
    padded = np.pad(arr, pad, mode="edge")
    blurred_rows = np.apply_along_axis(
        lambda m: np.convolve(m, k, mode="valid"), axis=1, arr=padded
    )
    blurred = np.apply_along_axis(
        lambda m: np.convolve(m, k, mode="valid"), axis=0, arr=blurred_rows
    )
    return blurred.astype(np.float32)


def _unsharp_mask(arr: np.ndarray, amount: float = 0.8, sigma: float = 1.5) -> np.ndarray:
    """
    Classic unsharp masking: sharpened = original + amount * (original - blurred).
    This is standard, decades-old image-processing technique — NOT AI, and
    it does not invent detail that isn't statistically present in the
    upsampled data. It boosts local contrast at edges that Lanczos
    interpolation otherwise smooths out, which is what actually reads as
    "sharper" to the eye. Still honestly labeled as classical, not AI.
    """
    blurred = _gaussian_blur(arr, sigma=sigma)
    sharpened = arr + amount * (arr - blurred)
    return np.clip(sharpened, 0.0, 1.0)


def enhance(bands: np.ndarray, scale_factor: int = 4) -> np.ndarray:
    """
    bands: float32 array, shape (n_bands, H, W), values ~0-1.
    Returns an upsampled array of shape (n_bands, H*scale, W*scale).

    Pipeline: per-band Lanczos resampling (float32, no precision-crushing
    8-bit step) followed by unsharp masking. This is still classical
    processing — it makes real edges in the data crisper, but it does not
    reconstruct genuinely new spatial information the way a trained
    super-resolution model would. Labeled accordingly everywhere this
    output surfaces (API response, frontend UI).
    """
    n_bands, h, w = bands.shape
    out_h, out_w = h * scale_factor, w * scale_factor
    out = np.zeros((n_bands, out_h, out_w), dtype=np.float32)

    for i in range(n_bands):
        img = Image.fromarray(bands[i], mode="F")
        resized = img.resize((out_w, out_h), resample=Image.LANCZOS)
        resized_arr = np.asarray(resized, dtype=np.float32)
        resized_arr = np.clip(resized_arr, 0.0, 1.0)
        out[i] = _unsharp_mask(resized_arr, amount=0.8, sigma=1.5)

    return out
