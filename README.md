# PIXELNOVEL — Phase 1 Skeleton

AI-Based Uncertainty-Aware Super-Resolution of Sentinel-2 Imagery.
This is **Phase 1 of the roadmap**: product skeleton covering MVP-1 → MVP-3.

## What's working right now

- **MVP-1 — Upload**: drag-and-drop a Sentinel-2 GeoTIFF (`.tif`/`.tiff`) in the browser.
- **MVP-2 — Validation + metadata**: backend checks CRS, dimensions, band count,
  pixel resolution (flags anything that isn't ~10/20/60 m), and estimated no-data
  percentage. Errors block the scene; warnings are shown but don't block.
- **MVP-3 — Map preview**: a quicklook PNG (percentile-stretched, bands 4/3/2 if
  available) is generated server-side and overlaid on a Leaflet map at the
  scene's real-world footprint (reprojected to WGS84).

Everything after this (preprocessing/tiling, SR model integration, uncertainty,
feature extraction, change detection, full GIS dashboard) is **not built yet** —
that's Phase 2 onward. See `29.` in the original product plan for the full roadmap.

## Project structure

```
PIXELNOVEL/
├── backend/
│   ├── main.py                    # FastAPI app entrypoint
│   ├── api/routes.py              # upload / validate / preview / list endpoints
│   ├── geospatial/
│   │   ├── validation.py          # MVP-2: GeoTIFF validation rules
│   │   └── preview.py             # MVP-3: PNG quicklook generation
│   ├── preprocessing/              # (empty — Phase 2)
│   ├── super_resolution/           # (empty — Phase 3)
│   ├── uncertainty/                 # (empty — Phase 4)
│   └── feature_extraction/          # (empty — Phase 5)
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── UploadPanel.jsx
│       │   ├── MetadataPanel.jsx
│       │   └── ScenePreviewMap.jsx
│       └── services/api.js
├── data/{input,processed,output}   # uploaded + generated files land here
├── models/super_resolution/         # (empty — for SR model weights, Phase 3)
└── tests/
```

## Running it locally

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/api/health`

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend expects the backend at
`http://localhost:8000` (hardcoded in `src/services/api.js` — move to an env
var before deploying anywhere real).

## API endpoints (Phase 1)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/scenes/upload` | Upload + validate a GeoTIFF, returns metadata |
| GET | `/api/scenes/{scene_id}` | Fetch stored scene record |
| GET | `/api/scenes/{scene_id}/preview` | PNG quicklook for map overlay |
| GET | `/api/scenes` | List uploaded scenes |

Note: scene storage is **in-memory** (`SCENES` dict in `api/routes.py`) for
MVP speed. It resets on server restart. Move to PostgreSQL when you get to
Phase 6+ (temporal comparison needs persistent scene records anyway).

## What was actually tested

Both the validation logic and the preview generation were run end-to-end
against a synthetic 4-band, 10 m, UTM-projected GeoTIFF (300×300 px) —
not just written and assumed to work. The FastAPI server was started and
hit with real HTTP requests (`/api/health`, `/api/scenes/upload`,
`/api/scenes/{id}/preview`) and returned correct JSON/PNG responses. The
frontend was installed and built successfully with `npm run build`.

What was **not** tested: real Sentinel-2 L1C/L2A `.SAFE`/`.jp2` products
(only a synthetic GeoTIFF), large scenes (tiling doesn't exist yet — that's
Phase 2), and the full drag-and-drop UI in an actual browser (no headless
browser in this environment — recommend you click through it yourself once
you run it locally).

## Deploying to Render (free tier)

`render.yaml` at the repo root defines both services as a Blueprint:

- **pixelnovel-backend** — Python web service (FastAPI/uvicorn)
- **pixelnovel-frontend** — static site (Vite build output)

Steps:
1. Push this repo to GitHub.
2. In Render: New → Blueprint → point at the repo. It reads `render.yaml`
   and creates both services.
3. After the backend deploys, copy its URL (e.g.
   `https://pixelnovel-backend.onrender.com`) and set it as `VITE_API_URL`
   (with `/api` appended) on the **frontend** service's env vars, then
   redeploy the frontend.
4. Set `FRONTEND_URL` on the **backend** service to the frontend's URL, so
   CORS allows it, then redeploy the backend.

Free-tier note: services spin down after ~15 min of inactivity and take
30-50s to wake up on the next request — expected for a demo, not an
always-on production issue.

## Next steps (Phase 2 — per the roadmap)

1. Cloud/shadow/no-data masking (currently only a crude no-data % estimate).
2. Tiling for large scenes (`MAX_DIMENSION_PX` currently just warns).
3. Normalization/band alignment prep for the SR model.

Then Phase 3: integrate a real SR baseline (SEN2SR or SwinIR) — see the
original product plan's "AI Super-Resolution Strategy" section.
