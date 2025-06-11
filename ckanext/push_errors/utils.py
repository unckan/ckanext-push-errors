import traceback


def get_error_trace_id(error: Exception) -> str:
    """
    Extract a unique identifier for an exception, based on the last traceback entry.
    Returns a string in the format: 'file_path:line_number'
    If traceback is unavailable, returns 'unknown'.
    """
    tb = traceback.extract_tb(error.__traceback__)
    if tb:
        file_path, line_number, *_ = tb[-1]
        return f"{file_path}:{line_number}"
    return "unknown"
