import traceback
import hashlib
import logging


def get_error_trace_id(error: Exception) -> str:
    """
    Generates a unique identifier for an exception using the file path and line number.
    """
    tb = traceback.extract_tb(error.__traceback__)
    if tb:
        file_path, line_number, _, _ = tb[-1]
        return f"{file_path}:{line_number}"
    return "unknown"


def get_error_log_id(record: logging.LogRecord) -> str:
    """
    Generates a unique identifier for a log record. Uses traceback info if present,
    otherwise hashes the message to produce a shorter ID.
    """
    if record.exc_info:
        tb = traceback.extract_tb(record.exc_info[2])
        if tb:
            file_path, line_number, _, _ = tb[-1]
            return f"{file_path}:{line_number}"
    # Fallback to hash of the log message
    message = record.getMessage()
    msg_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
    return f"loghash:{msg_hash[:12]}"
