from app.core.config import Settings


def test_get_nim_model_candidates_deduplicates_and_splits() -> None:
    settings = Settings(
        nim_model="mistralai/mistral-small-3.1-24b-instruct-2503",
        nim_fallback_models=(
            "abacusai/dracarys-llama-3.1-70b-instruct, "
            "01-ai/yi-large, mistralai/mistral-small-3.1-24b-instruct-2503"
        ),
    )

    assert settings.get_nim_model_candidates() == [
        "mistralai/mistral-small-3.1-24b-instruct-2503",
        "abacusai/dracarys-llama-3.1-70b-instruct",
        "01-ai/yi-large",
    ]
