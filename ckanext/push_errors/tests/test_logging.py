import requests
import logging
from datetime import datetime
from unittest.mock import patch, ANY
from ckanext.push_errors.logging import push_message, PushErrorHandler
from ckanext.push_errors import __VERSION__ as push_errors_version

logging.basicConfig(level=logging.DEBUG)


class TestPushErrorLogging:

    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.ckan_version", new="2.11.1")
    @patch("ckanext.push_errors.logging.toolkit.config")
    @patch("ckanext.push_errors.logging.datetime")
    @patch("ckanext.push_errors.logging.requests.post")
    def test_push_message_with_valid_config(self, mock_post, mock_datetime, mock_config, _can_send):
        fixed_time = datetime(2025, 1, 23, 14, 6, 38)
        mock_datetime.now.return_value = fixed_time
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        mock_config.get.side_effect = lambda key, default=None: {
            "ckanext.push_errors.url": "http://mock-url.com",
            "ckanext.push_errors.method": "POST",
            "ckan.site_url": "http://mock-site.com",
            "ckanext.push_errors.headers": '{"Authorization": "Bearer {site_url}"}',
            "ckanext.push_errors.data": '{"error": "{message}"}'
        }.get(key, default)

        mock_post.return_value.status_code = 200

        default_title = (
            f'PUSH_ERROR *http://mock-site.com* \n'
            f'v{push_errors_version} - CKAN 2.11.1\n{fixed_time.isoformat()} user: -\n'
        )
        expected_message = default_title + "\nTest message"

        response = push_message("Test message")
        mock_post.assert_called_once_with(
            "http://mock-url.com",
            json={"error": expected_message},
            headers={"Authorization": "Bearer http://mock-site.com"}
        )
        assert response.status_code == 200

    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.toolkit.config")
    @patch("ckanext.push_errors.logging.log")
    def test_push_message_with_invalid_url(self, mock_log, mock_config, _):
        mock_config.get.return_value = ""
        response = push_message("Test message")
        mock_log.warning.assert_called_once_with(
            'push-errors: No URL configured, logging message locally.'
        )
        assert response is None

    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.toolkit.config")
    @patch("ckanext.push_errors.logging.log")
    def test_push_message_with_invalid_method(self, mock_log, mock_config, _):
        mock_config.get.side_effect = lambda key, default=None: {
            "ckanext.push_errors.url": "http://mock-url.com",
            "ckanext.push_errors.method": "INVALID_METHOD"
        }.get(key, default)
        response = push_message("Test message")
        mock_log.error.assert_called_once_with('push-errors: Invalid method')
        assert response is None

    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.requests.post")
    @patch("ckanext.push_errors.logging.toolkit.config")
    @patch("ckanext.push_errors.logging.log")
    def test_push_message_with_network_error(self, mock_log, mock_config, mock_post, _):
        mock_config.get.side_effect = lambda key, default=None: {
            "ckanext.push_errors.url": "http://mock-url.com",
            "ckanext.push_errors.method": "POST",
            "ckan.site_url": "http://mock-site.com",
            "ckanext.push_errors.headers": '{"Authorization": "Bearer {site_url}"}',
            "ckanext.push_errors.data": '{"error": "{message}"}'
        }.get(key, default)
        mock_post.side_effect = requests.RequestException("Network error")
        response = push_message("Test message")
        mock_log.error.assert_called_once_with(
            'push-errors: Failed to send message to http://mock-url.com. Exception: Network error'
        )
        assert response is None

    def test_critical_error_logging(self):
        with patch("ckanext.push_errors.logging.push_message") as mock_push_message:
            log = logging.getLogger("ckan")
            log.handlers = []
            push_error_handler = PushErrorHandler()
            log.addHandler(push_error_handler)
            log.critical("This is a critical error!")
            mock_push_message.assert_called_once_with(ANY)

    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.toolkit.config")
    @patch("ckanext.push_errors.logging.log")
    def test_push_message_invalid_http_method(self, mock_log, mock_config, _):
        mock_config.get.side_effect = lambda key, default=None: {
            "ckanext.push_errors.url": "http://mock-url.com",
            "ckan.site_url": "http://mock-site.com",
            "ckanext.push_errors.method": "INVALID_METHOD"
        }.get(key, default)
        response = push_message("Test message")
        mock_log.error.assert_called_once_with('push-errors: Invalid method')
        assert response is None
