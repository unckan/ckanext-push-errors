import pytest
from unittest.mock import patch, ANY, MagicMock
from werkzeug.exceptions import InternalServerError, Unauthorized, Forbidden, NotFound
from ckanext.push_errors.plugin import PushErrorsPlugin


@patch("ckanext.push_errors.plugin.push_message")
def test_error_handler(mock_push_message, app):
    """Test that the error handler processes exceptions correctly."""
    # Crear un mock para la app con el método register_error_handler
    mock_app = MagicMock()
    mock_app.register_error_handler = MagicMock()

    # Instanciar el plugin directamente
    plugin = PushErrorsPlugin()
    plugin.make_middleware(mock_app, {})

    # Obtener el error_handler registrado desde el mock
    error_handler = mock_app.register_error_handler.call_args[0][1]

    # Simular la excepción
    try:
        error_handler(InternalServerError("Test exception"))
    except InternalServerError:
        pass

    # Verificar que push_message fue llamado correctamente
    mock_push_message.assert_called_once()
    assert "Test exception" in mock_push_message.call_args[0][0]


@pytest.mark.parametrize("exception", [
    Unauthorized("Unauthorized access"),
    Forbidden("Forbidden access"),
    NotFound("Page not found"),
    InternalServerError("Internal error"),
])
@patch("ckanext.push_errors.plugin.push_message")
def test_middleware_handles_multiple_exceptions(mock_push_message, exception):
    """Test that the middleware handles different exceptions correctly."""
    mock_app = MagicMock()
    mock_app.register_error_handler = MagicMock()

    # Instanciar el plugin
    plugin = PushErrorsPlugin()
    plugin.make_middleware(mock_app, {})
    error_handler = mock_app.register_error_handler.call_args[0][1]

    try:
        error_handler(exception)
    except type(exception):
        pass

    # For HTTP errors 401, 403, 404 (or their corresponding exceptions), push_message should not be called.
    if isinstance(exception, (Unauthorized, Forbidden, NotFound)):
        mock_push_message.assert_not_called()
    else:
        mock_push_message.assert_called_once_with(ANY)


@pytest.mark.ckan_config("ckanext.push_errors.traceback_length", "1000")
@patch("ckanext.push_errors.plugin.push_message")
def test_traceback_length_respected_flat_config(mock_push_message):
    """ Ensure the traceback is limited by the config value (flat .get usage). """

    mock_app = MagicMock()
    mock_app.register_error_handler = MagicMock()

    plugin = PushErrorsPlugin()
    plugin.make_middleware(mock_app, {})
    error_handler = mock_app.register_error_handler.call_args[0][1]

    try:
        error_handler(InternalServerError("Test exception" + "*" * 2000))
    except InternalServerError:
        pass

    mock_push_message.assert_called_once()
    called_msg = mock_push_message.call_args[0][0]
    trace_section = called_msg.split("```")[1]  # TRACE\n```{...}```
    assert len(trace_section) <= 1000, f"Traceback length exceeds limit: {len(trace_section)}"


@pytest.mark.ckan_config("ckanext.push_errors.traceback_length", "100")
@patch("ckanext.push_errors.plugin.push_message")
def test_traceback_length_respected_with_nested_exception(mock_push_message):
    """ Ensure traceback length is respected in nested exception scenarios."""

    mock_app = MagicMock()
    mock_app.register_error_handler = MagicMock()

    plugin = PushErrorsPlugin()
    plugin.make_middleware(mock_app, {})
    error_handler = mock_app.register_error_handler.call_args[0][1]

    def raise_nested_exception():
        try:
            raise ValueError("Inner error" + "*" * 1000)
        except ValueError:
            raise InternalServerError("Outer exception" + "*" * 1000)

    try:
        raise_nested_exception()
    except InternalServerError as e:
        try:
            error_handler(e)
        except InternalServerError:
            pass

    mock_push_message.assert_called_once()
    called_msg = mock_push_message.call_args[0][0]
    trace_section = called_msg.split("```")[1]
    assert len(trace_section) <= 100, f"Traceback length exceeds 100: {len(trace_section)}"
