from app.modules.commerce.domain.access_policy import AccessPolicy


def test_free_local_documents_are_not_artificially_capped():
    p = AccessPolicy()
    assert p.free_local_personal_documents is None
    assert "local_document_library" in p.free_features


def test_premium_contains_expensive_value_features():
    p = AccessPolicy()
    assert "audio_summaries" in p.premium_features
    assert "adaptive_planning" in p.premium_features
    assert p.premium_ai_credits_per_cycle > p.free_ai_trial_credits
