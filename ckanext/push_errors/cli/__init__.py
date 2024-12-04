import click
from ckanext.push_errors.cli.base import push_message_cli


@click.group("push-errors", short_help='Push-Errors plugin management commands')
def push_errors():
    pass


# Push-Errors commands
# ===========================================
push_errors.add_command(push_message_cli)
