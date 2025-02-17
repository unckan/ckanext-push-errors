import pytest
from unittest.mock import patch, ANY, MagicMock
from werkzeug.local import LocalProxy
from werkzeug.exceptions import InternalServerError, Unauthorized, Forbidden, NotFound


class CustomHTTPException(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


def test_make_middleware(mock_app, plugin):
    """Test that the middleware registers an error handler correctly."""
    plugin.make_middleware(mock_app, {})
    mock_app.register_error_handler.assert_called_once_with(Exception, ANY)


def test_error_handler(mock_app, plugin):
    """Test that the error handler processes exceptions correctly."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message:
        plugin.make_middleware(mock_app, {})
        error_handler = mock_app.register_error_handler.call_args[0][1]

        try:
            error_handler(InternalServerError("Test exception"))
        except InternalServerError:
            pass

        mock_push_message.assert_called_once()
        assert "Test exception" in mock_push_message.call_args[0][0]


@pytest.mark.parametrize(
    "exception,expected_call",
    [
        (Unauthorized("Test exception"), False),         # Specific HTTP exception.
        (Forbidden("Test exception"), False),            # Specific HTTP exception.
        (NotFound("Test exception"), False),             # Specific HTTP exception.
        (CustomHTTPException("Test exception", 401), False),  # Custom exception with HTTP code 401.
        (CustomHTTPException("Test exception", 403), False),  # Custom exception with HTTP code 403.
        (CustomHTTPException("Test exception", 404), False),  # Custom exception with HTTP code 404.
        (CustomHTTPException("Test exception", 500), True),   # Custom exception with HTTP code 500.
    ],
)
def test_ignore_errors_for_anonymous(mock_app, plugin, exception, expected_call):
    """Test that certain errors are ignored for anonymous users."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message, \
         patch("ckanext.push_errors.plugin.current_user", new=None):
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
def test_middleware_handles_multiple_exceptions(mock_app, plugin, exception):
    """Test that the middleware handles different exceptions correctly."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message:
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


def test_error_message_format(mock_app, plugin):
    """Test that the generated error message has the expected format."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message:
        # Create a mock request simulating a LocalProxy.
        mock_request = MagicMock()
        mock_request.args = {"param1": "value1"}
        mock_request.path = "/some/path"

        # Patch the LocalProxy to return our mock_request.
        with patch("ckan.common.request", new=LocalProxy(lambda: mock_request)):
            plugin.make_middleware(mock_app, {})
            error_handler = mock_app.register_error_handler.call_args[0][1]

            try:
                error_handler(InternalServerError("Critical failure"))
            except InternalServerError:
                pass

            # Retrieve the actual message sent.
            actual_message = mock_push_message.call_args[0][0]
            # Verify that key parts of the message are included.
            assert "INTERNAL_ERROR" in actual_message
            assert "Critical failure" in actual_message
            assert "InternalServerError" in actual_message
            assert "TRACE" in actual_message
