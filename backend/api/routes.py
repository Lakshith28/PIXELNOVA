"""
PIXELNOVA - API Routes (Phase 1: upload, validate, preview)
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from geospatial.color import compute_stretch_bounds
from geospatial.preview import generate_preview_png
from geospatial.render import render_confidence_png, render_true_color_png, write_enhanced_geotiff
from geospatial.validation import validate_geotiff
from preprocessing.normalize import load_normalized_bands
from super_resolution import pretrained_esrgan
from super_resolution.baseline import METHOD_LABEL as CLASSICAL_METHOD_LABEL
from super_resolution.baseline import enhance as classical_enhance
from uncertainty.heuristic import compute_confidence

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
INPUT_DIR = DATA_DIR / "input"
PROCESSED_DIR = DATA_DIR / "processed"

INPUT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".tif", ".tiff"}

# In-memory scene registry for the MVP. Phase 2+ should move this to Postgres.
SCENES: dict[str, dict] = {}


@router.post("/scenes/upload")
async def upload_scene(file: UploadFile = File(...)):
    """
    MVP-1: Accept a Sentinel-2 GeoTIFF upload.
    MVP-2: Validate it and return metadata.
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Expected one of {sorted(ALLOWED_EXTENSIONS)}.",
        )

    scene_id = str(uuid.uuid4())
    dest_path = INPUT_DIR / f"{scene_id}{suffix}"

    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = validate_geotiff(str(dest_path))

    SCENES[scene_id] = {
        "scene_id": scene_id,
        "original_filename": file.filename,
        "file_path": str(dest_path),
        "validation": result.as_dict(),
        "preview_generated": False,
    }

    if not result.valid:
        return {
            "scene_id": scene_id,
            "accepted": False,
            "validation": result.as_dict(),
        }

    return {
        "scene_id": scene_id,
        "accepted": True,
        "validation": result.as_dict(),
    }


@router.get("/scenes/{scene_id}")
async def get_scene(scene_id: str):
    scene = SCENES.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    return scene


@router.get("/scenes/{scene_id}/preview")
async def get_scene_preview(scene_id: str):
    """
    MVP-3 support: generate (if needed) and serve a PNG quicklook of the
    scene so the frontend can overlay it on the Leaflet map.
    """
    scene = SCENES.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    if not scene["validation"]["valid"]:
        raise HTTPException(status_code=400, detail="Scene failed validation; cannot preview.")

    preview_path = PROCESSED_DIR / f"{scene_id}_preview.png"
    if not preview_path.exists():
        generate_preview_png(scene["file_path"], str(preview_path))
        scene["preview_generated"] = True

    return FileResponse(
        preview_path,
        media_type="image/png",
        headers={"Cache-Control": "no-store, must-revalidate"},
    )


@router.post("/scenes/{scene_id}/run")
async def run_ai_pipeline(scene_id: str):
    """
    Runs the AI pipeline: preprocessing, super-resolution (pretrained
    ESRGAN model, falling back to classical upsampling if unavailable),
    heuristic confidence, and exports a real georeferenced enhanced
    GeoTIFF plus PNGs for the frontend.

    HONEST LABELING: method_label and the disclaimer field always
    reflect what actually ran. See super_resolution/pretrained_esrgan.py
    and uncertainty/heuristic.py for the honesty notes on each.
    """
    scene = SCENES.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    if not scene["validation"]["valid"]:
        raise HTTPException(status_code=400, detail="Scene failed validation; cannot process.")

    scale_factor = 4
    loaded = load_normalized_bands(scene["file_path"])
    bands = loaded["bands"]

    # Memory safety: the free-tier server has 512MB total. Measured 800x800
    # input peaking at ~580MB during tiled inference (over budget); a small
    # demo AOI (~200x200) measured ~115MB (safe). Cap here rather than risk
    # crashing the live server - MAX_PIXELS gives comfortable headroom.
    MAX_PIXELS = 250_000  # e.g. ~500x500
    input_pixels = bands.shape[1] * bands.shape[2]
    if input_pixels > MAX_PIXELS:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Scene is {bands.shape[2]}x{bands.shape[1]} px ({input_pixels:,} px), "
                f"which exceeds the {MAX_PIXELS:,} px limit for AI processing on this "
                "server. Please upload a smaller AOI crop (roughly 500x500 px or less)."
            ),
        )

    # Compute the color stretch from the ORIGINAL image and reuse it for
    # the enhanced render below, so "Enhanced" looks like a sharper version
    # of "Original" - not a differently-colored image. See geospatial/color.py.
    original_rgb_stack = np.stack([bands[2], bands[1], bands[0]], axis=0) if bands.shape[0] >= 3 else None
    shared_stretch_bounds = compute_stretch_bounds(original_rgb_stack) if original_rgb_stack is not None else None

    # Try the pretrained AI model first; fall back to classical upsampling if
    # it can't load or fails for any reason (untested dependency on this
    # server - see pretrained_esrgan.py's module docstring). Either way, the
    # API response's method_label and disclaimer reflect what ACTUALLY ran.
    try:
        enhanced = pretrained_esrgan.enhance_trained_from_file(
            scene["file_path"], scale_factor=scale_factor
        )
        method_label = pretrained_esrgan.METHOD_LABEL
        method_disclaimer = pretrained_esrgan.METHOD_DISCLAIMER
    except Exception as exc:  # noqa: BLE001 - deliberate fallback path
        print(f"[run_ai_pipeline] Trained model failed ({exc}); using classical baseline.")
        enhanced = classical_enhance(bands, scale_factor=scale_factor)
        method_label = CLASSICAL_METHOD_LABEL
        method_disclaimer = (
            "The AI model was unavailable, so this used classical Lanczos "
            "upsampling instead - not a trained AI super-resolution model. "
            "Confidence is a heuristic proxy based on local variance in the "
            "original image, not calibrated model uncertainty."
        )

    confidence_result = compute_confidence(
        bands, enhanced.shape[1:], loaded.get("nodata_mask")
    )

    enhanced_png_path = PROCESSED_DIR / f"{scene_id}_enhanced.png"
    confidence_png_path = PROCESSED_DIR / f"{scene_id}_confidence.png"
    enhanced_tif_path = PROCESSED_DIR / f"{scene_id}_enhanced.tif"

    render_true_color_png(enhanced, str(enhanced_png_path), stretch_bounds=shared_stretch_bounds)
    render_confidence_png(confidence_result["confidence_map"], str(confidence_png_path))
    write_enhanced_geotiff(
        enhanced, loaded["transform"], loaded["crs"], str(enhanced_tif_path), scale_factor
    )

    run_result = {
        "method_label": method_label,
        "confidence_method": confidence_result["method"],
        "mean_confidence": round(confidence_result["mean_confidence"], 3),
        "high_confidence_pct": confidence_result["high_confidence_pct"],
        "medium_confidence_pct": confidence_result["medium_confidence_pct"],
        "low_confidence_pct": confidence_result["low_confidence_pct"],
        "input_width": bands.shape[2],
        "input_height": bands.shape[1],
        "output_width": enhanced.shape[2],
        "output_height": enhanced.shape[1],
        "scale_factor": scale_factor,
        "input_resolution_m": round(loaded["pixel_resolution_m"], 2),
        "output_resolution_m": round(loaded["pixel_resolution_m"] / scale_factor, 2),
        "disclaimer": method_disclaimer,
    }
    scene["run_result"] = run_result
    return run_result


@router.get("/scenes/{scene_id}/enhanced-preview")
async def get_enhanced_preview(scene_id: str):
    scene = SCENES.get(scene_id)
    if not scene or "run_result" not in scene:
        raise HTTPException(status_code=404, detail="Run the AI pipeline first.")
    path = PROCESSED_DIR / f"{scene_id}_enhanced.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Enhanced preview not found.")
    return FileResponse(
        path, media_type="image/png", headers={"Cache-Control": "no-store, must-revalidate"}
    )


@router.get("/scenes/{scene_id}/confidence-preview")
async def get_confidence_preview(scene_id: str):
    scene = SCENES.get(scene_id)
    if not scene or "run_result" not in scene:
        raise HTTPException(status_code=404, detail="Run the AI pipeline first.")
    path = PROCESSED_DIR / f"{scene_id}_confidence.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Confidence preview not found.")
    return FileResponse(
        path, media_type="image/png", headers={"Cache-Control": "no-store, must-revalidate"}
    )


@router.get("/scenes/{scene_id}/enhanced-geotiff")
async def get_enhanced_geotiff(scene_id: str):
    scene = SCENES.get(scene_id)
    if not scene or "run_result" not in scene:
        raise HTTPException(status_code=404, detail="Run the AI pipeline first.")
    path = PROCESSED_DIR / f"{scene_id}_enhanced.tif"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Enhanced GeoTIFF not found.")
    return FileResponse(
        path, media_type="image/tiff", filename=f"pixelnova_enhanced_{scene_id[:8]}.tif"
    )


@router.get("/scenes")
async def list_scenes():
    return {
        "scenes": [
            {
                "scene_id": s["scene_id"],
                "original_filename": s["original_filename"],
                "valid": s["validation"]["valid"],
                "bounds_wgs84": s["validation"]["metadata"].get("bounds_wgs84"),
            }
            for s in SCENES.values()
        ]
    }
