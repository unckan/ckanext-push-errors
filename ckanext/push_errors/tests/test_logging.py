import requests
import logging
from datetime import datetime
from unittest.mock import patch, ANY
from ckanext.push_errors.logging import push_message, PushErrorHandler
import pytest

logging.basicConfig(level=logging.DEBUG)


class TestPushErrorLogging:

    @pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url.com")
    @pytest.mark.ckan_config("ckan.site_url", "http://mock-site.com")
    @pytest.mark.ckan_config("ckanext.push_errors.method", "POST")
    @pytest.mark.ckan_config("ckanext.push_errors.headers", '{"Authorization": "Bearer {site_url}"}')
    @pytest.mark.ckan_config("ckanext.push_errors.data", '{"error": "{message}"}')
    @patch("ckanext.push_errors.logging.requests.post")
    @patch("ckanext.push_errors.logging.datetime")
    @patch("ckanext.push_errors.logging.ckan_version", new="2.11.1")
    def test_push_message_with_valid_config(self, mock_datetime, mock_post):
        """Test sending messages with a valid configuration."""
        fixed_time = datetime(2025, 1, 23, 14, 6, 38)
        mock_datetime.now.return_value = fixed_time
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        default_title = (
            f'PUSH_ERROR *http://mock-site.com* \n'
            f'v0.1.4 - CKAN 2.11.1\n{fixed_time.isoformat()} user: -\n'
        )

        # Simulate a successful server response.
        mock_post.return_value.status_code = 200

        response = push_message("Test message")
        assert mock_post.called

        expected_message = default_title + "\nTest message"
        mock_post.assert_called_once_with(
            "http://mock-url.com",
            json={"error": expected_message},
            headers={"Authorization": "Bearer http://mock-site.com"}
        )
        assert response.status_code == 200

    @pytest.mark.ckan_config("ckanext.push_errors.url", "")
    @pytest.mark.ckan_config("ckan.site_url", "http://mock-site.com")
    def test_push_message_with_invalid_url(self):
        """Test behavior when no URL is configured."""
        with patch("ckanext.push_errors.logging.log") as mock_log:
            response = push_message("Test message")
            mock_log.warning.assert_called_once_with(
                'push-errors: No URL configured, logging message locally.'
            )
            assert response is None

    @pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url.com")
    @pytest.mark.ckan_config("ckan.site_url", "http://mock-site.com")
    @pytest.mark.ckan_config("ckanext.push_errors.method", "INVALID_METHOD")
    def test_push_message_with_invalid_method(self):
        """Test handling of an invalid HTTP method."""
        with patch("ckanext.push_errors.logging.log") as mock_log:
            response = push_message("Test message")
            mock_log.error.assert_called_once_with('push-errors: Invalid method')
            assert response is None

    @pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url.com")
    @pytest.mark.ckan_config("ckan.site_url", "http://mock-site.com")
    @pytest.mark.ckan_config("ckanext.push_errors.method", "POST")
    @pytest.mark.ckan_config("ckanext.push_errors.headers", '{"Authorization": "Bearer {site_url}"}')
    @pytest.mark.ckan_config("ckanext.push_errors.data", '{"error": "{message}"}')
    def test_push_message_with_network_error(self):
        """Test handling of network errors."""
        with patch("ckanext.push_errors.logging.requests.post") as mock_post, \
             patch("ckanext.push_errors.logging.log") as mock_log:
            # Simulate a network exception.
            mock_post.side_effect = requests.RequestException("Network error")
            response = push_message("Test message")
            mock_log.error.assert_called_once_with(
                'push-errors: Failed to send message to http://mock-url.com. Exception: Network error'
            )
            assert response is None

    def test_critical_error_logging(self):
        """Test that CRITICAL level logs are sent correctly."""
        with patch("ckanext.push_errors.logging.push_message") as mock_push_message:
            log = logging.getLogger("ckan")
            # Clear existing handlers to prevent multiple calls.
            log.handlers = []
            push_error_handler = PushErrorHandler()
            log.addHandler(push_error_handler)
            log.critical("This is a critical error!")
            mock_push_message.assert_called_once_with(ANY)

    @pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url.com")
    @pytest.mark.ckan_config("ckan.site_url", "http://mock-site.com")
    @pytest.mark.ckan_config("ckanext.push_errors.method", "INVALID_METHOD")
    def test_push_message_invalid_http_method(self):
        """Test that an invalid HTTP method logs an error and does not send a request."""
        with patch("ckanext.push_errors.logging.log") as mock_log:
            response = push_message("Test message")
            mock_log.error.assert_called_once_with('push-errors: Invalid method')
            assert response is None
