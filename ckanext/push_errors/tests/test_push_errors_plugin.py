
import pytest
from unittest.mock import patch, ANY, MagicMock
from werkzeug.local import LocalProxy
from werkzeug.exceptions import InternalServerError, Unauthorized, Forbidden, NotFound


def test_make_middleware(mock_app, plugin):
    """Prueba que el middleware registre correctamente un handler de errores."""
    # Llamar al método make_middleware
    plugin.make_middleware(mock_app, {})
    # Verificar que el handler de errores fue registrado correctamente
    mock_app.register_error_handler.assert_called_once_with(Exception, ANY)


def test_error_handler(mock_app, plugin):
    """Prueba que el handler de errores maneje correctamente las excepciones."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message:
        # Llamar al método make_middleware para registrar el handler de errores

        plugin.make_middleware(mock_app, {})
        error_handler = mock_app.register_error_handler.call_args[0][1]

        # Simular el manejo de una excepción
        try:
            error_handler(InternalServerError("Test exception"))
        except InternalServerError:
            pass

        # Verificar que el mensaje fue enviado correctamente
        mock_push_message.assert_called_once()
        assert "Test exception" in mock_push_message.call_args[0][0]


@pytest.mark.parametrize(
    "exception_type,status_code,expected_call",
    [
        (Unauthorized, None, False),  # Tipo específico
        (Forbidden, None, False),    # Tipo específico
        (NotFound, None, False),     # Tipo específico
        (Exception, 401, False),     # Código HTTP específico
        (Exception, 403, False),     # Código HTTP específico
        (Exception, 404, False),     # Código HTTP específico
        (Exception, 500, True),      # Otro código HTTP no ignorado
    ],
)
def test_ignore_errors_for_anonymous(mock_app, plugin, exception_type, status_code, expected_call):
    """Prueba que ciertos errores sean ignorados para usuarios anónimos."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message, \
         patch("ckanext.push_errors.plugin.current_user", new=None):

        # Llamar al método make_middleware para registrar el handler de errores
        plugin.make_middleware(mock_app, {})
        error_handler = mock_app.register_error_handler.call_args[0][1]

        # Crear la excepción a manejar
        exception = exception_type("Test exception")
        if status_code:
            exception.code = status_code  # Configurar el código de estado

        # Manejar la excepción
        try:
            error_handler(exception)
        except exception_type:
            pass

        # Verificar si se esperaba que el mensaje fuera enviado
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
    """Prueba que el middleware maneje diferentes excepciones correctamente."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message:
        plugin.make_middleware(mock_app, {})
        error_handler = mock_app.register_error_handler.call_args[0][1]

        try:
            error_handler(exception)
        except type(exception):
            pass

        # Si la excepción es 401, 403 o 404 y no hay usuario, no debería llamar push_message
        if isinstance(exception, (Unauthorized, Forbidden, NotFound)):
            mock_push_message.assert_not_called()
        else:
            mock_push_message.assert_called_once_with(ANY)


def test_error_message_format(mock_app, plugin):
    """Prueba que el mensaje de error generado tiene el formato esperado."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message:

        # Crear un mock de request simulando un LocalProxy
        mock_request = MagicMock()
        mock_request.args = {"param1": "value1"}
        mock_request.path = "/some/path"

        # Mockear el LocalProxy para que devuelva nuestro mock_request
        with patch("ckan.common.request", new=LocalProxy(lambda: mock_request)):
            plugin.make_middleware(mock_app, {})
            error_handler = mock_app.register_error_handler.call_args[0][1]

            try:
                error_handler(InternalServerError("Critical failure"))
            except InternalServerError:
                pass

            # Obtener el mensaje real enviado
            actual_message = mock_push_message.call_args[0][0]

            # Verificar que partes clave del mensaje están contenidas
            assert "INTERNAL_ERROR" in actual_message
            assert "Critical failure" in actual_message
            assert "InternalServerError" in actual_message
            assert "TRACE" in actual_message
