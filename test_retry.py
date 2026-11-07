
"""
test_retry.py

Tests the retry mechanism without making real API calls.
"""

from unittest.mock import Mock, patch

from memory import _retry, close_client


def test_retry_succeeds_after_failures():

    operation = Mock(
        side_effect=[
            ConnectionError("Temporary network failure"),
            TimeoutError("Temporary timeout"),
            "Success"
        ]
    )

    with patch("memory.time.sleep") as mock_sleep:

        result = _retry(operation, attempts=3, delay=1.5)

        assert result == "Success"
        assert operation.call_count == 3
        assert mock_sleep.call_count == 2

        delays = [
            call.args[0]
            for call in mock_sleep.call_args_list
        ]

        assert delays == [1.5, 3.0]

    print("PASS: Retry succeeded after two failures.")


def test_retry_exhausts_attempts():

    operation = Mock(
        side_effect=ConnectionError("Service unavailable")
    )

    with patch("memory.time.sleep") as mock_sleep:

        try:
            _retry(operation, attempts=3, delay=1.5)

        except ConnectionError as error:
            assert str(error) == "Service unavailable"

        else:
            raise AssertionError("Expected ConnectionError.")

        assert operation.call_count == 3
        assert mock_sleep.call_count == 2

    print("PASS: Final exception raised after three attempts.")


def test_invalid_attempts():

    try:
        _retry(lambda: "Success", attempts=0)

    except ValueError:
        print("PASS: Invalid retry count rejected.")

    else:
        raise AssertionError("Expected ValueError.")


def test_invalid_delay():

    try:
        _retry(lambda: "Success", delay=-1)

    except ValueError:
        print("PASS: Invalid retry delay rejected.")

    else:
        raise AssertionError("Expected ValueError.")


def run_tests():

    print("\n========== RETRY TESTS ==========\n")

    test_retry_succeeds_after_failures()
    test_retry_exhausts_attempts()
    test_invalid_attempts()
    test_invalid_delay()

    print("\nAll retry tests passed!")
    print("\n=================================")


if __name__ == "__main__":

    try:
        run_tests()

    finally:
        close_client()
        print("\nHindsight client closed.")
