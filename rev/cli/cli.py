
# Allows execution of a Rev Application from the command line

from .args import RootArgParser
import os, sys

def execute(app):
    
    # Execute command line options based on the specified app instance
    
    # Configure logging to console
    
    import logging
    from colorlog import ColoredFormatter
    
    console_log = logging.StreamHandler()
    console_log.setFormatter(ColoredFormatter(
        "%(asctime)s [%(log_color)s%(levelname)s%(reset)s] %(message)s",
    ))
    
    logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[#log.FileHandler("revserver.log"),
                console_log])
    
    # Handle command line arguments
    
    from . import CLI_COMMANDS
    
    argp = RootArgParser(app)
    args = argp.parse_known_args()[0]
    
    if args.COMMAND == 'help':
        if args.help_command_name in CLI_COMMANDS:
            cmd_spec = CLI_COMMANDS[args.help_command_name]
            cargp = cmd_spec['parser'](app)
            cargp.print_help()
        else:
            argp.print_help()
        sys.exit(2)
    
    else:
        cmd_spec = CLI_COMMANDS[args.COMMAND]
        cargp = cmd_spec['parser'](app)
        cargs = cargp.parse_args()
        
        cmd = cmd_spec['command']()
        cmd.run(app, cargs)
    