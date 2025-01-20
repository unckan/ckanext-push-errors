import pytest
from unittest.mock import MagicMock, patch
from ckanext.push_errors.plugin import PushErrorsPlugin
from werkzeug.exceptions import InternalServerError


@pytest.fixture
def mock_app():
    """Simula una aplicación para pruebas."""
    app = MagicMock()
    app.register_error_handler = MagicMock()
    app.logger = MagicMock()
    return app


@pytest.fixture
def mock_config():
    """Mockea la configuración de CKAN."""
    with patch('ckan.plugins.toolkit.config') as config:
        config.get.side_effect = lambda key, default=None: {
            'ckanext.push_errors.url': 'http://mock-url.com',
            'ckanext.push_errors.method': 'POST',
            'ckanext.push_errors.headers': '{"Authorization": "Bearer {site_url}"}',
            'ckanext.push_errors.data': '{"error": "{message}"}',
        }.get(key, default)
        yield config


@pytest.fixture
def plugin():
    """Crea una instancia del plugin."""
    return PushErrorsPlugin()


def test_make_middleware(mock_app, mock_config, plugin):
    """Prueba la creación del middleware."""
    plugin.make_middleware(mock_app, {})

    # Verifica que el registro de error se haya llamado al menos una vez
    mock_app.register_error_handler.assert_called()
    args, _ = mock_app.register_error_handler.call_args
    assert args[0] == Exception  # Verifica que se registre para todas las excepciones


def test_error_handler(mock_app, mock_config, plugin):
    """Prueba el manejo de errores sin Flask."""
    # Simula el entorno de CKAN
    with patch('ckanext.push_errors.plugin.current_user', new=MagicMock()) as mock_user, \
         patch('ckanext.push_errors.plugin.push_message') as mock_push_message, \
         patch('ckan.plugins.toolkit.request', new=MagicMock()) as mock_request:
        # Configura current_user simulado
        mock_user.name = 'test_user'

        # Configura la solicitud simulada
        mock_request.path = '/test-path'
        mock_request.args = {'param1': 'value1'}

        # Registra el middleware
        plugin.make_middleware(mock_app, {})
        error_handler = mock_app.register_error_handler.call_args[0][1]

        # Simula una excepción
        try:
            error_handler(InternalServerError("Test exception"))
        except InternalServerError:
            pass

        # Verifica que se haya enviado el mensaje de error
        mock_push_message.assert_called_once()
        error_message = mock_push_message.call_args[0][0]
        assert "Test exception" in error_message
        assert "/test-path" in error_message
        assert "test_user" in error_message


def test_push_message(mock_config):
    """Prueba el envío de mensajes sin requests-mock."""
    from ckanext.push_errors.plugin import push_message

    # Mockea la función req
    with patch('ckanext.push_errors.logging.req') as mock_req:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Success'
        mock_req.return_value = mock_response

        push_message("Test error message")

        # Verifica que se llamó a req con los parámetros correctos
        mock_req.assert_called_once()
        assert mock_req.call_args[0][0] == 'http://mock-url.com'  # URL
        assert mock_req.call_args[0][1] == 'POST'  # Método


def test_error_message_is_generated(mock_app, mock_config, plugin):
    """Prueba que el error_message se genera correctamente."""
    # Simula el entorno de CKAN
    with patch('ckanext.push_errors.plugin.current_user', new=MagicMock()) as mock_user, \
         patch('ckanext.push_errors.plugin.push_message') as mock_push_message, \
         patch('ckan.plugins.toolkit.request', new=MagicMock()) as mock_request:
        # Configura current_user simulado
        mock_user.name = 'test_user'

        # Configura la solicitud simulada
        mock_request.path = '/test-path'
        mock_request.args = {'param1': 'value1'}

        # Registra el middleware
        plugin.make_middleware(mock_app, {})
        error_handler = mock_app.register_error_handler.call_args[0][1]

        # Simula una excepción
        exception = InternalServerError("Test exception")
        try:
            error_handler(exception)
        except InternalServerError:
            pass

        # Verifica que push_message fue llamado con el error_message correcto
        mock_push_message.assert_called_once()
        error_message = mock_push_message.call_args[0][0]

        # Verifica el contenido de error_message
        assert "INTERNAL_ERROR `500 Internal Server Error: Test exception [(InternalServerError)]`" in error_message
        assert "TRACE\n```NoneType: None\n```" in error_message  # Cambia según el contenido esperado del stacktrace
        assert "on page /test-path" in error_message
        assert "by user *test_user*" in error_message
        assert "QUERY_PARAMS: {'param1': 'value1'}" in error_message
