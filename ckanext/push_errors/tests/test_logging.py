import requests
from datetime import datetime
from unittest.mock import patch
from ckanext.push_errors.logging import push_message


def test_push_message_with_valid_config(mock_config):
    """Prueba el envío de mensajes con una configuración válida."""
    # Mockear datetime.now para que sea consistente
    fixed_time = datetime(2025, 1, 23, 14, 6, 38)
    with patch("ckanext.push_errors.logging.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        default_title = (
            f'PUSH_ERROR *http://mock-site.com* \n'
            f'v0.1.4 - CKAN 2.11.1\n{fixed_time.isoformat()} user: -\n'
        )

        with patch("ckanext.push_errors.logging.requests.post") as mock_post:
            # Simular una respuesta exitosa del servidor
            mock_post.return_value.status_code = 200

            # Enviar un mensaje de prueba
            response = push_message("Test message")

            # Verificar que el mensaje fue enviado correctamente
            assert mock_post.called

            # Validar que el contenido del mensaje incluye el default_title con el salto de línea adicional
            expected_message = default_title + "\nTest message"
            mock_post.assert_called_once_with(
                "http://mock-url.com",
                json={"error": expected_message},
                headers={"Authorization": "Bearer http://mock-site.com"}
            )
            assert response.status_code == 200


def test_push_message_with_invalid_url(mock_config):
    """Prueba cuando no se configura una URL."""
    mock_config.get.side_effect = lambda key, default=None: (
        None if key == 'ckanext.push_errors.url' else default
    )

    with patch("ckanext.push_errors.logging.log") as mock_log:
        # Enviar un mensaje de prueba
        response = push_message("Test message")

        # Verificar que se registró un mensaje de advertencia
        mock_log.warning.assert_called_once_with(
            'push-errors: No URL configured, logging message locally.'
        )
        assert response is None


def test_push_message_with_invalid_method(mock_config):
    """Prueba el manejo de métodos no válidos."""
    # Mockear configuración con un método inválido pero con URL configurada
    mock_config.get.side_effect = lambda key, default=None: (
        'INVALID_METHOD' if key == 'ckanext.push_errors.method' else
        'http://mock-url.com' if key == 'ckanext.push_errors.url' else
        default
    )

    with patch("ckanext.push_errors.logging.log") as mock_log:
        # Enviar un mensaje de prueba
        response = push_message("Test message")

        # Verificar que se registró un mensaje de error específico
        mock_log.error.assert_called_once_with('push-errors: Invalid method')
        assert response is None


def test_push_message_with_network_error(mock_config):
    """Prueba el manejo de errores de red."""
    with patch("ckanext.push_errors.logging.requests.post") as mock_post, \
         patch("ckanext.push_errors.logging.log") as mock_log:

        # Simular una excepción de red
        mock_post.side_effect = requests.RequestException("Network error")

        # Enviar un mensaje de prueba
        response = push_message("Test message")

        # Verificar que se registró un mensaje de error
        mock_log.error.assert_called_once_with(
            'push-errors: Failed to send message to http://mock-url.com. Exception: Network error'
        )
        assert response is None
