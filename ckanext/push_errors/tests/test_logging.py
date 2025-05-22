import requests
import logging
import pytest
from datetime import datetime
from unittest.mock import patch, ANY
from ckanext.push_errors.logging import push_message, PushErrorHandler
from ckanext.push_errors import __VERSION__ as push_errors_version

logging.basicConfig(level=logging.DEBUG)


class TestPushErrorLogging:

    @pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url-99.com")
    @pytest.mark.ckan_config("ckanext.push_errors.headers", '{"Authorization": "Bearer {site_url}"}')
    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.ckan_version", new="2.11.1")
    @patch("ckanext.push_errors.logging.datetime")
    @patch("ckanext.push_errors.logging.requests.post")
    def test_push_message_with_valid_config(self, mock_post, mock_datetime, _can_send):
        fixed_time = datetime(2025, 1, 23, 14, 6, 38)
        mock_datetime.now.return_value = fixed_time
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        mock_post.return_value.status_code = 200

        pushed_msg = "Test message"
        expected_message_parts = [
            "PUSH_ERROR",
            "CKAN 2.11.1",
            pushed_msg,
            f"v{push_errors_version}",
        ]

        response = push_message(pushed_msg)
        # get all args for the post call
        args, kwargs = mock_post.call_args
        # check the URL (first param)
        assert args[0] == "http://mock-url-99.com"
        # check the json data
        msg = kwargs["json"]
        # check if all expected parts are in the message
        for part in expected_message_parts:
            assert part in msg["message"]
        # check the headers
        assert kwargs["headers"] == {"Authorization": "Bearer http://mock-site-99.com"}

        assert response.status_code == 200

    @pytest.mark.ckan_config("ckanext.push_errors.url", "")
    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.log")
    def test_push_message_with_invalid_url(self, mock_log, _):
        response = push_message("Test message")
        mock_log.warning.assert_called_once_with(
            'push-errors: No URL configured, logging message locally.'
        )
        assert response is None

    @pytest.mark.ckan_config("ckanext.push_errors.method", "INVALID_METHOD")
    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.log")
    def test_push_message_with_invalid_method(self, mock_log, _):
        response = push_message("Test message")
        mock_log.error.assert_called_once_with('push-errors: Invalid method')
        assert response is None

    @pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url.com")
    @patch("ckanext.push_errors.logging.can_send_message", return_value=True)
    @patch("ckanext.push_errors.logging.requests.post")
    @patch("ckanext.push_errors.logging.log")
    def test_push_message_with_network_error(self, mock_log, mock_post, _):
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
