"""
PIXELNOVA - Pretrained AI super-resolution via the `sentinel2sr` package
(wsx4_spatrad model: ESRGAN trained on the WorldStrat dataset).

Why this instead of a custom-trained model: this ships pretrained
weights, so there's no training step at all - just an extra Python
dependency that gets installed at deploy time. Much simpler and more
reliable for this project's constraints (no local training environment
available).

HONEST LIMITATIONS (from the model authors themselves, see
https://github.com/openearthplatforminitiative/sentinel2-super-resolution):
wsx4_spatrad is documented as their least safe model in terms of
accuracy - it struggles especially in urban areas and can generate
information not present in the original image. It performs meaningfully
better on rural/natural scenes. This is surfaced to the user via
METHOD_DISCLAIMER below, not hidden.

UNVERIFIED: this module could not be executed or tested before being
handed off - the package isn't installable in the offline dev sandbox
this was written in. The first real test of this code is the live
Render deploy. If it fails or is too slow/memory-heavy on the free
tier, the caller (api/routes.py) catches the exception and falls back
to the classical baseline automatically - so a failure here degrades
gracefully rather than breaking the app.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import rasterio

METHOD_LABEL = "ai_esrgan_wsx4_spatrad"
METHOD_DISCLAIMER = (
    "AI super-resolution using a pretrained ESRGAN model (wsx4_spatrad, "
    "trained on the WorldStrat dataset). The model's own authors document "
    "it as their least reliable model in terms of accuracy - it can "
    "generate plausible-looking detail that was not actually present in "
    "the original 10m data, particularly in dense urban areas. It "
    "performs meaningfully better on rural/natural scenes. Treat fine "
    "detail in this output as illustrative, not verified ground truth."
)

MODEL_NAME = "wsx4_spatrad"


def enhance_trained_from_file(input_tif_path: str, scale_factor: int = 4) -> np.ndarray:
    """
    Runs the pretrained wsx4_spatrad model on the original uploaded
    GeoTIFF directly (the sentinel2sr package reads the file itself,
    expecting bands in order [B02, B03, B04, B08] - the same order this
    app already validates and uses throughout).

    Returns a float32 (n_bands, H, W) array in ~0-1 reflectance range,
    to match the convention the rest of this pipeline (render.py,
    heuristic.py) already expects.

    Raises on any failure - the caller in api/routes.py catches this and
    falls back to the classical baseline, so a bad deploy of this
    dependency doesn't break the app entirely.
    """
    from sentinel2sr import run  # deferred: heavy import, only pay the cost if actually used

    with tempfile.TemporaryDirectory() as out_dir:
        run(MODEL_NAME, input_tif_path, output_dir=out_dir)

        out_files = sorted(Path(out_dir).glob("*.tif")) + sorted(Path(out_dir).glob("*.tiff"))
        if not out_files:
            raise RuntimeError(
                f"sentinel2sr produced no output file in {out_dir} - check its logs."
            )

        with rasterio.open(out_files[0]) as ds:
            arr = ds.read().astype(np.float32)

        # Defensive scale detection: Sentinel-2 L2A data conventionally
        # comes as digital numbers scaled by 10000 (so 0-1 reflectance
        # after dividing). If the output is already in a small range, it's
        # already normalized and dividing again would be wrong - checking
        # the actual max avoids silently mangling the output either way.
        if arr.max() > 10.0:
            arr = arr / 10000.0
        arr = np.clip(arr, 0.0, 1.0)

        expected_h = None  # no hard assertion on exact shape - just sanity check it upsampled
        if arr.shape[-1] < 2 or arr.shape[-2] < 2:
            raise RuntimeError(f"sentinel2sr output looks malformed: shape {arr.shape}")

        return arr
