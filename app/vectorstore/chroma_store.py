from __future__ import annotations

from typing import Any

import chromadb

from app.core.config import Settings
from app.models.schemas import RetrievedSource


class ChromaVectorStore:
    def __init__(self, settings: Settings):
        self._client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name
        )

    async def upsert(self, documents: list[RetrievedSource], embeddings: list[list[float]]) -> None:
        if not documents:
            return
        self._collection.upsert(
            ids=[document.source_id for document in documents],
            embeddings=embeddings,
            metadatas=[self._metadata(document) for document in documents],
            documents=[self._document_text(document) for document in documents],
        )

    async def search(self, query_embedding: list[float], k: int = 5) -> list[RetrievedSource]:
        results = self._collection.query(query_embeddings=[query_embedding], n_results=k)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        normalized: list[RetrievedSource] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            normalized.append(
                RetrievedSource(
                    source_id=metadata["source_id"],
                    source_name=metadata["source_name"],
                    source_type=metadata["source_type"],
                    title=metadata["title"],
                    url=metadata.get("url") or None,
                    language=metadata.get("language", "unknown"),
                    snippet=document,
                    claim_text=metadata.get("claim_text", ""),
                    verdict_label=metadata.get("verdict_label") or None,
                    credibility_weight=float(metadata.get("credibility_weight", 0.5)),
                    similarity_score=max(0.0, 1.0 - float(distance or 1.0)),
                    agreement=metadata.get("agreement", "unknown"),
                    metadata={"from_vector_store": True},
                )
            )
        return normalized

    @staticmethod
    def _document_text(document: RetrievedSource) -> str:
        return " ".join(filter(None, [document.title, document.snippet, document.claim_text]))

    @staticmethod
    def _metadata(document: RetrievedSource) -> dict[str, Any]:
        return {
            "source_id": document.source_id,
            "source_name": document.source_name,
            "source_type": document.source_type,
            "title": document.title,
            "url": str(document.url) if document.url else "",
            "language": document.language,
            "claim_text": document.claim_text,
            "verdict_label": document.verdict_label or "",
            "credibility_weight": document.credibility_weight,
            "agreement": document.agreement,
        }
