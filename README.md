# Multilingual Misinformation Detection Agent

## Overview

This project is a Python-only backend that analyzes a news headline and estimates how reliable it is on a `1-10` scale.

It is built as an evidence-first misinformation analysis system:
- input is a single headline string
- the backend detects the language
- the headline is normalized into a claim
- fact-check and web evidence are retrieved
- NVIDIA NIM is used for planning, query refinement, and evidence summarization
- deterministic backend logic produces the final score and classification

The LLM does not decide truth on its own. It only helps orchestrate retrieval and summarize grounded evidence.

## What The Backend Returns

For each headline, the API returns structured JSON with:
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

For lower-confidence or questionable reports, the response can also include:
- `actual_news_headline`
- `actual_news_description`

## Core Stack

- Python
- FastAPI
- NVIDIA NIM for orchestration
- Google Fact Check Tools API
- Tavily for web evidence search
- Chroma as the local vector store

## High-Level Flow

1. Client sends a headline to `POST /api/v1/analyze-headline`
2. Backend detects language and normalizes the claim
3. NIM generates a retrieval plan
4. Evidence is retrieved from fact-check and web sources
5. Results are deduplicated, ranked, and stored in the vector layer
6. NIM summarizes the evidence
7. Deterministic scoring logic assigns the final reliability score and class

## Project Structure

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

## Required Project Path

This project is expected to live at:

`C:\Codes\Projects\Multilingual Misinformation Detection Agent`

## Environment Variables

Create a `.env` file in the project root and set:

```env
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_API_KEY=your_nvidia_key
NIM_MODEL=mistralai/mistral-small-3.1-24b-instruct-2503
NIM_FALLBACK_MODELS=abacusai/dracarys-llama-3.1-70b-instruct,01-ai/yi-large

GOOGLE_FACT_CHECK_API_KEY=your_google_key
TAVILY_API_KEY=your_tavily_key
```

## Run Locally

```powershell
Set-Location "C:\Codes\Projects\Multilingual Misinformation Detection Agent"
uvicorn app.main:app --reload
```

Open:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Example Request

```json
{
  "headline": "Government confirms drinking coffee cures all cancers"
}
```

## Current Status

- Backend MVP implemented
- Tests passing
- Primary model configured through NVIDIA NIM
- Automatic fallback to alternate NIM models supported
- Google Fact Check and Tavily integrated
- Local vector persistence enabled through Chroma

## Notes

- Input is a headline string, not a news article URL
- Fact-check retrieval is prioritized over generic web search
- Scoring is deterministic and evidence-based
- Snopes and PolitiFact are planned as future adapters
