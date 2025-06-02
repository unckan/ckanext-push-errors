"""
Tests for the log_error function in error_logger.py.
Validates deduplication and optional notification suppression behavior.
"""

import logging
import pytest
from ckanext.push_errors.error_logger import log_error, logged_errors, disabled_notifications


class DummyError(Exception):
    """Custom test exception used to simulate error logging scenarios."""
    pass


def raise_dummy_error():
    """
    Raises a controlled test exception to validate the behavior of log_error.
    """
    raise DummyError("Dummy error")


@pytest.fixture(autouse=True)
def clear_tracking_sets():
    """Clear global tracking sets before each test"""
    logged_errors.clear()
    disabled_notifications.clear()


def test_log_error_once(caplog):
    """Should log the error once and avoid duplication"""
    with caplog.at_level(logging.CRITICAL):
        try:
            raise_dummy_error()
        except DummyError as e:
            log_error(e)
            log_error(e)  # second call should be ignored

    assert len(caplog.records) == 1
    assert "Dummy error" in caplog.text


def test_log_error_silenced(caplog):
    """Should not log if disable_notification=True"""
    with caplog.at_level(logging.CRITICAL):
        try:
            raise_dummy_error()
        except DummyError as e:
            log_error(e, disable_notification=True)

    assert len(caplog.records) == 1
    assert "Dummy error" in caplog.text

    # Retry: it should be silenced now
    with caplog.at_level(logging.CRITICAL):
        try:
            raise_dummy_error()
        except DummyError as e:
            log_error(e)

    assert len(caplog.records) == 1  # No new logs
