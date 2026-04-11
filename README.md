# Multilingual Misinformation Detection Agent

Python-only backend MVP for investigating a news headline, retrieving evidence, and returning a structured reliability assessment.

## Executive Summary

This backend takes a single headline, detects its language, normalizes the claim, retrieves fact-check and web evidence, summarizes that evidence with NVIDIA NIM, and returns a deterministic `1-10` reliability score. The model is never allowed to decide truth without evidence.

## Assumptions

- Project root is fixed to `C:\Codes\Projects\Multilingual Misinformation Detection Agent`
- FastAPI is the service layer only
- Mistral Small 3.1 24B Instruct via NVIDIA NIM is the primary orchestrator
- GLM-4.7 and Llama 3.1 Nemotron Nano 8B are pluggable stubs in the MVP
- Google Fact Check and Tavily are the live adapters in the MVP
- Snopes and PolitiFact are designed for later adapters, not scraped now

## Architecture

- FastAPI endpoint layer
- Language detection and claim normalization
- Pluggable NVIDIA NIM orchestrator interface
- Fact-check-first retrieval
- Tavily web evidence retrieval
- Local Chroma vector persistence
- Deterministic scoring engine
- Structured JSON response formatting

## NIM Model Comparison

- `Mistral Small 3.1 24B Instruct`: best current MVP default for reliable JSON planning and summarization
- `GLM-4.7`: strong future multilingual option, currently stubbed
- `Llama 3.1 Nemotron Nano 8B`: lower-cost fallback, currently stubbed

## Multilingual Recommendation

- MVP choice: native-language retrieval first with multilingual-friendly processing
- Future-proof choice: multilingual E5 or BGE multilingual embeddings plus a stronger reranker
- Translation is best kept as an optional aid, not the primary retrieval path

## Retrieval And Scoring

- Retrieve fact-check evidence first
- Expand with Tavily web search
- Store evidence in local Chroma for reuse
- Rank using source type, overlap, and source credibility
- Score deterministically from fact-check match, support, contradiction, credibility, recency, coverage, and uncertainty

## Project Structure

- `app/`
- `app/api/`
- `app/core/`
- `app/models/`
- `app/services/`
- `app/adapters/`
- `app/orchestrators/`
- `app/retrieval/`
- `app/scoring/`
- `app/vectorstore/`
- `tests/`
- `requirements.txt`
- `.env.example`
- `README.md`

## Setup On Windows

Use this exact path:

`C:\Codes\Projects\Multilingual Misinformation Detection Agent`

```powershell
Set-Location "C:\Codes\Projects\Multilingual Misinformation Detection Agent"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `.env` with:

- `NIM_API_KEY`
- `GOOGLE_FACT_CHECK_API_KEY`
- `TAVILY_API_KEY`

## Run

```powershell
Set-Location "C:\Codes\Projects\Multilingual Misinformation Detection Agent"
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Docs:

- [Swagger UI](http://127.0.0.1:8000/docs)

## Main Endpoint

`POST /api/v1/analyze-headline`

Request:

```json
{
  "headline": "Government confirms drinking coffee cures all cancers"
}
```

## Testing

```powershell
Set-Location "C:\Codes\Projects\Multilingual Misinformation Detection Agent"
.venv\Scripts\Activate.ps1
pytest
```

## Notes On Fact-Check Sources

- Google Fact Check Tools API is implemented
- Snopes and PolitiFact should be added via compliant adapters instead of brittle scraping
- Direct scraping is omitted because terms, HTML structure, and operational stability can change without notice
