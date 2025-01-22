
import pytest
from unittest.mock import patch
from werkzeug.exceptions import InternalServerError


def test_make_middleware(mock_app, plugin):
    """Prueba que el middleware registre correctamente un handler de errores."""
    # Llamar al método make_middleware
    plugin.make_middleware(mock_app, {})
    # Verificar que el handler de errores fue registrado correctamente
    mock_app.register_error_handler.assert_called_once_with(Exception, pytest.anything())


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


@pytest.mark.parametrize("status_code,expected_call", [(401, False), (403, False), (404, False), (500, True)])
def test_ignore_errors_for_anonymous(mock_app, plugin, status_code, expected_call):
    """Prueba que ciertos errores sean ignorados para usuarios anónimos."""
    with patch("ckanext.push_errors.plugin.push_message") as mock_push_message, \
         patch("ckanext.push_errors.plugin.current_user", new=None):

        # Llamar al método make_middleware para registrar el handler de errores
        plugin.make_middleware(mock_app, {})
        error_handler = mock_app.register_error_handler.call_args[0][1]

        # Simular el manejo de una excepción con el código de estado especificado
        exception = InternalServerError("Test exception") if status_code == 500 else Exception()
        try:
            error_handler(exception)
        except Exception:
            pass

        # Verificar si se esperaba que el mensaje fuera enviado
        if expected_call:
            mock_push_message.assert_called_once()
        else:
            mock_push_message.assert_not_called()
