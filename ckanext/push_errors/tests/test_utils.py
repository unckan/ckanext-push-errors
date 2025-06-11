from ckanext.push_errors.utils import get_error_trace_id


class DummyException(Exception):
    pass


def raise_dummy():
    raise DummyException("Testing traceback")


def test_get_error_trace_id_returns_valid_id():
    try:
        raise_dummy()
    except DummyException as e:
        trace_id = get_error_trace_id(e)
        assert isinstance(trace_id, str)
        assert ":" in trace_id
        assert trace_id.endswith(".py") or trace_id.count(":") == 1


def test_get_error_trace_id_returns_unknown_on_missing_trace():
    dummy = DummyException("No traceback attached")
    trace_id = get_error_trace_id(dummy)
    assert trace_id == "unknown"
