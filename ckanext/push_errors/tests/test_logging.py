
from unittest.mock import patch
from ckanext.push_errors.logging import push_message


def test_push_message_with_valid_config(mock_config):
    """Prueba el envío de mensajes con una configuración válida."""
    with patch("ckanext.push_errors.logging.requests.post") as mock_post:

        # Simular una respuesta exitosa del servidor
        mock_post.return_value.status_code = 200

        # Enviar un mensaje de prueba
        response = push_message("Test message")

        # Verificar que el mensaje fue enviado correctamente
        assert mock_post.called
        # Verificar que la respuesta fue exitosa
        assert response.status_code == 200


def test_push_message_with_invalid_config():
    """Prueba el manejo de configuraciones inválidas."""
    with patch("ckanext.push_errors.logging.toolkit.config.get", side_effect=lambda key, default=None: None):

        # Enviar un mensaje de prueba con una configuración inválida
        response = push_message("Test message")

        # Verificar que el mensaje no fue enviado
        assert response is None
