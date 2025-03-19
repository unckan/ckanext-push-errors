import pytest
from unittest.mock import patch, MagicMock
from ckanext.push_errors.logging import push_message


@pytest.mark.ckan_config('ckanext.push_errors.url', 'https://fake-url.org')
@pytest.mark.ckan_config('ckan.site_url', 'https://mysite.org')
@pytest.mark.ckan_config('ckanext.push_errors.method', 'POST')
@pytest.mark.ckan_config('ckanext.push_errors.headers', '{}')
@pytest.mark.ckan_config('ckanext.push_errors.data', '{}')
@pytest.mark.ckan_config('ckanext.push_errors.message_title', 'Test Message {site_url} - {now}')
@patch('ckanext.push_errors.logging.requests.post')
def test_push_message_success(mock_post):
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
    assert 'Message received' in response.text


@pytest.mark.ckan_config('ckanext.push_errors.url', None)  # No se define URL
@patch('ckanext.push_errors.logging.requests.post')
def test_push_message_no_url(mock_post):
    response = push_message("Mensaje sin URL")

    # Verificar que no se hizo ninguna solicitud
    mock_post.assert_not_called()
    assert response is None
