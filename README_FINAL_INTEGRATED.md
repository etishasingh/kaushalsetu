# KaushalSetu AI — Final Integrated Project

This package combines the original KaushalSetu recommendation backend with the redesigned frontend, career-detail video explorer, and the supplied voice/YouTube integration packages.

## One-command / one-click run

### Windows
Double-click:

`run_kaushalsetu.bat`

Then open `http://127.0.0.1:8000` if it does not open automatically.

### Terminal
```bash
pip install -r requirements.txt
python -X utf8 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The main site is served directly by FastAPI at `/`.

## Main user flow

`Home → Let's Get Started → Learner/Family Intake → 5 Recommendations → Career Detail → Career Journey Videos → AI Counsellor`

The chat page also supports browser speech-to-text and read-aloud responses where the browser exposes the Web Speech API.

## Integrated API routes

- `GET /health` — backend health and model/data status
- `POST /api/recommendations` — personalized top-K career recommendations
- `GET /api/careers` — catalogue browsing
- `GET /api/careers/{qualification_id}` — detailed career evidence
- `GET /api/careers/{qualification_id}/videos` — cached/live career-journey videos
- `POST /api/counsellor/chat` — evidence-grounded counselling
- `GET /voice` — bundled standalone voice chatbot page
- `GET /youtube-explorer` — bundled standalone YouTube explorer

## YouTube integration

`youtube_recommendation.py` remains a standalone engine as well as being used by the FastAPI `/videos` endpoint. It supports the supplied verified cache, four journey categories, relevance scoring, anti-clickbait filtering, and optional YouTube Data API v3 refresh.

Set `YOUTUBE_API_KEY` only if live discovery is wanted. The site works with the supplied local cache without that key.

## Voice integration

The supplied `voice_model/` directory is retained for standalone use and compatibility. The main website does not start a second port-8000 server; its chat uses the main FastAPI backend, while browser STT/TTS is available directly inside the redesigned chat UI.

For the original standalone voice server, see `voice_model/README.md`.

## Gemini note

The existing counsellor service recognizes `GEMINI_API_KEY` / `OPENAI_API_KEY` environment variables and keeps a deterministic grounded fallback. The current project source does **not** contain a completed external Gemini generation call; adding the key alone therefore does not magically create a live Gemini request. The grounded counsellor remains usable without an API key.

## Data and model artifacts

The original government/evidence datasets and trained retrieval artifacts are preserved. `integrations/dense_embeddings.npy` is the supplied copy of the same dense embedding artifact already used under `outputs/models/`.

## Useful standalone tools

- `youtube_career_videos.html` — standalone video explorer
- `run_youtube_recommendation.bat` — standalone YouTube CLI launcher
- `voice_model/kaushalsetu_voice_chatbot.html` — standalone voice UI
- `voice_model/run_voice_chatbot.bat` — standalone voice launcher
