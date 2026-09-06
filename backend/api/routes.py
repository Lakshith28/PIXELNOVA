"""
PIXELNOVA - API Routes (Phase 1: upload, validate, preview)
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from geospatial.preview import generate_preview_png
from geospatial.render import render_confidence_png, render_true_color_png, write_enhanced_geotiff
from geospatial.validation import validate_geotiff
from preprocessing.normalize import load_normalized_bands
from super_resolution.baseline import METHOD_LABEL, enhance
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

    return FileResponse(preview_path, media_type="image/png")


@router.post("/scenes/{scene_id}/run")
async def run_ai_pipeline(scene_id: str):
    """
    MVP-4/6/7: runs the current pipeline (classical baseline upsampling +
    heuristic confidence), exports a real georeferenced enhanced GeoTIFF,
    and renders PNGs for the frontend before/after and confidence views.

    HONEST LABELING: this is deliberately NOT called "AI super-resolution"
    anywhere in the response. See super_resolution/baseline.py and
    uncertainty/heuristic.py for why.
    """
    scene = SCENES.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    if not scene["validation"]["valid"]:
        raise HTTPException(status_code=400, detail="Scene failed validation; cannot process.")

    scale_factor = 4
    loaded = load_normalized_bands(scene["file_path"])
    bands = loaded["bands"]

    enhanced = enhance(bands, scale_factor=scale_factor)
    confidence_result = compute_confidence(
        bands, enhanced.shape[1:], loaded.get("nodata_mask")
    )

    enhanced_png_path = PROCESSED_DIR / f"{scene_id}_enhanced.png"
    confidence_png_path = PROCESSED_DIR / f"{scene_id}_confidence.png"
    enhanced_tif_path = PROCESSED_DIR / f"{scene_id}_enhanced.tif"

    render_true_color_png(enhanced, str(enhanced_png_path))
    render_confidence_png(confidence_result["confidence_map"], str(confidence_png_path))
    write_enhanced_geotiff(
        enhanced, loaded["transform"], loaded["crs"], str(enhanced_tif_path), scale_factor
    )

    run_result = {
        "method_label": METHOD_LABEL,
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
        "disclaimer": (
            "This uses classical Lanczos upsampling as a placeholder, not a "
            "trained AI super-resolution model. Confidence is a heuristic "
            "proxy based on local variance in the original image, not "
            "calibrated model uncertainty. Both will be replaced with real "
            "trained components in a later phase."
        ),
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
    return FileResponse(path, media_type="image/png")


@router.get("/scenes/{scene_id}/confidence-preview")
async def get_confidence_preview(scene_id: str):
    scene = SCENES.get(scene_id)
    if not scene or "run_result" not in scene:
        raise HTTPException(status_code=404, detail="Run the AI pipeline first.")
    path = PROCESSED_DIR / f"{scene_id}_confidence.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Confidence preview not found.")
    return FileResponse(path, media_type="image/png")


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
