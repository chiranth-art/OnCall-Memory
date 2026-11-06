"""
test_outcome_feedback.py

Mock-based tests for the updated outcome feedback function.
No real Hindsight writes are performed.
"""

from unittest.mock import patch

from memory import save_outcome, BANK_ID, close_client


def test_successful_outcome():
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
        assert "Fix worked: True" in data["content"]
        assert "increasing the connection pool" in data["content"].lower()
        assert data["context"] == "fix outcome feedback"

    print("PASS: Successful outcome stored correctly.")


def test_failed_outcome():
    with patch("memory.client.retain") as mock_retain:
        save_outcome(
            incident_id="INC-TEST-002",
            outcome="Restarting the service did not resolve the issue.",
            worked=False
        )

        mock_retain.assert_called_once()
        data = mock_retain.call_args.kwargs

        assert "INC-TEST-002" in data["content"]
        assert "Fix worked: False" in data["content"]
        assert "Restarting the service" in data["content"]

    print("PASS: Failed outcome stored correctly.")


def test_unspecified_outcome():
    with patch("memory.client.retain") as mock_retain:
        save_outcome(
            incident_id="INC-TEST-003",
            outcome="The engineer attempted a database restart.",
            worked=None
        )

        mock_retain.assert_called_once()
        data = mock_retain.call_args.kwargs

        assert "Fix worked: None" in data["content"]
        assert "Fix worked: True" not in data["content"]
        assert "Fix worked: False" not in data["content"]

    print("PASS: Unspecified outcome handled correctly.")


def run_tests():
    print("\n========== OUTCOME FEEDBACK TESTS ==========\n")

    test_successful_outcome()
    test_failed_outcome()
    test_unspecified_outcome()

    print("\nAll outcome feedback tests passed!")
    print("\n============================================")


if __name__ == "__main__":
    try:
        run_tests()
    finally:
        close_client()
        print("\nHindsight client closed.")
