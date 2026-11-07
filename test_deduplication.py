
"""
test_deduplication.py

Tests exact duplicate removal and Hindsight recall handling.
Uses mocked responses; no real memory is stored.
"""

from types import SimpleNamespace
from unittest.mock import patch

from memory import (
    _deduplicate_memories,
    find_similar,
    close_client
)


def test_exact_duplicates_removed():

    memories = [
        "Payment database timeout",
        "payment database timeout",
        "Redis authentication failure",
        "Payment database timeout"
    ]

    result = _deduplicate_memories(memories)

    assert result == [
        "Payment database timeout",
        "Redis authentication failure"
    ]

    print("PASS: Exact duplicates removed.")


def test_different_facts_preserved():

    memories = [
        "Database connection pool exhausted.",
        "Database query missing an index.",
        "Database connection leak detected."
    ]

    result = _deduplicate_memories(memories)

    assert len(result) == 3

    print("PASS: Different incident facts preserved.")


def test_original_text_and_order_preserved():

    memories = [
        "  PAYMENT TIMEOUT  ",
        "Redis connection failed",
        "payment timeout"
    ]

    result = _deduplicate_memories(memories)

    assert result == [
        "PAYMENT TIMEOUT",
        "Redis connection failed"
    ]

    print("PASS: Original text and order preserved.")


def test_empty_and_invalid_memories_ignored():

    memories = [
        "Payment timeout",
        "",
        "   ",
        None,
        123,
        "Redis failure"
    ]

    result = _deduplicate_memories(memories)

    assert result == [
        "Payment timeout",
        "Redis failure"
    ]

    print("PASS: Empty and invalid memories ignored.")


def test_find_similar_applies_limit():

    fake_results = SimpleNamespace(
        results=[
            SimpleNamespace(text="Payment timeout"),
            SimpleNamespace(text="payment timeout"),
            SimpleNamespace(text="Redis failure"),
            SimpleNamespace(text="Database failure")
        ]
    )

    with patch(
        "memory.client.recall",
        return_value=fake_results
    ) as mock_recall:

        result = find_similar(
            "Payment service error",
            limit=2
        )

        assert len(result) == 2
        assert result == [
            "Payment timeout",
            "Redis failure"
        ]

        mock_recall.assert_called_once()

    print("PASS: Recall deduplication and result limit work.")


def run_tests():

    print("\n========== DEDUPLICATION TESTS ==========\n")

    test_exact_duplicates_removed()
    test_different_facts_preserved()
    test_original_text_and_order_preserved()
    test_empty_and_invalid_memories_ignored()
    test_find_similar_applies_limit()

    print("\nAll deduplication tests passed!")
    print("\n=========================================")


if __name__ == "__main__":

    try:
        run_tests()

    finally:
        close_client()
        print("\nHindsight client closed.")
