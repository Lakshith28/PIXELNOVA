"""
PIXELNOVEL - API Routes (Phase 1: upload, validate, preview)
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from geospatial.preview import generate_preview_png
from geospatial.validation import validate_geotiff

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
