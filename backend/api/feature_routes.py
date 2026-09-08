"""Feature extraction and prototype two-date change detection routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.routes import SCENES, PROCESSED_DIR
from feature_extraction.features import classify_scene, render_feature_png, compare_class_maps, render_change_png

router = APIRouter()


@router.post("/scenes/{scene_id}/features")
async def extract_features(scene_id: str):
    scene = SCENES.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    if not scene["validation"]["valid"]:
        raise HTTPException(status_code=400, detail="Scene failed validation; cannot extract features.")
    try:
        result = classify_scene(scene["file_path"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    preview_path = PROCESSED_DIR / f"{scene_id}_features.png"
    render_feature_png(result["classes"], str(preview_path))
    response = {
        "method": "spectral_indices_and_built_up_heuristic",
        "ndvi": "(NIR - Red) / (NIR + Red)",
        "ndwi": "(Green - NIR) / (Green + NIR)",
        "built_up_note": "Built-up / bare-ground heuristic; not a supervised building detector.",
        "valid_pixels": result["valid_pixels"],
        "brightness_threshold": round(result["brightness_threshold"], 4),
        "stats": result["stats"],
    }
    scene["feature_result"] = response
    return response


@router.get("/scenes/{scene_id}/features-preview")
async def get_features_preview(scene_id: str):
    scene = SCENES.get(scene_id)
    if not scene or "feature_result" not in scene:
        raise HTTPException(status_code=404, detail="Run feature extraction first.")
    path = PROCESSED_DIR / f"{scene_id}_features.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Feature preview not found.")
    return FileResponse(path, media_type="image/png")


@router.post("/change-detection")
async def change_detection(before_scene_id: str, after_scene_id: str):
    before_scene = SCENES.get(before_scene_id)
    after_scene = SCENES.get(after_scene_id)
    if not before_scene or not after_scene:
        raise HTTPException(status_code=404, detail="Before or after scene not found.")
    if not before_scene["validation"]["valid"] or not after_scene["validation"]["valid"]:
        raise HTTPException(status_code=400, detail="Both scenes must pass validation.")

    try:
        before = classify_scene(before_scene["file_path"])
        after = classify_scene(after_scene["file_path"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if before["width"] != after["width"] or before["height"] != after["height"]:
        raise HTTPException(status_code=400, detail="Before and after scenes must have identical dimensions.")
    if before["crs"] != after["crs"]:
        raise HTTPException(status_code=400, detail="Before and after scenes must use the same CRS.")
    for a, b in zip(tuple(before["transform"]), tuple(after["transform"])):
        if abs(float(a) - float(b)) > 1e-7:
            raise HTTPException(status_code=400, detail="Before and after scenes must use the same geospatial grid/transform.")

    result = compare_class_maps(before["classes"], after["classes"])
    change_path = PROCESSED_DIR / f"{before_scene_id}_{after_scene_id}_change.png"
    render_change_png(before["classes"], after["classes"], str(change_path))
    response = {
        "before_scene_id": before_scene_id,
        "after_scene_id": after_scene_id,
        "method": "class-map comparison using NDVI/NDWI/built-up heuristic",
        "valid_pixels": result["valid_pixels"],
        "changed_pixels": result["changed_pixels"],
        "changed_percent": result["changed_percent"],
        "transitions": result["transitions"],
        "limitation": "Prototype change detection compares vegetation, water and built-up/bare classes; it is not a supervised object-level change detector.",
    }
    after_scene["change_detection_result"] = response
    return response


@router.get("/change-detection/{before_scene_id}/{after_scene_id}/preview")
async def get_change_preview(before_scene_id: str, after_scene_id: str):
    path = PROCESSED_DIR / f"{before_scene_id}_{after_scene_id}_change.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run change detection first.")
    return FileResponse(path, media_type="image/png")
