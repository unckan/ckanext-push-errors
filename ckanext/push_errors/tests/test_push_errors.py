import pytest
from unittest import mock
from flask import Flask
from flask_babel import Babel
from ckan.lib.helpers import _

from ckanext.push_errors.blueprints.push_errors import push_error_bp, test_push_error


@pytest.fixture
def app():
    """Create a Flask app with our blueprint registered"""
    app = Flask(__name__)
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    Babel(app)  # Inicializa Babel
    app.register_blueprint(push_error_bp)
    return app


class TestPushErrorView(object):
    """Tests for the push_errors blueprint"""

    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit.abort')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_unauthorized_no_user(self, mock_log, mock_abort, app):
        """
        Test that a 403 response is returned when no user is logged in
        """
        mock_abort.side_effect = Exception("403 - Unauthorized")

        with app.test_client() as client, mock.patch.dict('ckanext.push_errors.blueprints.push_errors.toolkit.g', {'userobj': None}):
            with pytest.raises(Exception) as e:
                client.get('/push-error/test')

        mock_abort.assert_called_once_with(403, 'Unauthorized to access this page')
        mock_log.critical.assert_not_called()

    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit.abort')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_unauthorized_not_sysadmin(self, mock_log, mock_abort, app):
        """
        Test that a 403 response is returned when the user is not a sysadmin
        """
        mock_abort.side_effect = Exception("403 - Unauthorized")

        mock_user = mock.Mock()
        mock_user.sysadmin = False

        with app.test_client() as client, mock.patch.dict('ckanext.push_errors.blueprints.push_errors.toolkit.g', {'userobj': mock_user}):
            with pytest.raises(Exception) as e:
                client.get('/push-error/test')

        mock_abort.assert_called_once_with(403, 'Unauthorized to access this page')
        mock_log.critical.assert_not_called()

    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_sysadmin_default_message(self, mock_log, mock_toolkit, app):
        """
        Test que un sysadmin puede acceder a la vista y loguear el mensaje por defecto
        """
        mock_user = mock.Mock()
        mock_user.sysadmin = True

        with app.test_client() as client, mock.patch.dict('ckanext.push_errors.blueprints.push_errors.toolkit.g', {'userobj': mock_user}):
            response = client.get('/push-error/test')

        mock_log.critical.assert_called_once_with('Push error test message')
        assert b'Message logged: Push error test message' in response.data

    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_sysadmin_custom_message(self, mock_log, mock_toolkit, app):
        """
        Test that a sysadmin can access the page and provide a custom error message to be logged
        """
        mock_user = mock.Mock()
        mock_user.sysadmin = True

        custom_msg = "Custom error message for testing"

        with app.test_client() as client, mock.patch.dict('ckanext.push_errors.blueprints.push_errors.toolkit.g', {'userobj': mock_user}):
            response = client.get(f'/push-error/test?msg={custom_msg}')

        mock_log.critical.assert_called_once_with(custom_msg)
        assert f'Message logged: {custom_msg}'.encode() in response.data

    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_integration_with_app_context(self, mock_log, mock_toolkit, app):
        """
        Test the view function within an application context to ensure the blueprint routing works
        """
        mock_user = mock.Mock()
        mock_user.sysadmin = True

        with app.test_client() as client, mock.patch.dict('ckanext.push_errors.blueprints.push_errors.toolkit.g', {'userobj': mock_user}):
            response = client.get('/push-error/test?msg=Integration Test')

        mock_log.critical.assert_called_once_with('Integration Test')
        assert b'Message logged: Integration Test' in response.data
