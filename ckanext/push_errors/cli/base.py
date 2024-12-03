import click
from ckanext.push_errors.logging import push_message


@click.command('push-message', short_help='Push message')
@click.option('-m,', '--message', help='Message to be pushed')
def send_reports(message):
    """ Push a message """

    click.secho('Pusshing message ...', fg='green')
    click.secho(f'Message: {message}', fg='yellow', bold=True, bg='black')
    try:
        response = push_message(message)
    except Exception as e:
        click.secho(f'Error pushing message: {e}', fg='red')
    if response is None:
        click.secho('No response', fg='red')
    else:
        click.secho('Message sent', fg='green')
