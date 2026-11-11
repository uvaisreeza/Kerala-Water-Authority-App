# KWA Notebook Scanner — GitHub Pages + Render

This package preserves your original frontend, entry table, calculations, reagent factors and report. It replaces unavailable `claude.use(...)` calls with a Render API backend.

## Required: Anthropic API key
A Claude chat subscription does not automatically include API usage. Create an API key at https://console.anthropic.com/ and enable API billing if needed. Never put the key in the HTML or public GitHub repository.

## GitHub Pages
1. Copy `frontend/index.html` from this ZIP into your repository root and name it `index.html`.
2. Commit and push; enable Settings → Pages if needed.

## Render backend
1. Deploy the `backend` folder as a Render Web Service. Set Root Directory to `backend`.
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables: `ANTHROPIC_API_KEY` (secret), `ANTHROPIC_MODEL=claude-sonnet-4-6`, `CORS_ORIGINS=*` for initial testing.
5. Deploy and verify `https://YOUR-SERVICE.onrender.com/health` returns `{"status":"healthy"}`.

## Connect the frontend
In `index.html`, replace `PASTE_YOUR_RENDER_BACKEND_URL_HERE` in `API_BASE` with your Render URL (no `/api/scan` suffix). Commit and push.

## Test
Upload one photo or both notebook pages together. Review yellow/uncertain cells and all lab results manually. Excel now downloads directly in the browser.

Up to 4 photos per scan, max 7 MB each. Anthropic API use is billed separately. Render free services may sleep when idle. CORS `*` is for initial testing only; restrict it to your GitHub Pages origin after setup. CORS is not authentication. Handwriting extraction is not guaranteed.
