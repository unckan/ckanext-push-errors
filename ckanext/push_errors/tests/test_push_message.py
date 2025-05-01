from unittest.mock import patch, MagicMock
import pytest
from ckanext.push_errors.logging import push_message


@patch('ckanext.push_errors.logging.requests.post')
@patch('ckanext.push_errors.logging.can_send_message', return_value=True)
@pytest.mark.ckan_config('ckanext.push_errors.url', 'http://example.com')
def test_push_message_success(mock_limit, mock_post):
    # Simular respuesta exitosa
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = 'Message received'
    mock_post.return_value = mock_response

    # Ejecutar la función
    response = push_message("Este es un mensaje de prueba")

    # Verificar que la llamada se hizo correctamente
    mock_post.assert_called_once()
    assert response.status_code == 200


@pytest.mark.ckan_config("ckanext.push_errors.url", "")
@patch('ckanext.push_errors.logging.requests.post')
def test_push_message_no_url(mock_post):
    # Configuración sin URL

    response = push_message("Missing URL")

    # Verificar que no se hizo ninguna solicitud
    mock_post.assert_not_called()
    assert response is None
