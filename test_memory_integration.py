"""
test_memory_integration.py

Tests whether the OnCall Memory layer can be
imported and safely called by the main agent.
"""

from memory import (
    save_incident,
    save_outcome,
    find_similar,
    learned_patterns,
    close_client
)


def expect_error(function, expected_error):
    """Check whether a function raises the expected error."""

    try:
        function()
    except expected_error:
        print(f"PASS: Expected {expected_error.__name__} raised.")
        return

    except Exception as error:
        raise AssertionError(
            f"Expected {expected_error.__name__}, "
            f"but got {type(error).__name__}: {error}"
        )

    raise AssertionError(
        f"Expected {expected_error.__name__}, but no error was raised."
    )


def run_tests():

    print("\n========== MEMORY INTEGRATION TEST ==========\n")

    # TEST 1: Check function imports
    functions = [
        save_incident,
        save_outcome,
        find_similar,
        learned_patterns
    ]

    assert all(callable(function) for function in functions)

    print("PASS: All four memory functions imported successfully.")

    # TEST 2: Validate save_incident
    expect_error(
    lambda: save_incident("invalid incident"),  # type: ignore
    TypeError
)

    expect_error(
        lambda: save_incident({}),
        ValueError
    )

    # TEST 3: Validate save_outcome
    expect_error(
        lambda: save_outcome("", "Resolution successful"),
        ValueError
    )

    expect_error(
        lambda: save_outcome("INC-TEST", ""),
        ValueError
    )

    # TEST 4: Validate find_similar
    expect_error(
        lambda: find_similar(""),
        ValueError
    )

    expect_error(
        lambda: find_similar("Database connection error", limit=0),
        ValueError
    )

    # TEST 5: Validate learned_patterns
    expect_error(
        lambda: learned_patterns(""),
        ValueError
    )

    print("\nAll integration checks passed!")

    print("\n========== TEST COMPLETED ==========")


if __name__ == "__main__":
    try:
        run_tests()

    finally:
        close_client()
        print("\nHindsight client closed.")