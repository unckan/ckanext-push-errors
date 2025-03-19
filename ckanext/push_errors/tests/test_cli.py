import pytest
from ckanext.push_errors.cli.base import push_message_cli


@pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url.com")
@pytest.mark.ckan_config("ckan.site_url", "http://mock-site.com")
@pytest.mark.ckan_config("ckanext.push_errors.method", "POST")
@pytest.mark.ckan_config("ckanext.push_errors.headers", '{"Authorization": "Bearer {site_url}"}')
@pytest.mark.ckan_config("ckanext.push_errors.data", '{"error": "{message}"}')
def test_push_message_cli(cli):
    """
    Test the 'push-message' CLI command.
    Verify that the command executes correctly and displays the expected output.
    """
    result = cli.invoke(push_message_cli, ["--message", "Test message"])
    assert result.exit_code == 0
    assert "Pusshing message ..." in result.output
    assert "Message: Test message" in result.output
