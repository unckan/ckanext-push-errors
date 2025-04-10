import pytest
from unittest.mock import patch, ANY, MagicMock
from werkzeug.exceptions import InternalServerError, Unauthorized, Forbidden, NotFound
from ckanext.push_errors.plugin import PushErrorsPlugin


class CustomHTTPException(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


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


@pytest.mark.parametrize(
    "exception,expected_call",
    [
        (Unauthorized("Test exception"), False),         # Specific HTTP exception.
        (Forbidden("Test exception"), False),            # Specific HTTP exception.
        (NotFound("Test exception"), False),             # Specific HTTP exception.
    ],
)
@patch("ckanext.push_errors.plugin.push_message")
def test_ignore_errors_for_anonymous(mock_push_message, exception, expected_call):
    """Test that certain errors are ignored for anonymous users."""
    # Crear un mock para la app con el método register_error_handler
    mock_app = MagicMock()
    mock_app.register_error_handler = MagicMock()

    # Instanciar el plugin directamente
    plugin = PushErrorsPlugin()
    plugin.make_middleware(mock_app, {})

    error_handler = mock_app.register_error_handler.call_args[0][1]

    try:
        error_handler(exception)
    except type(exception):
        pass

    if expected_call:
        mock_push_message.assert_called_once_with(ANY)
    else:
        mock_push_message.assert_not_called()


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
