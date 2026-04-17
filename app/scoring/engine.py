from __future__ import annotations

from datetime import datetime, timezone

from app.models.schemas import ClassificationLabel, EvidenceFeatures, RetrievedSource


class DeterministicScoringEngine:
    def score(
        self, retrieved_sources: list[RetrievedSource]
    ) -> tuple[ClassificationLabel, int, float, EvidenceFeatures]:
        fact_check_match_score = self._fact_check_match_score(retrieved_sources)
        support_score = self._support_score(retrieved_sources)
        contradiction_score = self._contradiction_score(retrieved_sources)
        source_credibility_score = self._credibility_score(retrieved_sources)
        recency_score = self._recency_score(retrieved_sources)
        coverage_score = min(1.0, len(retrieved_sources) / 5)
        uncertainty_penalty = self._uncertainty_penalty(retrieved_sources)

        has_fact_checks = any(s.source_type == "fact_check" for s in retrieved_sources)
        if has_fact_checks:
            # Fact-check sources are authoritative — give them dominant weight.
            raw_score = (
                0.40 * fact_check_match_score
                + 0.20 * support_score
                + 0.15 * source_credibility_score
                + 0.10 * recency_score
                + 0.10 * coverage_score
                - 0.25 * contradiction_score
                - 0.15 * uncertainty_penalty
            )
        else:
            # No fact-checks: support_score is the dominant signal.
            # Quality metrics (credibility, recency, coverage) describe the
            # *sources*, not the *claim* — they must not compensate for missing
            # evidence.  A small baseline deduction keeps unverified headlines
            # below neutral even when retrieved sources look reputable.
            raw_score = (
                0.70 * support_score
                + 0.10 * source_credibility_score
                + 0.08 * recency_score
                + 0.08 * coverage_score
                - 0.20 * contradiction_score
                - 0.10 * uncertainty_penalty
                - 0.05
            )
        reliability_score = max(1, min(10, round(5 + raw_score * 5)))
        classification = self._classify(
            reliability_score=reliability_score,
            support_score=support_score,
            contradiction_score=contradiction_score,
            fact_check_match_score=fact_check_match_score,
            evidence_count=len(retrieved_sources),
        )
        # When fact-checks are present they are the strongest confidence signal;
        # otherwise lean on support_score so confidence also rises for confirmed
        # headlines that have no dedicated fact-check entry.
        confidence_signal = abs(fact_check_match_score) if has_fact_checks else support_score
        confidence = max(
            0.05,
            min(
                0.99,
                0.25
                + 0.3 * coverage_score
                + 0.2 * source_credibility_score
                + 0.2 * confidence_signal
                - 0.25 * uncertainty_penalty,
            ),
        )
        features = EvidenceFeatures(
            fact_check_match_score=fact_check_match_score,
            support_score=support_score,
            contradiction_score=contradiction_score,
            source_credibility_score=source_credibility_score,
            recency_score=recency_score,
            coverage_score=coverage_score,
            uncertainty_penalty=uncertainty_penalty,
        )
        return classification, reliability_score, confidence, features

    @staticmethod
    def _fact_check_match_score(retrieved_sources: list[RetrievedSource]) -> float:
        fact_checks = [item for item in retrieved_sources if item.source_type == "fact_check"]
        if not fact_checks:
            return 0.0
        score = 0.0
        for item in fact_checks:
            if item.agreement == "supports":
                score += 1.0
            elif item.agreement == "contradicts":
                score -= 1.0
        return max(-1.0, min(1.0, score / max(1, len(fact_checks))))

    @staticmethod
    def _support_score(retrieved_sources: list[RetrievedSource]) -> float:
        if not retrieved_sources:
            return 0.0
        total = 0.0
        for item in retrieved_sources:
            if item.agreement == "supports":
                total += 1.0
            elif item.agreement == "related":
                # Only credit "related" sources when their content substantially
                # overlaps the claim (sim ≥ 0.4).  Generic articles that merely
                # share a keyword (e.g. "China" / "India") have sim ≈ 0.2–0.3
                # and contribute nothing, preventing topic-adjacent noise from
                # inflating scores for unverifiable headlines.
                sim = min(1.0, item.similarity_score or 0.0)
                total += max(0.0, (sim - 0.4) * 2.5)
        return min(1.0, total / len(retrieved_sources))

    @staticmethod
    def _contradiction_score(retrieved_sources: list[RetrievedSource]) -> float:
        if not retrieved_sources:
            return 1.0
        contradictions = sum(1 for item in retrieved_sources if item.agreement == "contradicts")
        return min(1.0, contradictions / len(retrieved_sources))

    @staticmethod
    def _credibility_score(retrieved_sources: list[RetrievedSource]) -> float:
        if not retrieved_sources:
            return 0.0
        return sum(item.credibility_weight for item in retrieved_sources) / len(retrieved_sources)

    @staticmethod
    def _recency_score(retrieved_sources: list[RetrievedSource]) -> float:
        now = datetime.now(timezone.utc)
        scored = []
        for item in retrieved_sources:
            if not item.published_at:
                continue
            age_days = max(0, (now - item.published_at.astimezone(timezone.utc)).days)
            scored.append(max(0.1, 1 - age_days / 365))
        return sum(scored) / len(scored) if scored else 0.3

    @staticmethod
    def _uncertainty_penalty(retrieved_sources: list[RetrievedSource]) -> float:
        if not retrieved_sources:
            return 1.0
        # Only penalise sources with NO topical connection to the claim.
        # "related" sources discuss the same event — penalising them as uncertain
        # wrongly drags down scores for confirmed news with only web sources.
        unknowns = sum(1 for item in retrieved_sources if item.agreement == "unknown")
        contradictions = sum(1 for item in retrieved_sources if item.agreement == "contradicts")
        return min(1.0, (0.6 * unknowns + contradictions) / len(retrieved_sources))

    @staticmethod
    def _classify(
        *,
        reliability_score: int,
        support_score: float,
        contradiction_score: float,
        fact_check_match_score: float,
        evidence_count: int,
    ) -> ClassificationLabel:
        if evidence_count == 0:
            return "insufficient_evidence"
        if contradiction_score >= 0.4 or fact_check_match_score <= -0.5:
            return "false" if reliability_score <= 3 else "misleading"
        if support_score >= 0.5 and reliability_score >= 7:
            return "true"
        if evidence_count < 2 or reliability_score <= 5:
            return "unverifiable"
        return "misleading"
