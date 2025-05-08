from unittest import mock
import pytest
from ckan.lib.helpers import url_for
from ckan.tests import factories


class TestPushErrorView:
    """Tests for the push_errors blueprint"""

    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_unauthorized_no_user(self, mock_log, app):
        """
        Test that a 403 response is returned when no user is logged in
        """
        url = url_for('/push-error/test', msg='test')
        response = app.get(url)

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

    @pytest.mark.ckan_config('ckanext.push_errors.url', 'http://example.com')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_sysadmin_default_message(self, mock_log, app):
        """
        Test that a sysadmin can access the view and log the default message
        """
        msg = 'Push error test message'
        sysadmin_with_token = factories.SysadminWithToken()
        url = url_for('push_errors.test_push_error', msg=msg)
        auth = {"Authorization": sysadmin_with_token['token']}
        response = app.get(url, headers=auth)

        mock_log.critical.assert_called_once_with(msg)
        assert f'Message logged: {msg}'.encode() in response.data

    @pytest.mark.ckan_config('ckanext.push_errors.url', 'http://example.com')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_sysadmin_custom_message(self, mock_log, app):
        """
        Test that a sysadmin can access the view and log a custom message
        """
        text = 'Custom error message for testing'
        sysadmin_with_token = factories.SysadminWithToken()
        url = url_for('push_errors.test_push_error', msg=text.replace(" ", "+"))
        auth = {"Authorization": sysadmin_with_token['token']}
        response = app.get(url, headers=auth)

        mock_log.critical.assert_called_once_with(text)
        assert f'Message logged: {text}'.encode() in response.data

    @pytest.mark.ckan_config('ckanext.push_errors.url', 'http://example.com')
    @mock.patch('ckanext.push_errors.blueprints.push_errors.log')
    def test_integration_with_app_context(self, mock_log, app):
        """
        Test the view function within an application context to ensure the blueprint routing works
        """
        msg = 'Integration Test'
        sysadmin_with_token = factories.SysadminWithToken()
        url = url_for('push_errors.test_push_error', msg=msg.replace(" ", "+"))
        auth = {"Authorization": sysadmin_with_token['token']}
        response = app.get(url, headers=auth)

        mock_log.critical.assert_called_once_with(msg)
        assert f'Message logged: {msg}'.encode() in response.data
