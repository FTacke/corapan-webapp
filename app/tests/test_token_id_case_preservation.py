"""Test that token_id preserves case through the entire pipeline.

Ensures that token IDs like 'VENb379fcc75' remain exactly as-is,
not lowercased to 'venb379fcc75'.
"""

from src.app.services.blacklab_search import _hit_to_canonical


def test_token_id_preserves_uppercase():
    """Token ID with uppercase letters should remain unchanged."""
    hit = {
        "docPid": "test",
        "match": {
            "word": ["test"],
            "tokid": ["VENb379fcc75"],  # Mixed case
        },
    }

    mapped = _hit_to_canonical(hit)
    assert mapped["token_id"] == "VENb379fcc75", (
        f"Expected 'VENb379fcc75' but got '{mapped['token_id']}' - "
        "token_id must preserve case"
    )


def test_token_id_preserves_various_cases():
    """Test various case patterns in token IDs."""
    test_cases = [
        "ESP8c0a4e499",
        "VENb379fcc75",
        "ARGTEST123",
        "mixedCase456",
    ]

    for token_id in test_cases:
        hit = {
            "docPid": "test",
            "match": {
                "word": ["test"],
                "tokid": [token_id],
            },
        }

        mapped = _hit_to_canonical(hit)
        assert mapped["token_id"] == token_id, (
            f"Token ID '{token_id}' was transformed to '{mapped['token_id']}' - "
            "case must be preserved exactly"
        )
