
import argparse
from .args import BaseArgParser, BaseCommand
import os

class RunServerArgParser(BaseArgParser):

    def __init__(self, app, **kwargs):
        
        class IPAddressValidator(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, values)
        
        class PortNumberValidator(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, values)
        
        super().__init__(
                usage='%(prog)s runserver [ip_address] [port] [options]',
                **kwargs)
        
        self.description += '\n\n  runserver - Runs a local test server for your Rev Framework application'
    
        self.add_argument('command', help=argparse.SUPPRESS)
        
        self.add_argument('ip_address',
                          type=str,
                          nargs='?',
                          action=IPAddressValidator,
                          default=app.config['DEBUG_SERVER_ADDRESS'],
                          help='Sets the IP Address to run the server on')
        
        self.add_argument('port',
                          type=int,
                          nargs='?',
                          action=PortNumberValidator,
                          default=app.config['DEBUG_SERVER_PORT'],
                          help='Sets the Port Number to run the server on')

        self.add_argument('--no-reload',
                          default=False,
                          action='store_true',
                          help='Turn off auto-reloading of the application when the code is changed')

        self.add_argument('--no-syncdb',
                          default=False,
                          action='store_true',
                          help='Disables automatic reloading of module data on application (re)load')

import logging

class RunServerCommand(BaseCommand):
    def run(self, app, args, **kwargs):

        reload = False if args.no_reload else True
        syncdb = False if args.no_syncdb else 'auto'
        
        # Avoid duplicate initialisation with Werkzeug reloader
        if not reload or os.environ.get("WERKZEUG_RUN_MAIN") == "true": 
            app.init(syncdb=syncdb)
        
        app.run(
            host=args.ip_address,
            port=args.port,
            use_reloader=reload,
            debug=True)