import pytest
from unittest.mock import MagicMock, patch
from ckanext.push_errors.plugin import PushErrorsPlugin


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
