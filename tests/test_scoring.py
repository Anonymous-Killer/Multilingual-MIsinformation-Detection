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
    assert 0 <= score <= 10
    assert 0 <= confidence <= 1


def test_absurd_unsupported_claim_stays_at_floor() -> None:
    engine = DeterministicScoringEngine()
    sources = [
        RetrievedSource(
            source_id="1",
            source_name="News One",
            source_type="web_search",
            title="Donald Trump campaign update",
            url="https://example.com/news-one",
            snippet="Donald Trump spoke at a campaign event in Florida.",
            agreement="related",
            similarity_score=0.72,
            credibility_weight=0.85,
        ),
        RetrievedSource(
            source_id="2",
            source_name="News Two",
            source_type="web_search",
            title="Donald Trump attends rally",
            url="https://example.com/news-two",
            snippet="Donald Trump addressed supporters in a televised rally.",
            agreement="related",
            similarity_score=0.75,
            credibility_weight=0.8,
        ),
        RetrievedSource(
            source_id="3",
            source_name="News Three",
            source_type="web_search",
            title="Donald Trump latest appearance",
            url="https://example.com/news-three",
            snippet="Coverage of Donald Trump continues ahead of the election.",
            agreement="related",
            similarity_score=0.7,
            credibility_weight=0.78,
        ),
    ]
    classification, score, confidence, _ = engine.score(sources)
    assert classification in {"unverifiable", "insufficient_evidence", "misleading"}
    assert score <= 1
    assert 0 <= confidence <= 1
