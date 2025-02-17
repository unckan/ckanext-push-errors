import pytest
from unittest.mock import MagicMock
from ckanext.push_errors.plugin import PushErrorsPlugin


@pytest.fixture
def mock_app():
    """Simulate an application for testing."""
    app = MagicMock()
    app.register_error_handler = MagicMock()
    app.logger = MagicMock()
    return app


@pytest.fixture
def plugin():
    """Create an instance of the PushErrorsPlugin."""
    return PushErrorsPlugin()
