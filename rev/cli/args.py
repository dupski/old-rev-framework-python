
import argparse
import sys

from rev.app.log import LOG_LEVELS

class BaseArgParser(argparse.ArgumentParser):
    
    def __init__(self, **kwargs):

        from rev import PKG_NAME, PKG_VERSION
        
        super().__init__(
                description='{} v{}'.format(PKG_NAME, PKG_VERSION),
                add_help=True,
                formatter_class=argparse.RawTextHelpFormatter,
                **kwargs)

        self.add_argument('--log-level',
                          type=str,
                          nargs='?',
                          default='INFO',
                          help='Sets the logging level. Valid options are: ' + str(', '.join(LOG_LEVELS.keys())))
        
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

class RootArgParser(BaseArgParser):
    
    def __init__(self, app, **kwargs):

        from . import CLI_COMMANDS
        
        class CommandValidator(argparse.Action):
            def __call__(self, parser, namespace, value, option_string=None):
                if value != 'help' and value not in CLI_COMMANDS:
                    raise argparse.ArgumentError(self, "Invalid command. See help.")
                setattr(namespace, self.dest, value)
        
        super().__init__(
                usage='%(prog)s COMMAND [options]',
                epilog="Type '%(prog)s help COMMAND' for further info about each command\n",
                **kwargs)
    
        cmd_list = ''
        for cmd, cmd_props in CLI_COMMANDS.items():
            cmd_list += '  {} - {}\n'.format(cmd, cmd_props['description'])
    
        self.add_argument('COMMAND',
                          type=str,
                          action=CommandValidator,
                          help='Specify the command to run. Can be one of:\n\n' + cmd_list)

        self.add_argument('help_command_name', nargs='?', help=argparse.SUPPRESS)

class BaseCommand():
    def run(self, app, args, **kwargs):
        raise Exception('run() must be implemented for command')
        