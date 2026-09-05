"""
PIXELNOVEL - Raster Validation
Validates that an uploaded file is a usable, georeferenced Sentinel-2-style GeoTIFF.

This is MVP-2: raster validation + metadata display.
We deliberately keep validation rules conservative and explicit, so failures
are explainable to the user (this matters for the "trust" positioning of the
whole product - we don't silently accept bad input).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from rasterio.warp import transform_bounds


# Sentinel-2 L2A/L1C typical native resolutions in metres.
EXPECTED_RESOLUTIONS_M = (10.0, 20.0, 60.0)
RESOLUTION_TOLERANCE_M = 1.0

# Reasonable bounds so a user doesn't accidentally upload a tiny crop or a
# whole-continent mosaic and think the pipeline hung.
MIN_DIMENSION_PX = 32
MAX_DIMENSION_PX = 20000


@dataclass
class ValidationIssue:
    level: str  # "error" | "warning"
    code: str
    message: str


@dataclass
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [issue.__dict__ for issue in self.issues],
            "metadata": self.metadata,
        }


def validate_geotiff(path: str) -> ValidationResult:
    """
    Open the file with rasterio and run a series of checks.
    Returns a ValidationResult that is safe to serialize directly to JSON.
    """
    issues: list[ValidationIssue] = []

    try:
        dataset = rasterio.open(path)
    except RasterioIOError as exc:
        return ValidationResult(
            valid=False,
            issues=[
                ValidationIssue(
                    level="error",
                    code="UNREADABLE_FILE",
                    message=f"File could not be opened as a raster: {exc}",
                )
            ],
        )

    with dataset:
        metadata = _extract_metadata(dataset)

        # --- CRS check ---
        if dataset.crs is None:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="NO_CRS",
                    message="Image has no coordinate reference system (not georeferenced).",
                )
            )

        # --- Dimension checks ---
        if dataset.width < MIN_DIMENSION_PX or dataset.height < MIN_DIMENSION_PX:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="TOO_SMALL",
                    message=(
                        f"Image is only {dataset.width}x{dataset.height} px; "
                        f"minimum supported is {MIN_DIMENSION_PX}x{MIN_DIMENSION_PX} px."
                    ),
                )
            )
        if dataset.width > MAX_DIMENSION_PX or dataset.height > MAX_DIMENSION_PX:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="VERY_LARGE",
                    message=(
                        f"Image is {dataset.width}x{dataset.height} px; scenes this large "
                        "should be tiled before super-resolution (Phase 2)."
                    ),
                )
            )

        # --- Band count check ---
        if dataset.count == 0:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="NO_BANDS",
                    message="Image has zero bands.",
                )
            )
        elif dataset.count < 3:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="LOW_BAND_COUNT",
                    message=(
                        f"Only {dataset.count} band(s) found. Sentinel-2 multispectral "
                        "products typically provide 4+ bands (e.g. B02,B03,B04,B08)."
                    ),
                )
            )

        # --- Resolution sanity check ---
        res_x = abs(dataset.transform.a)
        res_y = abs(dataset.transform.e)
        pixel_res = (res_x + res_y) / 2.0
        matches_expected = any(
            abs(pixel_res - expected) <= RESOLUTION_TOLERANCE_M
            for expected in EXPECTED_RESOLUTIONS_M
        )
        if not matches_expected:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="UNEXPECTED_RESOLUTION",
                    message=(
                        f"Pixel resolution ~{pixel_res:.2f} units/px does not match typical "
                        f"Sentinel-2 resolutions {EXPECTED_RESOLUTIONS_M}. "
                        "Proceeding, but confirm this is Sentinel-2 data."
                    ),
                )
            )

        # --- No-data / nodata coverage check (sampled, not full-scene, for speed) ---
        nodata_pct = _estimate_nodata_percentage(dataset)
        metadata["estimated_nodata_percent"] = round(nodata_pct, 2)
        if nodata_pct > 40.0:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="HIGH_NODATA",
                    message=(
                        f"~{nodata_pct:.1f}% of sampled pixels are no-data/black. "
                        "Scene may be heavily clipped, off-swath, or corrupted."
                    ),
                )
            )

        has_error = any(i.level == "error" for i in issues)

        return ValidationResult(valid=not has_error, issues=issues, metadata=metadata)


def _extract_metadata(dataset: rasterio.io.DatasetReader) -> dict[str, Any]:
    bounds = dataset.bounds
    footprint_wgs84 = None
    try:
        if dataset.crs is not None:
            left, bottom, right, top = transform_bounds(
                dataset.crs, "EPSG:4326", *bounds, densify_pts=21
            )
            footprint_wgs84 = {
                "west": left,
                "south": bottom,
                "east": right,
                "north": top,
            }
    except Exception:
        footprint_wgs84 = None

    return {
        "width_px": dataset.width,
        "height_px": dataset.height,
        "band_count": dataset.count,
        "dtype": str(dataset.dtypes[0]) if dataset.count else None,
        "crs": dataset.crs.to_string() if dataset.crs else None,
        "pixel_resolution": {
            "x": abs(dataset.transform.a),
            "y": abs(dataset.transform.e),
            "units": dataset.crs.linear_units if dataset.crs else "unknown",
        },
        "bounds_native_crs": {
            "left": bounds.left,
            "bottom": bounds.bottom,
            "right": bounds.right,
            "top": bounds.top,
        },
        "bounds_wgs84": footprint_wgs84,
        "driver": dataset.driver,
        "nodata_value": dataset.nodata,
    }


def _estimate_nodata_percentage(dataset: rasterio.io.DatasetReader, sample_size: int = 512) -> float:
    """
    Sample a downscaled read of band 1 to estimate % of nodata/zero pixels
    without reading the full (potentially huge) raster into memory.
    """
    try:
        band1 = dataset.read(
            1,
            out_shape=(min(sample_size, dataset.height), min(sample_size, dataset.width)),
        )
    except Exception:
        return 0.0

    if dataset.nodata is not None:
        nodata_mask = band1 == dataset.nodata
    else:
        nodata_mask = band1 == 0

    total = nodata_mask.size
    if total == 0:
        return 0.0
    return float(np.count_nonzero(nodata_mask)) / total * 100.0
