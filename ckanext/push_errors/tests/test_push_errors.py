from unittest import mock
import uuid
from ckan.lib.helpers import url_for
from ckan.tests import factories
from ckanext.push_errors.blueprints import push_errors


class TestPushErrorView:
    """Tests for the push_errors blueprint"""

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_unauthorized_no_user(self, mock_log, app):
        """
        Test that a 403 response is returned when no user is logged in
        """
        with app.flask_app.app_context():
            with mock.patch.object(push_errors.toolkit, '_', lambda x: x):
                client = app.test_client()
                response = client.get('/push-error/test')

        assert response.status_code == 403
        assert b'Unauthorized to access this page' in response.data
        mock_log.critical.assert_not_called()

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_unauthorized_not_sysadmin(self, mock_log, app):
        """
        Test that a 403 response is returned when the user is not a sysadmin
        """
        user_with_token = factories.UserWithToken()
        url = url_for('/push-error/test', msg='test')
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)

        assert response.status_code == 403
        assert b'Unauthorized to access this page' in response.data
        mock_log.critical.assert_not_called()

    @mock.patch('ckanext.push_errors.logging.push_message')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit.config.get')
    def test_sysadmin_default_message(self, mock_config_get, mock_push_message, app):
        """
        Test that a sysadmin can access the view and log the default message
        """
        # Mock configuration values
        mock_config_get.side_effect = lambda key, default=None: {
            'ckanext.push_errors.url': 'http://example.com',
        }.get(key, default)

        sysadmin_with_token = factories.UserWithToken()
        url = url_for('/push-error/test', msg='Push error test message')
        auth = {"Authorization": sysadmin_with_token['token']}
        response = app.get(url, headers=auth)

        mock_push_message.assert_called_once_with('Push error test message')
        assert b'Message logged: Push error test message' in response.data

    @mock.patch('ckanext.push_errors.logging.push_message')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit.config.get')
    def test_sysadmin_custom_message(self, mock_config_get, mock_push_message, app):
        """
        Test that a sysadmin can access the view and log a custom message
        """
        # Mock configuration values
        mock_config_get.side_effect = lambda key, default=None: {
            'ckanext.push_errors.url': 'http://example.com',
        }.get(key, default)

        text = 'Custom error message for testing'
        sysadmin_with_token = factories.UserWithToken()
        url = url_for('/push-error/test', msg=text.replace(" ", "+"))
        auth = {"Authorization": sysadmin_with_token['token']}
        response = app.get(url, headers=auth)

        mock_push_message.assert_called_once_with(text)
        assert b'Message logged: Custom error message for testing' in response.data

    @mock.patch('ckanext.push_errors.logging.push_message')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.toolkit.config.get')
    def test_integration_with_app_context(self, mock_config_get, mock_push_message, app):
        """
        Test the view function within an application context to ensure the blueprint routing works
        """
        # Mock configuration values
        mock_config_get.side_effect = lambda key, default=None: {
            'ckanext.push_errors.url': 'http://example.com',
        }.get(key, default)

        sysadmin_with_token = factories.UserWithToken()
        url = url_for('/push-error/test', msg='Integration Test')
        auth = {"Authorization": sysadmin_with_token['token']}
        response = app.get(url, headers=auth)

        mock_push_message.assert_called_once_with('Integration Test')
        assert b'Message logged: Integration Test' in response.data
