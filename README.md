# Multilingual Misinformation Detection Agent

## Live Demo

- App: [https://multilingual-misinformation-detection.onrender.com/](https://multilingual-misinformation-detection.onrender.com/)
- Repository: [https://github.com/Anonymous-Killer/Multilingual-MIsinformation-Detection](https://github.com/Anonymous-Killer/Multilingual-MIsinformation-Detection)

## Overview

This project is a full-stack misinformation analysis application that takes a news headline, investigates it with retrieved evidence, and returns a structured reliability assessment.

The system is designed to be evidence-first:
- the input is a single headline string
- the backend detects the language
- the headline is normalized into a claim
- fact-check and web evidence are retrieved
- an NVIDIA NIM orchestrator helps plan retrieval and summarize evidence
- deterministic scoring logic produces the final reliability score

The LLM is not allowed to decide truth on intuition alone. It is restricted to planning, retrieval coordination, and grounded summarization.

## What The App Does

Given a headline, the app:
1. detects its language
2. normalizes it into a cleaner claim
3. retrieves fact-check and web evidence
4. ranks and deduplicates sources
5. summarizes the evidence
6. returns a reliability score and classification

The API returns structured JSON including:
- `input_headline`
- `detected_language`
- `normalized_claim`
- `classification`
- `retrieved_sources`
- `evidence_summary`
- `reliability_score`
- `confidence`
- `reasoning_trace_summary`
- `limitations`
- `uncertainty_flags`
- `actual_news_headline`
- `actual_news_description`

## Current Product State

The project is now deployed as a working full-stack app:
- FastAPI backend on Render
- React + Vite frontend on Render
- frontend calls the deployed backend through `VITE_API_BASE_URL`
- backend includes CORS configuration for the deployed frontend

The scoring logic has also been tightened to handle edge cases better:
- absurd unsupported headlines can now fall to `0/10`
- broad entity overlap alone should not keep unsupported claims near neutral
- low-score explanatory cards now prefer non-fact-check event coverage over fact-check titles when possible

## Tech Stack

### Backend

- Python
- FastAPI
- httpx
- Pydantic
- NVIDIA NIM
- Google Fact Check Tools API
- Tavily
- Chroma

### Frontend

- React
- Vite
- TypeScript
- React Router
- Tailwind CSS
- Lucide React

## Architecture

### Backend modules

- `app/api/` FastAPI routes
- `app/core/` configuration and logging
- `app/models/` request and response schemas
- `app/services/` pipeline logic
- `app/adapters/` external API adapters
- `app/orchestrators/` NVIDIA NIM orchestration logic
- `app/retrieval/` retrieval and ranking
- `app/scoring/` deterministic scoring engine
- `app/vectorstore/` embeddings and Chroma integration
- `tests/` backend tests

### Frontend modules

- `frontend/src/api/` API client
- `frontend/src/components/` UI components
- `frontend/src/hooks/` frontend hooks
- `frontend/src/pages/` route-level pages
- `frontend/src/types/` frontend response types

## High-Level Flow

1. The frontend sends a headline to `POST /api/v1/analyze-headline`
2. The backend detects language and normalizes the claim
3. NVIDIA NIM generates a retrieval plan
4. Evidence is pulled from:
   - Google Fact Check Tools API
   - Tavily web search
   - the local Chroma-backed vector layer
5. Results are deduplicated and ranked
6. NIM summarizes the evidence
7. Deterministic logic assigns the final score and classification
8. The frontend renders the result, sources, confidence, and uncertainty flags

## Local Development

Project root:

`C:\Codes\Projects\Multilingual Misinformation Detection Agent`

### Backend setup

Create a `.env` file in the project root with values such as:

```env
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_API_KEY=your_nvidia_key
NIM_MODEL=mistralai/mistral-small-3.1-24b-instruct-2503
NIM_FALLBACK_MODELS=abacusai/dracarys-llama-3.1-70b-instruct,01-ai/yi-large

GOOGLE_FACT_CHECK_API_KEY=your_google_key
TAVILY_API_KEY=your_tavily_key
```

Run the backend:

```powershell
Set-Location "C:\Codes\Projects\Multilingual Misinformation Detection Agent"
uvicorn app.main:app --reload
```

Backend docs:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Frontend setup

Run the frontend:

```powershell
Set-Location "C:\Codes\Projects\Multilingual Misinformation Detection Agent\frontend"
npm install
npm run dev
```

For local frontend-to-backend calls, the Vite dev server proxies `/api` to `http://localhost:8000`.

## Deployment Notes

### Render deployment split

The app is deployed as two Render services:
- backend: Render Web Service
- frontend: Render Static Site

### Backend deployment considerations

- backend uses `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Python version is pinned in Render for dependency compatibility
- CORS must allow the deployed frontend origin

### Frontend deployment considerations

- frontend root directory on Render is `frontend`
- build command is `npm run build`
- publish directory is `dist`
- `VITE_API_BASE_URL` points to the backend Render service

## Example Request

```json
{
  "headline": "Government confirms drinking coffee cures all cancers"
}
```

## Testing

Run backend tests:

```powershell
Set-Location "C:\Codes\Projects\Multilingual Misinformation Detection Agent"
pytest
```

## Notes

- Input is a headline string, not a news article URL
- Fact-check retrieval is prioritized over generic web search
- Scores are deterministic and evidence-based
- The vector layer currently uses local persistence
- Snopes and PolitiFact are still future adapter candidates rather than active integrations
