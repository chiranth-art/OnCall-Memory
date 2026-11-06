
"""
test_outcome_feedback.py

Mock-based tests for Hindsight outcome feedback.
These tests do not write to the real Hindsight bank.
"""

from unittest.mock import patch

from memory import save_outcome, BANK_ID


def test_successful_outcome():
    """Verify that successful fixes are stored correctly."""

    with patch("memory.client.retain") as mock_retain:

        save_outcome(
            incident_id="INC-TEST-001",
            outcome="Increasing the connection pool resolved the timeout.",
            worked=True
        )

        mock_retain.assert_called_once()

        data = mock_retain.call_args.kwargs

        assert data["bank_id"] == BANK_ID
        assert "INC-TEST-001" in data["content"]
        assert "the fix WORKED" in data["content"]
        assert "increasing the connection pool" in data["content"].lower()
        assert data["context"] == "fix outcome feedback"

    print("PASS: Successful outcome stored correctly.")


def test_failed_outcome():
    """Verify that failed fixes are stored correctly."""

    with patch("memory.client.retain") as mock_retain:

        save_outcome(
            incident_id="INC-TEST-002",
            outcome="Restarting the service did not resolve the issue.",
            worked=False
        )

        mock_retain.assert_called_once()

        data = mock_retain.call_args.kwargs

        assert "INC-TEST-002" in data["content"]
        assert "the fix did NOT work" in data["content"]
        assert "Restarting the service" in data["content"]

    print("PASS: Failed outcome stored correctly.")


def test_unspecified_outcome():
    """Verify that unspecified results are not treated as success."""

    with patch("memory.client.retain") as mock_retain:

        save_outcome(
            incident_id="INC-TEST-003",
            outcome="The engineer attempted a database restart.",
            worked=None
        )

        mock_retain.assert_called_once()

        data = mock_retain.call_args.kwargs

        assert "Result: not specified" in data["content"]
        assert "the fix WORKED" not in data["content"]
        assert "the fix did NOT work" not in data["content"]

    print("PASS: Unspecified outcome handled correctly.")


def test_outcome_with_date():
    """Verify that an optional date is passed to Hindsight."""

    with patch("memory.client.retain") as mock_retain:

        save_outcome(
            incident_id="INC-TEST-004",
            outcome="Database index addition resolved the issue.",
            worked=True,
            date="2026-11-05"
        )

        data = mock_retain.call_args.kwargs

        assert data["timestamp"] == "2026-11-05"

    print("PASS: Optional date passed correctly.")


def run_tests():

    print("\n========== OUTCOME FEEDBACK TESTS ==========\n")

    test_successful_outcome()
    test_failed_outcome()
    test_unspecified_outcome()
    test_outcome_with_date()

    print("\nAll outcome feedback tests passed!")
    print("\n============================================")


if __name__ == "__main__":

    try:
        run_tests()

    finally:
        from memory import close_client
        close_client()
        print("\nHindsight client closed.")
