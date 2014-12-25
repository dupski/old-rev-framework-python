from .cli import execute

CLI_COMMANDS = {}

def register_command(command, description, parser, command_class):
    global CLI_COMMANDS
    CLI_COMMANDS[command] = {
        'description' : description,
        'parser' : parser,
        'command' : command_class,
    }

from .runserver import RunServerArgParser, RunServerCommand
from .syncdb import SyncDBArgParser, SyncDBCommand

register_command('runserver', 'starts the rev framework test server', RunServerArgParser, RunServerCommand)
register_command('syncdb', 'synchronise database metadata', SyncDBArgParser, SyncDBCommand)