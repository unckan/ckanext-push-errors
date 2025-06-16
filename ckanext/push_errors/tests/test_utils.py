import logging
from ckanext.push_errors.utils import get_error_trace_id, get_error_log_id


class CustomError(Exception):
    pass


def raise_custom_error_and_log():
    try:
        raise CustomError("Simulated catched error")
    except Exception as e:
        logging.getLogger("testlogger").critical(f"Some critical error {e}", exc_info=True)


class ListHandler(logging.Handler):
    """Custom handler to store log records in a list."""
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def raise_custom_error():
    """Raises a CustomError to simulate an error scenario for testing purposes."""
    raise CustomError("Simulated error")


def test_get_error_trace_id_returns_path_and_line():
    """
    Test that get_error_trace_id returns a string containing the file path and line number
    where the CustomError was raised, formatted as 'path/to/file.py:<line>'.
    Ensures the returned trace_id contains a colon and does not end with '.py'.
    """
    try:
        raise_custom_error()
    except CustomError as e:
        trace_id = get_error_trace_id(e)
        assert ":" in trace_id, "Trace ID should contain a colon"
        path, line = trace_id.rsplit(":", 1)
        assert path.endswith("test_utils.py"), f"Expected path to end with test_utils.py, got {path}"
        assert line.isdigit(), f"Expected a line number, got {line}"


def test_get_error_trace_id_unknown_when_no_tb():
    """
    Test that get_error_trace_id returns 'unknown' when the exception has no traceback.

    This test creates a CustomError instance without a traceback and verifies that
    the get_error_trace_id function returns the string 'unknown' as expected.
    """
    e = CustomError("No traceback")
    trace_id = get_error_trace_id(e)
    assert trace_id == "unknown"


def test_get_error_log_id_from_exc_info():
    """
    Tests the get_error_log_id function to ensure it generates an appropriate log identifier
    from a logging record containing exception information.

    - Creates a test logger.
    - Raises and catches a custom exception.
    - Generates a log record with the captured exception.
    - Obtains the log identifier using get_error_log_id.
    - Verifies that the identifier does not start with "loghash:" and contains ":".

    This function checks that get_error_log_id correctly processes exception information
    in a logging record and generates the expected identifier.
    """
    logger = logging.getLogger("testlogger")
    logger.setLevel(logging.CRITICAL)
    handler = ListHandler()
    logger.addHandler(handler)

    # Ejecutar el log
    raise_custom_error_and_log()

    # Asegurar que se capturó un registro
    assert len(handler.records) > 0, "Expected at least one log record"

    log_record = handler.records[-1]
    log_id = get_error_log_id(log_record)
    assert not log_id.startswith("loghash:")
    assert ":" in log_id

    # Limpieza
    logger.removeHandler(handler)


def test_get_error_log_id_from_message_hash():
    """
    Test that get_error_log_id generates a unique log ID for a given LogRecord.

    This test creates a LogRecord with a critical error message and verifies that
    the generated log ID starts with the expected prefix ("loghash:") and has a
    length greater than 12 characters, ensuring the uniqueness and format of the
    log identifier.
    """
    record = logging.LogRecord(
        name="test", level=logging.CRITICAL, pathname="", lineno=0,
        msg="Some random critical error", args=(), exc_info=None
    )
    log_id = get_error_log_id(record)
    assert log_id.startswith("loghash:")
    assert len(log_id) > 12
