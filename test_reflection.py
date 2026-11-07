
"""
test_reflection.py

Tests Hindsight reflection integration using mocked responses.
No real Hindsight API calls are made.
"""

from types import SimpleNamespace
from unittest.mock import patch

from memory import learned_patterns, BANK_ID, close_client


def test_reflection_returns_text():

    fake_response = SimpleNamespace(
        text="Historical evidence shows three different root causes."
    )

    with patch(
        "memory.client.reflect",
        return_value=fake_response
    ) as mock_reflect:

        result = learned_patterns(
            "  Analyse previous payment incidents.  "
        )

        assert result == (
            "Historical evidence shows three different root causes."
        )

        mock_reflect.assert_called_once_with(
            bank_id=BANK_ID,
            query="Analyse previous payment incidents.",
            apply_all_directives=True
        )

    print("PASS: Reflection returned the expected text.")
    print("PASS: All active directives were requested.")


def test_reflection_fallback():

    fake_response = SimpleNamespace(text=None)

    with patch(
        "memory.client.reflect",
        return_value=fake_response
    ):

        result = learned_patterns("Analyse database incidents.")

        assert result == str(fake_response)

    print("PASS: Reflection fallback works when text is unavailable.")


def test_reflection_rejects_invalid_input():

    try:
        learned_patterns("")

    except ValueError:
        print("PASS: Empty reflection question rejected.")

    else:
        raise AssertionError("Expected ValueError.")


def run_tests():

    print("\n========== REFLECTION TESTS ==========\n")

    test_reflection_returns_text()
    test_reflection_fallback()
    test_reflection_rejects_invalid_input()

    print("\nAll reflection tests passed!")
    print("\n=======================================")


if __name__ == "__main__":

    try:
        run_tests()

    finally:
        close_client()
        print("\nHindsight client closed.")
