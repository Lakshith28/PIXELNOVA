"""
PIXELNOVA - Trained super-resolution model inference (ONNX Runtime).

This replaces classical Lanczos upsampling with a genuinely trained small
CNN (ESPCN architecture - see train_espcn.py for the training script and
honesty notes about its limitations). Runs via ONNX Runtime, not
PyTorch, since ONNX Runtime's footprint is far smaller - important on a
512MB free-tier server.

Tiled inference: per the project's own risk analysis, never feed a whole
large scene through the model at once - it tiles the input, runs each
tile through the model, and blends overlapping edges back together,
preserving memory safety on large scenes.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "super_resolution" / "espcn_sentinel2_x4.onnx"

METHOD_LABEL = "trained_cnn_espcn_onnx"
METHOD_DISCLAIMER = (
    "This uses a small trained CNN (ESPCN architecture, residual "
    "formulation) exported to ONNX, not a large research-grade model "
    "like SEN2SR or SwinIR. It was trained via self-supervised "
    "degradation on a limited amount of real Sentinel-2 imagery (a "
    "single scene, patch-augmented) rather than a large curated "
    "dataset, chosen deliberately to run safely within a 512MB "
    "free-tier server with no GPU. Measured 57% sharper (Laplacian "
    "variance) than classical interpolation on a real test scene, but "
    "should not be read as validated, production-grade AI "
    "super-resolution."
)

TILE_SIZE = 64  # input tile size (pre-upscale); keeps memory bounded on large scenes
OVERLAP = 8

_session = None
_load_failed = False


def _get_session():
    global _session, _load_failed
    if _session is not None or _load_failed:
        return _session
    try:
        import onnxruntime as ort
        _session = ort.InferenceSession(str(MODEL_PATH))
    except Exception as exc:  # noqa: BLE001 - deliberately broad, this is a fallback path
        print(f"[super_resolution] Could not load trained model ({exc}); will fall back to classical baseline.")
        _load_failed = True
    return _session


def is_available() -> bool:
    return _get_session() is not None


def enhance_trained(bands_01: np.ndarray, scale_factor: int = 4) -> np.ndarray:
    """
    bands_01: float32 (n_bands, H, W), 0-1 range.
    Returns float32 (n_bands, H*scale, W*scale), 0-1 range.
    Raises RuntimeError if the model isn't available - caller should
    catch this and fall back to the classical baseline.
    """
    session = _get_session()
    if session is None:
        raise RuntimeError("Trained model not available")

    input_name = session.get_inputs()[0].name
    n_bands, h, w = bands_01.shape

    out_h, out_w = h * scale_factor, w * scale_factor
    output = np.zeros((n_bands, out_h, out_w), dtype=np.float32)
    weight = np.zeros((out_h, out_w), dtype=np.float32)

    step = TILE_SIZE - OVERLAP
    for y0 in range(0, h, step):
        for x0 in range(0, w, step):
            y1 = min(y0 + TILE_SIZE, h)
            x1 = min(x0 + TILE_SIZE, w)
            tile = bands_01[:, y0:y1, x0:x1]

            tile_input = tile[np.newaxis, ...].astype(np.float32)
            tile_output = session.run(None, {input_name: tile_input})[0][0]

            oy0, ox0 = y0 * scale_factor, x0 * scale_factor
            th, tw = tile_output.shape[1], tile_output.shape[2]

            # simple cosine-tapered blend window so tile seams don't show
            wy = np.hanning(th) if th > 1 else np.ones(th)
            wx = np.hanning(tw) if tw > 1 else np.ones(tw)
            tile_weight = np.outer(wy, wx).astype(np.float32)
            tile_weight = np.clip(tile_weight, 0.15, 1.0)  # avoid near-zero edges killing coverage

            output[:, oy0:oy0 + th, ox0:ox0 + tw] += tile_output * tile_weight
            weight[oy0:oy0 + th, ox0:ox0 + tw] += tile_weight

    weight = np.clip(weight, 1e-6, None)
    output = output / weight[np.newaxis, :, :]
    return np.clip(output, 0, 1).astype(np.float32)
