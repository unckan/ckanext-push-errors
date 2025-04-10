import pytest
from ckanext.push_errors.cli.base import push_message_cli


@pytest.fixture
def test_push_message_cli(cli):
    """
    Test the 'push-message' CLI command.
    Verify that the command executes correctly and displays the expected output.
    """
    result = cli.invoke(push_message_cli, ["--message", "Test message"])
    assert result.exit_code == 0
    assert "Pusshing message ..." in result.output
    assert "Message: Test message" in result.output
