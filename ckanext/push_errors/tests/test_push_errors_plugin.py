
import pytest
from unittest.mock import patch, ANY
from werkzeug.exceptions import InternalServerError, Unauthorized, Forbidden, NotFound, InternalServerError



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
