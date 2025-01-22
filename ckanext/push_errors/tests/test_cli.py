import pytest
from click.testing import CliRunner
from ckanext.push_errors.cli.base import push_message_cli


@pytest.mark.parametrize("message", ["Test message", "Another message"])
def test_push_message_cli(message):
    """
    Test el comando CLI 'push-message'.
    Verifique que el comando se ejecute correctamente y muestre el mensaje esperado.
    """
    # Inicializar el ejecutor de pruebas para los comandos Click
    runner = CliRunner()
    # Ejecutar el comando 'push-message' con el mensaje de prueba
    result = runner.invoke(push_message_cli, ["--message", message])

    # Verificar que el comando se ejecute correctamente y muestre el mensaje esperado
    assert result.exit_code == 0
    assert "Pusshing message ..." in result.output
    assert f"Message: {message}" in result.output
