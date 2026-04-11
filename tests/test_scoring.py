from datetime import datetime, timezone

from app.models.schemas import RetrievedSource
from app.scoring.engine import DeterministicScoringEngine


def test_scoring_false_claim_with_fact_check() -> None:
    engine = DeterministicScoringEngine()
    sources = [
        RetrievedSource(
            source_id="1",
            source_name="Reuters Fact Check",
            source_type="fact_check",
            title="Claim is false",
            url="https://www.reuters.com/fact-check/example",
            verdict_label="False",
            agreement="contradicts",
            published_at=datetime.now(timezone.utc),
            credibility_weight=0.95,
        )
    ]
    classification, score, confidence, features = engine.score(sources)
    assert classification == "false"
    assert score <= 3
    assert confidence > 0.2
    assert features.fact_check_match_score < 0


def test_scoring_insufficient_evidence() -> None:
    engine = DeterministicScoringEngine()
    classification, score, confidence, _ = engine.score([])
    assert classification == "insufficient_evidence"
    assert 1 <= score <= 10
    assert 0 <= confidence <= 1
