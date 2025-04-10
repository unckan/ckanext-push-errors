import pytest
from unittest import mock
from flask import Flask, g
from flask_babel import Babel
from ckanext.push_errors.blueprints import push_errors
from ckanext.push_errors.blueprints.push_errors import push_error_bp


@pytest.fixture
def app():
    """Create a Flask app with our blueprint registered"""
    app = Flask(__name__)
    app.secret_key = 'test-secret'
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    Babel(app)
    app.register_blueprint(push_error_bp)
    return app


class TestPushErrorView:
    """Tests for the push_errors blueprint"""

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_unauthorized_no_user(self, mock_log, app):
        """
        Test that a 403 response is returned when no user is logged in
        """
        with app.app_context():
            g.userobj = None
            with mock.patch.object(push_errors.toolkit, '_', lambda x: x):
                with app.test_client() as client:
                    response = client.get('/push-error/test')

        assert response.status_code == 403
        assert b'Unauthorized to access this page' in response.data
        mock_log.critical.assert_not_called()

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_unauthorized_not_sysadmin(self, mock_log, app):
        """
        Test that a 403 response is returned when the user is not a sysadmin
        """
        user_mock = mock.Mock()
        user_mock.sysadmin = False

        with app.app_context():
            g.userobj = user_mock
            with mock.patch.object(push_errors.toolkit, '_', lambda x: x):
                with app.test_client() as client:
                    response = client.get('/push-error/test')

        assert response.status_code == 403
        assert b'Unauthorized to access this page' in response.data
        mock_log.critical.assert_not_called()

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_sysadmin_default_message(self, mock_log, app):
        """
        Test que un sysadmin puede acceder a la vista y loguear el mensaje por defecto
        """
        user_mock = mock.Mock()
        user_mock.sysadmin = True

        with app.app_context():
            g.userobj = user_mock
            with mock.patch.object(push_errors.toolkit, '_', lambda x: x):
                with app.test_client() as client:
                    response = client.get('/push-error/test?msg=Push+error+test+message')

        mock_log.critical.assert_called_once_with('Push error test message')
        assert b'Message logged: Push error test message' in response.data

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_sysadmin_custom_message(self, mock_log, app):
        """
        Test that a sysadmin can access the page and provide a custom error message to be logged
        """
        text = 'Custom error message for testing'
        user_mock = mock.Mock()
        user_mock.sysadmin = True

        with app.app_context():
            g.userobj = user_mock
            with mock.patch.object(push_errors.toolkit, '_', lambda x: x):
                with app.test_client() as client:
                    response = client.get(f'/push-error/test?msg={text.replace(" ", "+")}')

        mock_log.critical.assert_called_once_with(text)
        assert b'Message logged: Custom error message for testing' in response.data

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_integration_with_app_context(self, mock_log, app):
        """
        Test the view function within an application context to ensure the blueprint routing works
        """
        user_mock = mock.Mock()
        user_mock.sysadmin = True

        with app.app_context():
            g.userobj = user_mock
            with mock.patch.object(push_errors.toolkit, '_', lambda x: x):
                with app.test_client() as client:
                    response = client.get('/push-error/test?msg=Integration+Test')

        mock_log.critical.assert_called_once_with('Integration Test')
        assert b'Message logged: Integration Test' in response.data
