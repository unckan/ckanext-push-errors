from unittest.mock import patch, MagicMock
from ckanext.push_errors.logging import push_message


@patch('ckanext.push_errors.logging.toolkit')
@patch('ckanext.push_errors.logging.requests.post')
def test_push_message_success(mock_post, mock_toolkit):
    # Configuración de mocks
    mock_toolkit.config.get.side_effect = lambda key, default=None: {
        'ckanext.push_errors.url': 'https://fake-url.org',
        'ckan.site_url': 'https://mysite.org',
        'ckanext.push_errors.method': 'POST',
        'ckanext.push_errors.headers': '{}',
        'ckanext.push_errors.data': '{}',
        'ckanext.push_errors.message_title': 'Test Message {site_url} - {now}'
    }.get(key, default)

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


@patch('ckanext.push_errors.logging.toolkit')
@patch('ckanext.push_errors.logging.requests.post')
def test_push_message_no_url(mock_post, mock_toolkit):
    # Configuración sin URL
    mock_toolkit.config.get.return_value = None

    response = push_message("Mensaje sin URL")

    # Verificar que no se hizo ninguna solicitud
    mock_post.assert_not_called()
    assert response is None
